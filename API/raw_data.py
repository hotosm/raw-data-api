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

# from .auth import login_required
from starlette.background import BackgroundTasks
from fastapi import APIRouter, Request
from fastapi_versioning import version
from fastapi.responses import JSONResponse

# from fastapi import APIRouter, Depends, Request
from src.galaxy.validation.models import RawDataCurrentParams
from src.galaxy.app import RawData
from celery.result import AsyncResult
from .api_worker import process_raw_data

router = APIRouter(prefix="/raw-data")

# @router.post("/historical-snapshot/")
# def get_historical_data(params:RawDataHistoricalParams):
#     start_time = time.time()
#     result= RawData(params).extract_historical_data()
#     return generate_rawdata_response(result,start_time)


@router.post("/current-snapshot/")
@version(1)
def get_current_data(
    params: RawDataCurrentParams, background_tasks: BackgroundTasks, request: Request
):
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
    task = process_raw_data.delay(request.url.scheme, request.client.host, params, background_tasks)
    return JSONResponse({"task_id": task.id, "track_link": f"/current-snapshot/tasks/{task.id}/"})


@router.get("/current-snapshot/tasks/{task_id}/")
def get_status(task_id):
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }
    return JSONResponse(result)


@router.get("/status/")
@version(1)
def check_current_db_status():
    """Gives status about DB update, Substracts with current time and last db update time"""
    result = RawData().check_status()
    response = f"{result} ago"
    return {"last_updated": response}
