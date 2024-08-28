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

"""[Router Responsible for Raw data API ]"""

# Standard library imports
import json
from typing import AsyncGenerator

# Third party imports
import orjson
import redis
from area import area
from fastapi import APIRouter, Body, Depends, HTTPException, Request, Path, Query
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi_versioning import version

# Reader imports
from src.app import RawData
from src.config import (
    ALLOW_BIND_ZIP_FILTER,
    CELERY_BROKER_URL,
    DEFAULT_QUEUE_NAME,
    EXPORT_MAX_AREA_SQKM,
)
from src.config import LIMITER as limiter
from src.config import RATE_LIMIT_PER_MIN as export_rate_limit
from src.query_builder.builder import raw_currentdata_extraction_query
from src.validation.models import (
    RawDataCurrentParams,
    RawDataCurrentParamsBase,
    SnapshotResponse,
    StatusResponse,
    ErrorMessage,
    common_responses,
)

from .api_worker import process_raw_data
from .auth import AuthUser, UserRole, get_optional_user

router = APIRouter(prefix="", tags=["Extract"])

redis_client = redis.StrictRedis.from_url(CELERY_BROKER_URL)


@router.get(
    "/status", response_model=StatusResponse, responses={"500": {"model": ErrorMessage}}
)
@version(1)
def check_database_last_updated():
    """Gives status about how recent the osm data is. It will give the last time that database was updated completely"""
    result = RawData().check_status()
    return {"last_updated": result}


