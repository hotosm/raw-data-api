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

from area import area
from geojson_pydantic import MultiPolygon, Polygon
from geojson_pydantic.types import BBox
from pydantic import BaseModel as PydanticModel
from pydantic import Field, validator
from typing_extensions import TypedDict

from src.config import ALLOW_BIND_ZIP_FILTER, EXPORT_MAX_AREA_SQKM


def to_camel(string: str) -> str:
    split_string = string.split("_")

    return "".join([split_string[0], *[w.capitalize() for w in split_string[1:]]])


class BaseModel(PydanticModel):
    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True
        use_enum_values = True
        extra = "forbid"


class RawDataOutputType(Enum):
    GEOJSON = "geojson"
    KML = "kml"
    SHAPEFILE = "shp"
    FLATGEOBUF = "fgb"
    MBTILES = "mbtiles"  # fully experimental for now
    GEOPACKAGE = "gpkg"
    PGDUMP = "sql"
    CSV = "csv"
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


#
#     "tags": { # no of rows returned
#       "point" : {"amenity":["shop"]},
#       "line" : {},
#       "polygon" : {"key":["value"]},
#       "all_geometry" : {"building":['yes']}
#       },
#     "attributes": { # no of columns / name
#       "point": [], column
#       "line" : [],
#       "polygon" : [],
#       "all_geometry" : [],
#       }
#      }


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


class RawDataCurrentParams(BaseModel):
    output_type: Optional[RawDataOutputType] = Field(
        default=RawDataOutputType.GEOJSON.value, example="geojson"
    )
    min_zoom: Optional[int] = Field(
        default=None, description="Only for mbtiles"
    )  # only for if mbtiles is output
    max_zoom: Optional[int] = Field(
        default=None, description="Only for mbtiles"
    )  # only for if mbtiles is output
    file_name: Optional[str] = Field(default=None, example="My test export")
    geometry_type: Optional[List[SupportedGeometryFilters]] = Field(
        default=None, example=["point", "polygon"]
    )
    centroid: Optional[bool] = Field(
        default=False, description="Exports centroid of features as geom"
    )
    use_st_within: Optional[bool] = Field(
        default=False,
        description="Exports features which are exactly inside the passed polygons (ST_WITHIN) By default features which are intersected with passed polygon is exported",
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
    uuid: Optional[bool] = Field(
        default=True,
        description="Attaches uid to exports by default , Only disable this if it is recurring export",
    )
    if ALLOW_BIND_ZIP_FILTER:
        bind_zip: Optional[bool] = True

        @validator("bind_zip", allow_reuse=True)
        def check_bind_option(cls, value, values):
            """checks if shp is selected along with bind to zip file"""
            if value is False and values.get("output_type") == "shp":
                raise ValueError(
                    "Can't deliver Shapefile without zip , Remove bind_zip paramet or set it to True"
                )
            return value

    @validator("output_type", allow_reuse=True)
    def check_output_type(cls, value, values):
        """Checks mbtiles required field"""
        if value == RawDataOutputType.MBTILES.value:
            if values.get("min_zoom") and values.get("max_zoom"):
                if values.get("min_zoom") < 0 or values.get("max_zoom") > 22:
                    raise ValueError("Zoom range should range from 0-22")
                return value
            else:
                raise ValueError(
                    "Field min_zoom and max_zoom must be supplied for mbtiles output type"
                )
        return value

    @validator("geometry", always=True)
    def check_geometry_area(cls, value, values):
        """Validates geom area_m2"""
        area_m2 = area(json.loads(value.json()))
        area_km2 = area_m2 * 1e-6

        RAWDATA_CURRENT_POLYGON_AREA = int(EXPORT_MAX_AREA_SQKM)

        output_type = values.get("output_type")
        if output_type:
            # for mbtiles ogr2ogr does very worst job when area gets bigger we should write owr own or find better approach for larger area
            if output_type == RawDataOutputType.MBTILES.value:
                RAWDATA_CURRENT_POLYGON_AREA = 2  # we need to figure out how much tile we are generating before passing request on the basis of bounding box we can restrict user , right now relation contains whole country for now restricted to this area but can not query relation will take ages because that will intersect with country boundary : need to clip it
        if area_km2 > RAWDATA_CURRENT_POLYGON_AREA:
            raise ValueError(
                f"""Polygon Area {int(area_km2)} Sq.KM is higher than Threshold : {RAWDATA_CURRENT_POLYGON_AREA} Sq.KM for {output_type}"""
            )
        return value

    @validator("geometry_type", allow_reuse=True)
    def return_unique_value(cls, value):
        """return unique list"""
        return list(set(value))


class WhereCondition(TypedDict):
    key: str
    value: List[str]


class OsmFeatureType(Enum):
    NODES = "nodes"
    WAYS_LINE = "ways_line"
    WAYS_POLY = "ways_poly"
    RELATIONS = "relations"


class SnapshotParamsPlain(BaseModel):
    bbox: Optional[
        BBox
    ] = None  # xmin: NumType, ymin: NumType, xmax: NumType, ymax: NumType , srid:4326
    select: Optional[List[str]] = ["*"]
    where: List[WhereCondition] = [{"key": "building", "value": ["*"]}]
    join_by: Optional[JoinFilterType] = JoinFilterType.OR.value
    look_in: Optional[List[OsmFeatureType]] = ["nodes", "ways_poly"]
    geometry_type: SupportedGeometryFilters = None

    @validator("select", always=True)
    def validate_select_statement(cls, value, values):
        """Validates geom area_m2"""
        for v in value:
            if v != "*" and len(v) < 2:
                raise ValueError(
                    "length of select attribute must be greater than 2 letters"
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
