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
"""Page contains validation models for application"""
import json
from enum import Enum
from typing import Dict, List, Optional, Union

from geojson_pydantic import MultiPolygon, Polygon
from geojson_pydantic.types import BBox
from pydantic import BaseModel as PydanticModel
from pydantic import Field, validator
from typing_extensions import TypedDict

from src.config import (
    ALLOW_BIND_ZIP_FILTER,
    ENABLE_POLYGON_STATISTICS_ENDPOINTS,
    ENABLE_TILES,
    EXPORT_MAX_AREA_SQKM,
)


def to_camel(string: str) -> str:
    split_string = string.split("_")

    return "".join([split_string[0], *[w.capitalize() for w in split_string[1:]]])


class BaseModel(PydanticModel):
    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True
        use_enum_values = True
        # extra = "forbid"


class RawDataOutputType(Enum):
    GEOJSON = "geojson"
    KML = "kml"
    SHAPEFILE = "shp"
    FLATGEOBUF = "fgb"
    GEOPACKAGE = "gpkg"
    PGDUMP = "sql"
    CSV = "csv"
    GEOPARQUET = "parquet"
    if ENABLE_TILES:
        MBTILES = "mbtiles"
        PMTILES = "pmtiles"  ## EXPERIMENTAL


class SupportedFilters(Enum):
    TAGS = "tags"
    ATTRIBUTES = "attributes"

    @classmethod
    def has_value(cls, value):
        """Checks value"""
        return value in cls._value2member_map_


class SupportedGeometryFilters(Enum):
    POINT = "point"
    LINE = "line"
    POLYGON = "polygon"
    ALLGEOM = "all_geometry"

    @classmethod
    def has_value(cls, value):
        """Checks if the value is supported"""
        return value in cls._value2member_map_


class JoinFilterType(Enum):
    OR = "OR"
    AND = "AND"


class SQLFilter(BaseModel):
    join_or: Optional[Dict[str, List[str]]]
    join_and: Optional[Dict[str, List[str]]]


class TagsFilter(BaseModel):
    point: Optional[SQLFilter]
    line: Optional[SQLFilter]
    polygon: Optional[SQLFilter]
    all_geometry: Optional[SQLFilter]


class AttributeFilter(BaseModel):
    point: Optional[List[str]]
    line: Optional[List[str]]
    polygon: Optional[List[str]]
    all_geometry: Optional[List[str]]


class Filters(BaseModel):
    tags: Optional[TagsFilter]
    attributes: Optional[AttributeFilter]


class RawDataCurrentParamsBase(BaseModel):
    output_type: Optional[RawDataOutputType] = Field(
        default=RawDataOutputType.GEOJSON.value, example="geojson"
    )
    geometry_type: Optional[List[SupportedGeometryFilters]] = Field(
        default=None, example=["point", "polygon"]
    )
    centroid: Optional[bool] = Field(
        default=False, description="Exports centroid of features as geom"
    )
    use_st_within: Optional[bool] = Field(
        default=True,
        description="Exports features which are exactly inside the passed polygons (ST_WITHIN) By default features which are intersected with passed polygon is exported",
    )
    if ENABLE_POLYGON_STATISTICS_ENDPOINTS:
        include_stats: Optional[bool] = Field(
            default=False,
            description="Includes detailed stats about the polygon passed such as buildings count , road count along with summary about data completeness in the area",
        )
    filters: Optional[Filters] = Field(
        default=None,
        example={
            "tags": {"all_geometry": {"join_or": {"building": []}}},
            "attributes": {"all_geometry": ["name"]},
        },
        description="Filter for point,line,polygon/ all geometry for both select and where clause, All geometry filter means : It will apply the same filter to all the geometry type",
    )
    geometry: Union[Polygon, MultiPolygon] = Field(
        default=None,
        example={
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
    )

    @validator("geometry_type", allow_reuse=True)
    def return_unique_value(cls, value):
        """return unique list"""
        return list(set(value))


class RawDataCurrentParams(RawDataCurrentParamsBase):
    if ENABLE_TILES:
        min_zoom: Optional[int] = Field(
            default=None, description="Only for mbtiles"
        )  # only for if mbtiles is output
        max_zoom: Optional[int] = Field(
            default=None, description="Only for mbtiles"
        )  # only for if mbtiles is output
    file_name: Optional[str] = Field(default=None, example="My test export")
    uuid: Optional[bool] = Field(
        default=True,
        description="Attaches uid to exports by default , Only disable this if it is recurring export",
    )
    if ALLOW_BIND_ZIP_FILTER:
        bind_zip: Optional[bool] = True

        @validator("bind_zip", allow_reuse=True)
        def check_bind_option(cls, value, values):
            """Checks if cloud optimized output format or geoJSON is selected along with bind to zip file"""
            if value is False:
                if values.get("output_type") not in (
                    (
                        [
                            RawDataOutputType.GEOJSON.value,
                            RawDataOutputType.FLATGEOBUF.value,
                            RawDataOutputType.GEOPARQUET.value,
                        ]
                        + ([RawDataOutputType.PMTILES.value] if ENABLE_TILES else [])
                    )
                ):
                    raise ValueError(
                        "Only Cloud Optimized format and GeoJSON is supported for streaming"
                    )
            return value


class SnapshotResponse(BaseModel):
    task_id: str
    track_link: str

    class Config:
        schema_extra = {
            "example": {
                "task_id": "aa539af6-83d4-4aa3-879e-abf14fffa03f",
                "track_link": "/tasks/status/aa539af6-83d4-4aa3-879e-abf14fffa03f/",
            }
        }


class SnapshotTaskResult(BaseModel):
    download_url: str
    file_name: str
    response_time: str
    query_area: str
    binded_file_size: str
    zip_file_size_bytes: int


class SnapshotTaskResponse(BaseModel):
    id: str
    status: str
    result: SnapshotTaskResult

    class Config:
        schema_extra = {
            "example": {
                "id": "3fded368-456f-4ef4-a1b8-c099a7f77ca4",
                "status": "SUCCESS",
                "result": {
                    "download_url": "https://s3.us-east-1.amazonaws.com/exports-stage.hotosm.org/Raw_Export_3fded368-456f-4ef4-a1b8-c099a7f77ca4_GeoJSON.zip",
                    "file_name": "Raw_Export_3fded368-456f-4ef4-a1b8-c099a7f77ca4_GeoJSON",
                    "response_time": "0:00:12.175976",
                    "query_area": "6 Sq Km ",
                    "binded_file_size": "7 MB",
                    "zip_file_size_bytes": 1331601,
                },
            }
        }


class StatusResponse(BaseModel):
    last_updated: str

    class Config:
        schema_extra = {"example": {"lastUpdated": "2022-06-27 19:59:24+05:45"}}


class StatsRequestParams(BaseModel):
    geometry: Union[Polygon, MultiPolygon] = Field(
        example={
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
    )

    @validator("geometry", allow_reuse=True)
    def get_value_as_feature(cls, value):
        """Converts geometry to geojson feature"""
        feature = {
            "type": "Feature",
            "geometry": json.loads(value.json()),
            "properties": {},
        }
        return feature
