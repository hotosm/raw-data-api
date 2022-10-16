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
from typing import List, Union, Optional
from pydantic import validator
from pydantic import BaseModel as PydanticModel
from geojson_pydantic import Polygon, MultiPolygon
from enum import Enum
from area import area
from src.galaxy.config import config, allow_bind_zip_filter


def to_camel(string: str) -> str:
    split_string = string.split("_")

    return "".join(
        [split_string[0], *[w.capitalize() for w in split_string[1:]]])


class BaseModel(PydanticModel):
    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True
        use_enum_values = True


class RawDataOutputType (Enum):
    GEOJSON = "GeoJSON"
    KML = "kml"
    SHAPEFILE = "shp"
    FLATGEOBUF = "fgb"
    MBTILES = "mbtiles"  # fully experimental for now
    GEOPACKAGE = "gpkg"


class SupportedFilters(Enum):
    TAGS = "tags"
    ATTRIBUTES = "attributes"

    @classmethod
    def has_value(cls, value):
        """Checks value"""
        return value in cls._value2member_map_


class SupportedGeometryFilters(Enum):
    POINT = 'point'
    LINE = 'line'
    POLYGON = 'polygon'
    ALLGEOM = 'all_geometry'

    @classmethod
    def has_value(cls, value):
        """Checks if the value is supported"""
        return value in cls._value2member_map_


class JoinFilterType (Enum):
    OR = "OR"
    AND = "AND"


class RawDataCurrentParams(BaseModel):
    output_type: Optional[RawDataOutputType] = None
    file_name: Optional[str] = None
    geometry: Union[Polygon, MultiPolygon]
    filters: Optional[dict] = None
    join_filter_type: Optional[JoinFilterType] = None
    geometry_type: Optional[List[SupportedGeometryFilters]] = None
    if allow_bind_zip_filter:
        bind_zip: Optional[bool] = True

        @validator("bind_zip", allow_reuse=True)
        def check_bind_option(cls, value, values):
            """checks if shp is selected along with bind to zip file"""
            if value is False and values.get("output_type") == 'shp':
                raise ValueError(
                    "Can't deliver Shapefile without zip , Remove bind_zip paramet or set it to True")
            return value

    @validator("filters", allow_reuse=True)
    def check_value(cls, value, values):
        """Checks given fields"""
        for key, v in value.items():
            if SupportedFilters.has_value(key):  # check for tags or attributes
                # check if value is of dict type or not for tags and attributes
                if isinstance(v, dict):
                    for k, val in v.items():
                        # now checking either point line or polygon
                        if SupportedGeometryFilters.has_value(k):
                            if key == SupportedFilters.TAGS.value:  # if it is tag then value should be of dictionary
                                if isinstance(val, dict):
                                    # if it is dictionary it should be of type key:['value']
                                    for osmkey, osmvalue in val.items():
                                        if isinstance(osmvalue, list):
                                            pass
                                        else:
                                            raise ValueError(
                                                f"""Osm value --{osmvalue}-- should be inside List : {key}-{k}-{val}-{osmvalue}""")
                                else:
                                    raise ValueError(
                                        f"""Type of {val} filter in {key} - {k} - {val} should be dictionary""")
                            elif key == SupportedFilters.ATTRIBUTES.value:
                                # if it is attributes then value should be of list i.e. "point":[]
                                if isinstance(val, list):
                                    pass
                                else:
                                    raise ValueError(
                                        f"""Type of {val} filter in {key} - {k} - {val} should be list""")
                        else:
                            raise ValueError(
                                f"""Value {k} for filter {key} - {k} is not supported""")
                else:
                    raise ValueError(
                        f"""Value for filter {key} should be of dict Type""")
            else:
                raise ValueError(
                    f"""Filter {key} is not supported. Supported filters are 'tags' and 'attributes'""")
        return value

    @validator("geometry", always=True)
    def check_geometry_area(cls, value, values):
        """Validates geom area_m2"""
        area_m2 = area(json.loads(value.json()))
        area_km2 = area_m2 * 1E-6

        RAWDATA_CURRENT_POLYGON_AREA = int(config.get(
            "API_CONFIG", "max_area", fallback=100000))

        output_type = values.get("output_type")
        if output_type:
            # for mbtiles ogr2ogr does very worst job when area gets bigger we should write owr own or find better approach for larger area
            if output_type == RawDataOutputType.MBTILES.value:
                RAWDATA_CURRENT_POLYGON_AREA = 2  # we need to figure out how much tile we are generating before passing request on the basis of bounding box we can restrict user , right now relation contains whole country for now restricted to this area but can not query relation will take ages because that will intersect with country boundary : need to clip it
        if area_km2 > RAWDATA_CURRENT_POLYGON_AREA:
            raise ValueError(
                f"""Polygon Area {int(area_km2)} Sq.KM is higher than Threshold : {RAWDATA_CURRENT_POLYGON_AREA} Sq.KM""")
        return value
