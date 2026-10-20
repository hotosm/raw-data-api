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
"""Pydantic models for osm2pgsql query parameters and filter configuration."""

from typing import Dict, List, Optional, Union

from geojson_pydantic import Feature, FeatureCollection, MultiPolygon, Polygon
from pydantic import BaseModel as PydanticModel
from pydantic import ConfigDict, Field, field_validator

from .enums import SupportedGeometryFilters


def to_camel(string: str) -> str:
    split_string = string.split("_")

    return "".join([split_string[0], *[w.capitalize() for w in split_string[1:]]])


class BaseModel(PydanticModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        use_enum_values=True,
    )


class JoinFilterType:
    OR = "OR"
    AND = "AND"


class SQLFilter(BaseModel):
    join_or: Optional[Dict[str, List[str]]] = Field(default=None)
    join_and: Optional[Dict[str, List[str]]] = Field(default=None)


class TagsFilter(BaseModel):
    point: Optional[SQLFilter] = Field(default=None)
    line: Optional[SQLFilter] = Field(default=None)
    polygon: Optional[SQLFilter] = Field(default=None)
    all_geometry: Optional[SQLFilter] = Field(default=None)


class AttributeFilter(BaseModel):
    point: Optional[List[str]] = Field(default=None)
    line: Optional[List[str]] = Field(default=None)
    polygon: Optional[List[str]] = Field(default=None)
    all_geometry: Optional[List[str]] = Field(default=None)


class Filters(BaseModel):
    tags: Optional[TagsFilter] = Field(default=None)
    attributes: Optional[AttributeFilter] = Field(default=None)


class GeometryValidatorMixin:
    @field_validator("geometry")
    @classmethod
    def validate_geometry(cls, value):
        """Validates geometry"""
        if value:
            if value.type == "Feature":
                if value.geometry.type not in ["Polygon", "MultiPolygon"]:
                    raise ValueError(
                        f"Feature geometry type {value.geometry.type} must be of type polygon/multipolygon",
                    )
                return value.geometry
            if value.type == "FeatureCollection":
                for feature in value.features:
                    if feature.geometry.type not in ["Polygon", "MultiPolygon"]:
                        raise ValueError(
                            f"Feature Collection can't have {feature.type} , should be polygon/multipolygon"
                        )
                if len(value.features) > 1:
                    raise ValueError(
                        "Feature collection with multiple features is not supported yet"
                    )
                return value.features[0].geometry
        return value


class SnapshotQueryParams(BaseModel, GeometryValidatorMixin):
    """Base parameters for snapshot extraction queries.

    Subclass this to add application-specific fields (e.g. output format enums,
    file naming, zoom levels).
    """

    output_type: Optional[str] = Field(
        default="geojson", json_schema_extra={"example": "geojson"}
    )
    geometry_type: Optional[List[SupportedGeometryFilters]] = Field(
        default=None, json_schema_extra={"example": ["point", "polygon"]}
    )
    centroid: Optional[bool] = Field(
        default=False, description="Exports centroid of features as geom"
    )
    use_st_within: Optional[bool] = Field(
        default=True,
        description="Exports features which are exactly inside the passed polygons (ST_WITHIN) By default features which are intersected with passed polygon is exported",
    )
    include_user_metadata: Optional[bool] = Field(
        default=False,
        description="Include user metadata on exports , Only available to logged in users",
    )
    filters: Optional[Filters] = Field(
        default=None,
        json_schema_extra={
            "example": {
                "tags": {"all_geometry": {"join_or": {"building": []}}},
                "attributes": {"all_geometry": ["name"]},
            },
        },
        description="Filter for point,line,polygon/ all geometry for both select and where clause, All geometry filter means : It will apply the same filter to all the geometry type",
    )
    geometry: Union[
        Polygon,
        MultiPolygon,
        Feature,
        FeatureCollection,
    ] = Field(
        json_schema_extra={
            "example": {
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
    )

    @field_validator("geometry_type")
    @classmethod
    def return_unique_value(cls, value):
        """return unique list"""
        if value:
            return list(set(value))
        return value


class CategoryBase(BaseModel):
    """Base model for category configuration.

    Subclass this to add application-specific fields (e.g. hdx config,
    export formats with validation).
    """

    types: List[str] = Field(
        ...,
        description="List of feature types (points, lines, polygons).",
        json_schema_extra={"example": ["lines"]},
    )
    select: List[str] = Field(
        ...,
        description="List of selected fields.",
        json_schema_extra={"example": ["name", "highway"]},
    )
    where: str = Field(
        ...,
        description="SQL-like condition to filter features.",
        json_schema_extra={"example": "highway IS NOT NULL"},
    )

    @field_validator("types")
    @classmethod
    def validate_types(cls, value):
        """validates geom types"""
        allowed_types = {"points", "lines", "polygons"}
        for item in value:
            if item not in allowed_types:
                raise ValueError(
                    f"Invalid type: {item}. Allowed types are {', '.join(allowed_types)}"
                )
        return value
