# Copyright (C) 2021 Humanitarian OpenStreetmap Team

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Humanitarian OpenStreetmap Team
# 1100 13th Street NW Suite 800 Washington, D.C. 20005
# <info@hotosm.org>

"""[Router Responsible for Raw data API ]
"""
import os
from datetime import datetime as dt
from uuid import uuid4
import time
import zipfile
import requests
# from .auth import login_required
import pathlib
import shutil
from starlette.background import BackgroundTasks
import orjson

from fastapi import APIRouter, Request
from fastapi_versioning import version
from fastapi.responses import JSONResponse
# from fastapi import APIRouter, Depends, Request
from src.galaxy.query_builder.builder import format_file_name_str
from src.galaxy.validation.models import RawDataCurrentParams, RawDataOutputType
from src.galaxy.app import RawData, S3FileTransfer
from .api_worker import process_raw_data
from src.galaxy.config import export_rate_limit, use_s3_to_upload, logger as logging, config, limiter, allow_bind_zip_filter

router = APIRouter(prefix="/raw-data")

# @router.post("/historical-snapshot/")
# def get_historical_data(params:RawDataHistoricalParams):
#     start_time = time.time()
#     result= RawData(params).extract_historical_data()
#     return generate_rawdata_response(result,start_time)


@router.post("/current-snapshot/")
@version(1)
def get_current_snapshot_osm_data(params: RawDataCurrentParams, background_tasks: BackgroundTasks, request: Request):
    """Generates the current raw OpenStreetMap data available on database based on the input geometry, query and spatial features

    Args:

        params (RawDataCurrentParams):
                {
                "outputType": "GeoJSON", # supported are : kml,shp,(FLATGEOBUF)fgb
                "fileName": "string",
                "geometry": { # only polygon is supported ** required field **
                    "coordinates": [
                    [
                        [
                        1,0
                        ],
                        [
                        2,0
                        ]
                    ]
                    ],
                    "type": "Polygon"
                },
                "filters" : {
                    "tags": { # tags filter controls no of rows returned
                    "point" : {"amenity":["shop"]},
                    "line" : {},
                    "polygon" : {"key":["value1","value2"],"key2":["value1"]},
                    "all_geometry" : {"building":['yes']} # master filter applied to all of the geometries selected on geometryType
                    },
                    "attributes": { # attribute column controls associated k-v pairs returned
                    "point": [], column
                    "line" : [],
                    "polygon" : [],
                    "all_geometry" : ["name","address"], # master field applied to all geometries selected on geometryType
                    }
                    },
                "geometryType": [
                    "point","line","polygon"
                ],
                joinFilterType:"OR" # options are and / or . 'or' by default -- applies condition for filters **optional
                }
        background_tasks (BackgroundTasks): task to cleanup the files produced during export
        request (Request): request instance

        Returns :
        {
            "download_url": Url for downloading the requested file in zip,
            "file_name": name_of_export + unique_id + outputformat,
            "response_time": time taken to generate the export,
            "query_area": area in sq km ,
            "binded_file_size": actual zipped file size in MB,
            "zip_file_size_bytes": [
                zip file size in bytes
            ]
        }
        Sample Query :
        1. Sample query to extract point and polygon features that are marked building=*  with name attribute
        {
            "outputType": "GeoJSON",
            "fileName": "Pokhara_buildings",
            "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                    [
                        [
                        83.96919250488281,
                        28.194446860487773
                        ],
                        [
                        83.99751663208006,
                        28.194446860487773
                        ],
                        [
                        83.99751663208006,
                        28.214869548073377
                        ],
                        [
                        83.96919250488281,
                        28.214869548073377
                        ],
                        [
                        83.96919250488281,
                        28.194446860487773
                        ]
                    ]
                    ]
                },
            "filters": {"tags":{"all_geometry":{"building":[]}},"attributes":{"all_geometry":["name"]}},
            "geometryType": [
                "point","polygon"
            ]
        }
        2. Query to extract all OpenStreetMap features in a polygon in shapefile format:
        {
            "outputType": "shp",
            "fileName": "Pokhara_all_features",
            "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                    [
                        [
                        83.96919250488281,
                        28.194446860487773
                        ],
                        [
                        83.99751663208006,
                        28.194446860487773
                        ],
                        [
                        83.99751663208006,
                        28.214869548073377
                        ],
                        [
                        83.96919250488281,
                        28.214869548073377
                        ],
                        [
                        83.96919250488281,
                        28.194446860487773
                        ]
                    ]
                    ]
                }
        }
        3. Clean query to extract all features by deafult; output will be same as 2nd query but in GeoJSON format and output name will be `default`
        {
            "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                    [
                        [
                        83.96919250488281,
                        28.194446860487773
                        ],
                        [
                        83.99751663208006,
                        28.194446860487773
                        ],
                        [
                        83.99751663208006,
                        28.214869548073377
                        ],
                        [
                        83.96919250488281,
                        28.214869548073377
                        ],
                        [
                        83.96919250488281,
                        28.194446860487773
                        ]
                    ]
                    ]
                }
        }

    """
