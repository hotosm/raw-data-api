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

from src.galaxy.config import use_s3_to_upload, logger as logging, config

router = APIRouter(prefix="/raw-data")

# @router.post("/historical-snapshot/")
# def get_historical_data(params:RawDataHistoricalParams):
#     start_time = time.time()
#     result= RawData(params).extract_historical_data()
#     return generate_rawdata_response(result,start_time)


@router.post("/current-snapshot/")
@version(1)
def get_current_data(params: RawDataCurrentParams, background_tasks: BackgroundTasks, request: Request):
    """Generates the current raw OpenStreetMap data available on database based on the input geometry, query and spatial features

    Args:

        params (RawDataCurrentParams):
                {
                "outputType": "GeoJSON",
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
                ]
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
    if params.output_type is None:  # if no ouput type is supplied default is geojson output
        params.output_type = RawDataOutputType.GEOJSON.value

    # unique id for zip file and geojson for each export
    if params.file_name:
        # need to format string from space to _ because it is filename , may be we need to filter special character as well later on
        formatted_file_name = format_file_name_str(params.file_name)
        # exportname = f"{formatted_file_name}_{datetime.now().isoformat()}_{str(uuid4())}"
        exportname = f"""{formatted_file_name}_{str(uuid4())}_{params.output_type}"""  # disabled date for now

    else:
        # exportname = f"Raw_Export_{datetime.now().isoformat()}_{str(uuid4())}"
        exportname = f"Raw_Export_{str(uuid4())}_{params.output_type}"

    logging.info("Request %s received", exportname)

    dump_temp_file, geom_area, root_dir_file = RawData(
        params).extract_current_data(exportname)
    path = f"""{root_dir_file}{exportname}/"""

    if os.path.exists(path) is False:
        return JSONResponse(
            status_code=400,
            content={"Error": "Request went too big"}
        )

    logging.debug('Zip Binding Started !')
    # saving file in temp directory instead of memory so that zipping file will not eat memory
    zip_temp_path = f"""{root_dir_file}{exportname}.zip"""
    zf = zipfile.ZipFile(zip_temp_path, "w", zipfile.ZIP_DEFLATED)

    directory = pathlib.Path(path)
    for file_path in directory.iterdir():
        zf.write(file_path, arcname=file_path.name)

    # Compressing geojson file
    zf.writestr("clipping_boundary.geojson",
                orjson.dumps(dict(params.geometry)))

    zf.close()
    logging.debug('Zip Binding Done !')
    inside_file_size = 0
    for temp_file in dump_temp_file:
        # clearing tmp geojson file since it is already dumped to zip file we don't need it anymore
        if os.path.exists(temp_file):
            inside_file_size += os.path.getsize(temp_file)

    # remove the file that are just binded to zip file , we no longer need to store it
    background_tasks.add_task(remove_file, path)

    # check if download url will be generated from s3 or not from config
    if use_s3_to_upload:
        file_transfer_obj = S3FileTransfer()
        download_url = file_transfer_obj.upload(zip_temp_path, exportname)
        # watches the status code of the link provided and deletes the file if it is 200
        background_tasks.add_task(watch_s3_upload, download_url, zip_temp_path)
    else:

        # getting from config in case api and frontend is not hosted on same url
        client_host = config.get(
            "API_CONFIG", "api_host", fallback=f"""{request.url.scheme}://{request.client.host}""")
        client_port = config.get("API_CONFIG", "api_port", fallback=8000)

        if client_port:
            download_url = f"""{client_host}:{client_port}/v1/exports/{exportname}.zip"""  # disconnected download portion from this endpoint because when there will be multiple hits at a same time we don't want function to get stuck waiting for user to download the file and deliver the response , we want to reduce waiting time and free function !
        else:
            download_url = f"""{client_host}/v1/exports/{exportname}.zip"""  # disconnected download portion from this endpoint because when there will be multiple hits at a same time we don't want function to get stuck waiting for user to download the file and deliver the response , we want to reduce waiting time and free function !

    # getting file size of zip , units are in bytes converted to mb in response
    zip_file_size = os.path.getsize(zip_temp_path)
    response_time = dt.now() - start_time
    response_time_str = str(response_time)
    logging.info(
        f"Done Export : {exportname} of {round(inside_file_size/1000000)} MB / {geom_area} sqkm in {response_time_str}")

    return {"download_url": download_url, "file_name": exportname, "response_time": response_time_str, "query_area": f"""{geom_area} Sq Km """, "binded_file_size": f"""{round(inside_file_size/1000000)} MB""", "zip_file_size_bytes": {zip_file_size}}


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
