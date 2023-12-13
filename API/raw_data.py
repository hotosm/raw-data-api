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
import json
import os
import shutil
import time

import requests
from area import area
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi_versioning import version
from geojson import FeatureCollection

from src.app import RawData
from src.config import ALLOW_BIND_ZIP_FILTER, EXPORT_MAX_AREA_SQKM
from src.config import LIMITER as limiter
from src.config import RATE_LIMIT_PER_MIN as export_rate_limit
from src.config import logger as logging
from src.validation.models import (
    RawDataCurrentParams,
    RawDataCurrentParamsBase,
    SnapshotResponse,
    StatusResponse,
)

from .api_worker import process_raw_data
from .auth import AuthUser, UserRole, get_optional_user

router = APIRouter(prefix="", tags=["Extract"])


@router.get("/status/", response_model=StatusResponse)
@version(1)
def check_database_last_updated():
    """Gives status about how recent the osm data is , it will give the last time that database was updated completely"""
    result = RawData().check_status()
    return {"last_updated": result}


@router.post("/snapshot/", response_model=SnapshotResponse)
@limiter.limit(f"{export_rate_limit}/minute")
@version(1)
def get_osm_current_snapshot_as_file(
    request: Request,
    params: RawDataCurrentParams = Body(
        default={},
        examples={
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
    2. Now navigate to /tasks/ with your task id to track progress and result

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
        area_m2 = area(json.loads(params.geometry.json()))
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

    queue_name = "recurring_queue" if not params.uuid else "raw_default"
    task = process_raw_data.apply_async(
        args=(params,), queue=queue_name, track_started=True
    )
    return JSONResponse({"task_id": task.id, "track_link": f"/tasks/status/{task.id}/"})


@router.post("/snapshot/plain/", response_model=FeatureCollection)
@version(1)
def get_osm_current_snapshot_as_plain_geojson(
    request: Request,
    params: RawDataCurrentParamsBase,
    user: AuthUser = Depends(get_optional_user),
):
    """Generates the Plain geojson for the polygon within 30 Sqkm and returns the result right away

    Args:
        request (Request): _description_
        params (RawDataCurrentParamsBase): Same as /snapshot excpet multiple output format options and configurations

    Returns:
        Featurecollection: Geojson
    """
    area_m2 = area(json.loads(params.geometry.json()))
    area_km2 = area_m2 * 1e-6
    if area_km2 > 10:
        raise HTTPException(
            status_code=400,
            detail=[
                {
                    "msg": f"""Polygon Area {int(area_km2)} Sq.KM is higher than Threshold : 10 Sq.KM"""
                }
            ],
        )
    params.output_type = "geojson"  # always geojson
    result = RawData(params).extract_plain_geojson()
    return result


@router.get("/countries/", response_model=FeatureCollection)
@version(1)
def get_countries(q: str = ""):
    result = RawData().get_countries_list(q)
    return result


@router.get("/osm_id/", response_model=FeatureCollection)
@version(1)
def get_osm_feature(osm_id: int):
    return RawData().get_osm_feature(osm_id)