# def get_current_data(params:RawDataCurrentParams,background_tasks: BackgroundTasks, user_data=Depends(login_required)): # this will use osm login makes it restrict login
    start_time = dt.now()
    bind_zip=params.bind_zip if allow_bind_zip_filter else True
    # unique id for zip file and geojson for each export
    params.file_name=format_file_name_str(params.file_name) if params.file_name else 'Export'
    exportname = f"{params.file_name}_{str(str(uuid4()))}_{params.output_type}"

    logging.info("Request %s received", exportname)

    geom_area, working_dir = RawData(params).extract_current_data(exportname)
    inside_file_size = 0
    if bind_zip:
        logging.debug('Zip Binding Started !')
        # saving file in temp directory instead of memory so that zipping file will not eat memory
        upload_file_path = os.path.join(working_dir,os.pardir,f"{exportname}.zip")

        zf = zipfile.ZipFile(upload_file_path, "w", zipfile.ZIP_DEFLATED)
        for file_path in pathlib.Path(working_dir).iterdir():
            zf.write(file_path, arcname=file_path.name)
            inside_file_size += os.path.getsize(file_path)

        # Compressing geojson file
        zf.writestr("clipping_boundary.geojson",
                    orjson.dumps(dict(params.geometry)))

        zf.close()
        logging.debug('Zip Binding Done !')
    else:
        for file_path in pathlib.Path(working_dir).iterdir():
            upload_file_path=file_path
            inside_file_size += os.path.getsize(file_path)
            break # only take one file inside dir , if contains many it should be inside zip
    # check if download url will be generated from s3 or not from config
    if use_s3_to_upload:
        file_transfer_obj = S3FileTransfer()
        download_url = file_transfer_obj.upload(upload_file_path, exportname, file_suffix='zip' if bind_zip else params.output_type.lower())
    else:
        download_url = str(upload_file_path) # give the static file download url back to user served from fastapi static export path

    # getting file size of zip , units are in bytes converted to mb in response
    zip_file_size = os.path.getsize(upload_file_path)
    # watches the status code of the link provided and deletes the file if it is 200
    if use_s3_to_upload:
        background_tasks.add_task(watch_s3_upload,download_url, upload_file_path)
    if use_s3_to_upload or bind_zip:
        #remove working dir from the machine , if its inside zip / uploaded we no longer need it
        background_tasks.add_task(remove_file,working_dir)
    response_time = dt.now() - start_time
    response_time_str = str(response_time)
    logging.info(f"Done Export : {exportname} of {round(inside_file_size/1000000)} MB / {geom_area} sqkm in {response_time_str}")

    return {"download_url": download_url, "file_name": exportname, "response_time": response_time_str, "query_area": f"""{geom_area} Sq Km """, "binded_file_size": f"""{round(inside_file_size/1000000,2)} MB""", "zip_file_size_bytes": {zip_file_size}}


@router.get("/status/")
@version(1)
def check_current_db_status():
    """Gives status about DB update, Substracts with current time and last db update time"""
    result = RawData().check_status()
    response = f"{result} ago"
    return {"last_updated": response}


def remove_file(path: str) -> None:
    """Used for removing temp file dir and its all content after zip file is delivered to user
    """
    try:
        shutil.rmtree(path)
    except OSError as ex:
        logging.error("Error: %s - %s.", ex.filename, ex.strerror)


def watch_s3_upload(url: str, path: str) -> None:
    """Watches upload of s3 either it is completed or not and removes the temp file after completion

    Args:
        url (_type_): url generated by the script where data will be available
        path (_type_): path where temp file is located at
    """
    start_time = time.time()
    remove_temp_file = True
    check_call = requests.head(url).status_code
    if check_call != 200:
        logging.debug("Upload is not done yet waiting ...")
        while check_call != 200:  # check until status is not green
            check_call = requests.head(url).status_code
            if time.time() - start_time > 300:
                logging.error(
                    "Upload time took more than 5 min , Killing watch : %s , URL : %s", path, url)
                remove_temp_file = False  # don't remove the file if upload fails
                break
            time.sleep(3)  # check each 3 second
    # once it is verfied file is uploaded finally remove the file
    if remove_temp_file:
        logging.debug(
            "File is uploaded at %s , flushing out from %s", url, path)
        os.unlink(path)