@router.post(
    "/snapshot",
    response_model=SnapshotResponse,
    responses={
        **common_responses,
        404: {"model": ErrorMessage},
        429: {"model": ErrorMessage},
    },
)
@limiter.limit(f"{export_rate_limit}/minute")
@version(1)
def get_osm_current_snapshot_as_file(
    request: Request,
    params: RawDataCurrentParams = Body(
        default={},
        openapi_examples={
            "normal": {
                "summary": "Example : Extract Evertyhing in the area",
                "description": "**Query** to Extract everything in the area , You can pass your geometry only and you will get everything on that area",
                "value": {
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [83.96919250488281, 28.194446860487773],
                                [83.99751663208006, 28.194446860487773],
                                [83.99751663208006, 28.214869548073377],
                                [83.96919250488281, 28.214869548073377],
                                [83.96919250488281, 28.194446860487773],
                            ]
                        ],
                    }
                },
            },
            "fileformats": {
                "summary": "An example with different file formats and filename",
                "description": "Raw Data API  can export data into multiple file formats . See outputype for more details",
                "value": {
                    "outputType": "shp",
                    "fileName": "Pokhara_all_features",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [83.96919250488281, 28.194446860487773],
                                [83.99751663208006, 28.194446860487773],
                                [83.99751663208006, 28.214869548073377],
                                [83.96919250488281, 28.214869548073377],
                                [83.96919250488281, 28.194446860487773],
                            ]
                        ],
                    },
                },
            },
            "filters": {
                "summary": "An example with filters and geometry type",
                "description": "Raw Data API  supports different kind of filters on both attributes and tags . See filters for more details",
                "value": {
                    "outputType": "geojson",
                    "fileName": "Pokhara_buildings",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [83.96919250488281, 28.194446860487773],
                                [83.99751663208006, 28.194446860487773],
                                [83.99751663208006, 28.214869548073377],
                                [83.96919250488281, 28.214869548073377],
                                [83.96919250488281, 28.194446860487773],
                            ]
                        ],
                    },
                    "filters": {
                        "tags": {"all_geometry": {"join_or": {"building": []}}},
                        "attributes": {"all_geometry": ["name"]},
                    },
                    "geometryType": ["point", "polygon"],
                },
            },
            "filters2": {
                "summary": "An example with more filters",
                "description": "Raw Data API  supports different kind of filters on both attributes and tags . See filters for more details",
                "value": {
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [83.585701, 28.046607],
                                [83.585701, 28.382561],
                                [84.391823, 28.382561],
                                [84.391823, 28.046607],
                                [83.585701, 28.046607],
                            ]
                        ],
                    },
                    "fileName": "my export",
                    "outputType": "geojson",
                    "geometryType": ["point", "polygon"],
                    "filters": {
                        "tags": {
                            "all_geometry": {
                                "join_or": {"building": []},
                                "join_and": {"amenity": ["cafe", "restaurant", "pub"]},
                            }
                        },
                        "attributes": {"all_geometry": ["name", "addr"]},
                    },
                },
            },
            "allfilters": {
                "summary": "An example with multiple level of filters",
                "description": "Raw Data API  supports multiple level of filters on point line polygon . See filters for more details",
                "value": {
                    "fileName": "Example export with all features",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [83.585701, 28.046607],
                                [83.585701, 28.382561],
                                [84.391823, 28.382561],
                                [84.391823, 28.046607],
                                [83.585701, 28.046607],
                            ]
                        ],
                    },
                    "outputType": "geojson",
                    "geometryType": ["point", "line", "polygon"],
                    "filters": {
                        "tags": {
                            "point": {
                                "join_or": {
                                    "amenity": [
                                        "bank",
                                        "ferry_terminal",
                                        "bus_station",
                                        "fuel",
                                        "kindergarten",
                                        "school",
                                        "college",
                                        "university",
                                        "place_of_worship",
                                        "marketplace",
                                        "clinic",
                                        "hospital",
                                        "police",
                                        "fire_station",
                                    ],
                                    "building": [
                                        "bank",
                                        "aerodrome",
                                        "ferry_terminal",
                                        "train_station",
                                        "bus_station",
                                        "pumping_station",
                                        "power_substation",
                                        "kindergarten",
                                        "school",
                                        "college",
                                        "university",
                                        "mosque ",
                                        " church ",
                                        " temple",
                                        "supermarket",
                                        "marketplace",
                                        "clinic",
                                        "hospital",
                                        "police",
                                        "fire_station",
                                        "stadium ",
                                        " sports_centre",
                                        "governor_office ",
                                        " townhall ",
                                        " subdistrict_office ",
                                        " village_office ",
                                        " community_group_office",
                                        "government_office",
                                    ],
                                    "man_made": [
                                        "tower",
                                        "water_tower",
                                        "pumping_station",
                                    ],
                                    "tower:type": ["communication"],
                                    "aeroway": ["aerodrome"],
                                    "railway": ["station"],
                                    "emergency": ["fire_hydrant"],
                                    "landuse": ["reservoir", "recreation_gound"],
                                    "waterway": ["floodgate"],
                                    "natural": ["spring"],
                                    "power": ["tower", "substation"],
                                    "shop": ["supermarket"],
                                    "leisure": [
                                        "stadium ",
                                        " sports_centre ",
                                        " pitch ",
                                        " swimming_pool",
                                        "park",
                                    ],
                                    "office": ["government"],
                                }
                            },
                            "line": {
                                "join_or": {
                                    "highway": [
                                        "motorway ",
                                        " trunk ",
                                        " primary ",
                                        " secondary ",
                                        " tertiary ",
                                        " service ",
                                        " residential ",
                                        " pedestrian ",
                                        " path ",
                                        " living_street ",
                                        " track",
                                    ],
                                    "railway": ["rail"],
                                    "man_made": ["embankment"],
                                    "waterway": [],
                                }
                            },
                            "polygon": {
                                "join_or": {
                                    "amenity": [
                                        "bank",
                                        "ferry_terminal",
                                        "bus_station",
                                        "fuel",
                                        "kindergarten",
                                        "school",
                                        "college",
                                        "university",
                                        "place_of_worship",
                                        "marketplace",
                                        "clinic",
                                        "hospital",
                                        "police",
                                        "fire_station",
                                    ],
                                    "building": [
                                        "bank",
                                        "aerodrome",
                                        "ferry_terminal",
                                        "train_station",
                                        "bus_station",
                                        "pumping_station",
                                        "power_substation",
                                        "power_plant",
                                        "kindergarten",
                                        "school",
                                        "college",
                                        "university",
                                        "mosque ",
                                        " church ",
                                        " temple",
                                        "supermarket",
                                        "marketplace",
                                        "clinic",
                                        "hospital",
                                        "police",
                                        "fire_station",
                                        "stadium ",
                                        " sports_centre",
                                        "governor_office ",
                                        " townhall ",
                                        " subdistrict_office ",
                                        " village_office ",
                                        " community_group_office",
                                        "government_office",
                                    ],
                                    "man_made": [
                                        "tower",
                                        "water_tower",
                                        "pumping_station",
                                    ],
                                    "tower:type": ["communication"],
                                    "aeroway": ["aerodrome"],
                                    "railway": ["station"],
                                    "landuse": ["reservoir", "recreation_gound"],
                                    "waterway": [],
                                    "natural": ["spring"],
                                    "power": ["substation", "plant"],
                                    "shop": ["supermarket"],
                                    "leisure": [
                                        "stadium ",
                                        " sports_centre ",
                                        " pitch ",
                                        " swimming_pool",
                                        "park",
                                    ],
                                    "office": ["government"],
                                    "type": ["boundary"],
                                    "boundary": ["administrative"],
                                }
                            },
                        },
                        "attributes": {
                            "point": [
                                "building",
                                "ground_floor:height",
                                "capacity:persons",
                                "building:structure",
                                "building:condition",
                                "name",
                                "admin_level",
                                "building:material",
                                "office",
                                "building:roof",
                                "backup_generator",
                                "access:roof",
                                "building:levels",
                                "building:floor",
                                "addr:full",
                                "addr:city",
                                "source",
                            ],
                            "line": ["width", "source", "waterway", "name"],
                            "polygon": [
                                "landslide_prone",
                                "name",
                                "admin_level",
                                "type",
                                "is_in:town",
                                "flood_prone",
                                "is_in:province",
                                "is_in:city",
                                "is_in:municipality",
                                "is_in:RW",
                                "is_in:village",
                                "source",
                                "boundary",
                            ],
                        },
                    },
                },
            },
        },
    ),
    user: AuthUser = Depends(get_optional_user),
):
    """Generates the current raw OpenStreetMap data available on database based on the input geometry, query and spatial features.

    Steps to Run Snapshot :

    1.  Post the your request here and your request will be on queue, endpoint will return as following :
        {
            "task_id": "your task_id",
            "track_link": "/tasks/task_id/"
        }
    2. Now navigate to /tasks/ with your task id to track progress and result\n


    Authentication is optional. If no token provided, it returns a user with limited options / guest user

    """
    if not (user.role is UserRole.STAFF.value or user.role is UserRole.ADMIN.value):
        if params.file_name:
            if "/" in params.file_name:
                raise HTTPException(
                    status_code=403,
                    detail=[
                        {
                            "msg": "Insufficient Permission to use folder structure exports , Remove / from filename or get access"
                        }
                    ],
                )
        area_m2 = area(json.loads(params.geometry.model_dump_json()))
        area_km2 = area_m2 * 1e-6
        RAWDATA_CURRENT_POLYGON_AREA = int(EXPORT_MAX_AREA_SQKM)
        if area_km2 > RAWDATA_CURRENT_POLYGON_AREA:
            raise HTTPException(
                status_code=400,
                detail=[
                    {
                        "msg": f"""Polygon Area {int(area_km2)} Sq.KM is higher than Threshold : {RAWDATA_CURRENT_POLYGON_AREA} Sq.KM"""
                    }
                ],
            )
        if not params.uuid:
            raise HTTPException(
                status_code=403,
                detail=[{"msg": "Insufficient Permission for uuid = False"}],
            )
        if ALLOW_BIND_ZIP_FILTER:
            if not params.bind_zip:
                ACCEPTABLE_STREAMING_AREA_SQKM2 = 200
                if area_km2 > ACCEPTABLE_STREAMING_AREA_SQKM2:
                    raise HTTPException(
                        status_code=406,
                        detail=[
                            {
                                "msg": f"Area {area_km2} km2 is greater than {ACCEPTABLE_STREAMING_AREA_SQKM2} km2 which is supported for streaming in this permission"
                            }
                        ],
                    )

    if user.id == 0 and params.include_user_metadata:
        raise HTTPException(
            status_code=403,
            detail=[
                {
                    "msg": "Insufficient Permission for extracting exports with user metadata, Please login first"
                }
            ],
        )
    queue_name = DEFAULT_QUEUE_NAME  # Everything directs to default now
    task = process_raw_data.apply_async(
        args=(params.model_dump(),),
        queue=queue_name,
        track_started=True,
        kwargs={"user": user.model_dump()},
    )
    return JSONResponse(
        {
            "task_id": task.id,
            "track_link": f"/tasks/status/{task.id}/",
            "queue": redis_client.llen(queue_name),
        }
    )


