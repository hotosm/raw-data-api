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
from galaxy.query_builder.builder import format_file_name_str
from galaxy.validation.models import RawDataCurrentParams, RawDataOutputType
from galaxy.app import RawData, S3FileTransfer
from .api_worker import process_raw_data
from galaxy.config import export_rate_limit, use_s3_to_upload, logger as logging, config, limiter, allow_bind_zip_filter

router = APIRouter(prefix="/raw-data")

@router.get("/status/")
@version(1)
def check_current_db_status():
    """Gives status about how recent the osm data is , it will give the last time that database was updated completely"""
    result = RawData().check_status()
    return {"last_updated": result}


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
@version(1)
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