@router.post("/current-snapshot/")
@limiter.limit(f"{export_rate_limit}/minute")
@version(2)
def get_current_snapshot_of_osm_data(
    params: RawDataCurrentParams, request: Request):
    """Generates the current raw OpenStreetMap data available on database based on the input geometry, query and spatial features.

    Steps to Run Snapshot :

    1.  Post the your request here and your request will be on queue, endpoint will return as following :
        {
            "task_id": "your task_id",
            "track_link": "/tasks/task_id/"
        }
    2. Now navigate to /tasks/ with your task id to track progress and result

    Args:

        params (RawDataCurrentParams):
                {
                "outputType": "GeoJSON", # supports kml,(FLATGEOBUF)fgb,shp
                "fileName": "string",
                "geometry": { # only polygon is supported ** required field **
                    "coordinates": [
                    [
                        [
                        1,0
                        ],
                        [
                        2,0
                        ]
                    ]
                    ],
                    "type": "Polygon"
                },
                "filters" : {
                    "tags": { # tags filter controls no of rows returned
                    "point" : {"amenity":["shop"]},
                    "line" : {},
                    "polygon" : {"key":["value1","value2"],"key2":["value1"]},
                    "all_geometry" : {"building":['yes']} # master filter applied to all of the geometries selected on geometryType
                    },
                    "attributes": { # attribute column controls associated k-v pairs returned
                    "point": [], column
                    "line" : [],
                    "polygon" : [],
                    "all_geometry" : ["name","address"], # master field applied to all geometries selected on geometryType
                    }
                    },
                "geometryType": [
                    "point","line","polygon"
                ],
                joinFilterType:"OR" # options are and / or , 'or' by default -- applies condition for filters **optional
                }
        background_tasks (BackgroundTasks): task to cleanup the files produced during export
        request (Request): request instance

        Returns :
        {
            "task_id": "7d241e47-ffd6-405c-9312-614593f77b14",
            "track_link": "/current-snapshot/tasks/7d241e47-ffd6-405c-9312-614593f77b14/"
        }

        Sample Query :
        1. Sample query to extract point and polygon features that are marked building=*  with name attribute
        {
            "outputType": "GeoJSON",
            "fileName": "Pokhara_buildings",
            "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                    [
                        [
                        83.96919250488281,
                        28.194446860487773
                        ],
                        [
                        83.99751663208006,
                        28.194446860487773
                        ],
                        [
                        83.99751663208006,
                        28.214869548073377
                        ],
                        [
                        83.96919250488281,
                        28.214869548073377
                        ],
                        [
                        83.96919250488281,
                        28.194446860487773
                        ]
                    ]
                    ]
                },
            "filters": {"tags":{"all_geometry":{"building":[]}},"attributes":{"all_geometry":["name"]}},
            "geometryType": [
                "point","polygon"
            ]
        }
        2. Query to extract all OpenStreetMap features in a polygon in shapefile format:
        {
            "outputType": "shp",
            "fileName": "Pokhara_all_features",
            "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                    [
                        [
                        83.96919250488281,
                        28.194446860487773
                        ],
                        [
                        83.99751663208006,
                        28.194446860487773
                        ],
                        [
                        83.99751663208006,
                        28.214869548073377
                        ],
                        [
                        83.96919250488281,
                        28.214869548073377
                        ],
                        [
                        83.96919250488281,
                        28.194446860487773
                        ]
                    ]
                    ]
                }
        }
        3. Clean query to extract all features by deafult; output will be same as 2nd query but in GeoJSON format and output name will be `default`
        {
            "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                    [
                        [
                        83.96919250488281,
                        28.194446860487773
                        ],
                        [
                        83.99751663208006,
                        28.194446860487773
                        ],
                        [
                        83.99751663208006,
                        28.214869548073377
                        ],
                        [
                        83.96919250488281,
                        28.214869548073377
                        ],
                        [
                        83.96919250488281,
                        28.194446860487773
                        ]
                    ]
                    ]
                }
        }

    """
    # def get_current_data(params:RawDataCurrentParams,background_tasks: BackgroundTasks, user_data=Depends(login_required)): # this will use osm login makes it restrict login
    task = process_raw_data.delay(params)
    return JSONResponse({"task_id": task.id, "track_link": f"/tasks/status/{task.id}/"})