@router.post(
    "/snapshot/plain", responses={**common_responses, 404: {"model": ErrorMessage}}
)
@version(1)
async def get_osm_current_snapshot_as_plain_geojson(
    request: Request,
    params: RawDataCurrentParamsBase,
    user: AuthUser = Depends(get_optional_user),
):
    """Generates the Plain geojson for the polygon within 30 Sqkm and returns the result right away

    Args:
        request (Request): _description_
        params (RawDataCurrentParamsBase): Same as /snapshot except multiple output format options and configurations

    Returns:
        FeatureCollection: Geojson\n

    Authentication is optional. If no token provided, it returns a user with limited options / guest user
    """
    if user.id == 0 and params.include_user_metadata:
        raise HTTPException(
            status_code=403,
            detail=[
                {
                    "msg": "Insufficient Permission for extracting exports with user metadata, Please login first"
                }
            ],
        )
    area_m2 = area(json.loads(params.geometry.model_dump_json()))

    area_km2 = area_m2 * 1e-6
    if int(area_km2) > 6:
        raise HTTPException(
            status_code=400,
            detail=[
                {
                    "msg": f"""Polygon Area {int(area_km2)} Sq.KM is higher than Threshold : 6 Sq.KM"""
                }
            ],
        )

    params.output_type = "geojson"  # always geojson

    async def generate_geojson() -> AsyncGenerator[bytes, None]:
        # start of featurecollection
        yield b'{"type": "FeatureCollection", "features": ['

        raw_data = RawData(params)
        extraction_query = raw_currentdata_extraction_query(params)

        with raw_data.con.cursor(name="fetch_raw_quick") as cursor:
            cursor.itersize = 500
            cursor.execute(extraction_query)

            first_feature = True
            for row in cursor:
                feature = orjson.loads(row[0])
                if not first_feature:
                    # add comma to maintain the struct
                    yield b","
                else:
                    first_feature = False
                yield orjson.dumps(feature)
            cursor.close()

        # end of featurecollect
        yield b"]}"

    return StreamingResponse(generate_geojson(), media_type="application/geo+json")


@router.get("/countries", responses={"500": {"model": ErrorMessage}})
@version(1)
def get_countries(
    q: str = Query("", description="Query parameter for filtering countries"),
):
    """
    Gets Countries list from the database
    Args:
        q (str): query parameter for filtering countries
    Returns:
        featurecollection: geojson of country
    """

    result = RawData().get_countries_list(q)
    return result


@router.get("/countries/{cid}")
@version(1)
def get_specific_country(cid: int):
    result = RawData().get_country(cid)
    return result


@router.get(
    "/osm_id",
    responses={"404": {"model": ErrorMessage}, "500": {"model": ErrorMessage}},
)
@version(1)
def get_osm_feature(osm_id: int = Path(description="The OSM ID of feature")):
    """
    Gets geometry of osm_id in geojson
    Args:
        osm_id (int): osm_id of feature
    Returns:
        featurecollection: Geojson
    """

    return RawData().get_osm_feature(osm_id)
