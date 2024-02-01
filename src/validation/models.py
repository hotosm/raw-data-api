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

from geojson_pydantic import Feature, FeatureCollection, MultiPolygon, Polygon
from geojson_pydantic.types import BBox
from pydantic import BaseModel as PydanticModel
from pydantic import Field, validator
from typing_extensions import TypedDict

from src.config import (
    ALLOW_BIND_ZIP_FILTER,
    ENABLE_HDX_EXPORTS,
    ENABLE_POLYGON_STATISTICS_ENDPOINTS,
    ENABLE_TILES,
)

if ENABLE_HDX_EXPORTS:
    from src.config import ALLOWED_HDX_TAGS, ALLOWED_HDX_UPDATE_FREQUENCIES


def to_camel(string: str) -> str:
    split_string = string.split("_")

    return "".join([split_string[0], *[w.capitalize() for w in split_string[1:]]])


class BaseModel(PydanticModel):
    class Config:
        alias_generator = to_camel
        populate_by_name = True
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
    @validator("geometry")
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


class RawDataCurrentParamsBase(BaseModel, GeometryValidatorMixin):
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
    geometry: Union[
        Polygon,
        MultiPolygon,
        Feature,
        FeatureCollection,
    ] = Field(
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
        if value:
            return list(set(value))
        return value


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
        json_schema_extra = {
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
        json_schema_extra = {
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
        json_schema_extra = {"example": {"lastUpdated": "2022-06-27 19:59:24+05:45"}}


class StatsRequestParams(BaseModel, GeometryValidatorMixin):
    iso3: Optional[str] = Field(
        default=None,
        description="ISO3 Country Code.",
        min_length=3,
        max_length=3,
        example="NPL",
    )
    geometry: Optional[
        Union[Polygon, MultiPolygon, Feature, FeatureCollection]
    ] = Field(
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

    @validator("geometry", pre=True, always=True)
    def set_geometry_or_iso3(cls, value, values):
        """Either geometry or iso3 should be supplied."""
        if value is not None and values.get("iso3") is not None:
            raise ValueError("Only one of geometry or iso3 should be supplied.")
        if value is None and values.get("iso3") is None:
            raise ValueError("Either geometry or iso3 should be supplied.")
        return value


### HDX BLock


class HDXModel(BaseModel):
    """
    Model for HDX configuration settings.

    Fields:
    - tags (List[str]): List of tags for the HDX model.
    - caveats (str): Caveats/Warning for the Datasets.
    - notes (str): Extra notes to append in the notes section of HDX datasets.
    """

    tags: List[str] = Field(
        default=["geodata"],
        description="List of tags for the HDX model.",
        example=["roads", "transportation", "geodata"],
    )
    caveats: str = Field(
        default="OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
        description="Caveats/Warning for the Datasets.",
        example="OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
    )
    notes: str = Field(
        default="",
        description="Extra notes to append in notes section of hdx datasets",
        example="Sample notes to append",
    )

    @validator("tags")
    def validate_tags(cls, value):
        """Validates tags if they are allowed from hdx allowed approved tags

        Args:
            value (_type_): _description_

        Raises:
            ValueError: _description_

        Returns:
            _type_: _description_
        """
        if value:
            for item in value:
                if ALLOWED_HDX_TAGS:
                    if item.strip() not in ALLOWED_HDX_TAGS:
                        raise ValueError(
                            f"Invalid tag {item.strip()} , Should be within {ALLOWED_HDX_TAGS}"
                        )
        return value


class CategoryModel(BaseModel):
    """
    Model for category configuration settings.

    Fields:
    - hdx (HDXModel): HDX configuration model.
    - types (List[str]): List of feature types (points, lines, polygons).
    - select (List[str]): List of selected fields.
    - where (str): SQL-like condition to filter features.
    - formats (List[str]): List of Export Formats (suffixes).
    """

    hdx: Optional[HDXModel] = Field(
        default=None, description="HDX Specific configurations"
    )
    types: List[str] = Field(
        ...,
        description="List of feature types (points, lines, polygons).",
        example=["lines"],
    )
    select: List[str] = Field(
        ...,
        description="List of selected fields.",
        example=["name", "highway"],
    )
    where: str = Field(
        ...,
        description="SQL-like condition to filter features.",
        example="highway IS NOT NULL",
    )
    formats: List[str] = Field(
        ...,
        description="List of Export Formats (suffixes).",
        example=["gpkg", "geojson"],
    )

    @validator("types")
    def validate_types(cls, value):
        """validates geom types

        Args:
            value (_type_): _description_

        Raises:
            ValueError: _description_

        Returns:
            _type_: _description_
        """
        allowed_types = {"points", "lines", "polygons"}
        for item in value:
            if item not in allowed_types:
                raise ValueError(
                    f"Invalid type: {item}. Allowed types are {', '.join(allowed_types)}"
                )
        return value

    @validator("formats")
    def validate_export_types(cls, value):
        """Validates export types if they are supported

        Args:
            value (_type_): _description_

        Raises:
            ValueError: _description_

        Returns:
            _type_: _description_
        """
        for export_type in value:
            if export_type not in EXPORT_TYPE_MAPPING:
                raise ValueError(f"Unsupported export type: {export_type}")
        return value


class ExportTypeInfo:
    """
    Class representing export type information.

    Fields:
    - suffix (str): File suffix for the export type.
    - driver_name (str): GDAL driver name.
    - layer_creation_options (List[str]): Layer creation options.
    - format_option (str): Format option for GDAL.
    """

    def __init__(self, suffix, driver_name, layer_creation_options, format_option):
        self.suffix = suffix
        self.driver_name = driver_name
        self.layer_creation_options = layer_creation_options
        self.format_option = format_option


EXPORT_TYPE_MAPPING = {
    "geojson": ExportTypeInfo("geojson", "GeoJSON", [], "GDAL"),
    "shp": ExportTypeInfo(
        "shp", "ESRI Shapefile", ["ENCODING=UTF-8,2GB_LIMIT=No,RESIZE=Yes"], "GDAL"
    ),
    "gpkg": ExportTypeInfo("gpkg", "GPKG", ["SPATIAL_INDEX=No"], "GDAL"),
    "sqlite": ExportTypeInfo("sqlite", "SQLite", [], "GDAL"),
    "fgb": ExportTypeInfo("fgb", "FlatGeobuf", ["VERIFY_BUFFERS=NO"], "GDAL"),
    "mvt": ExportTypeInfo("mvt", "MVT", [], "GDAL"),
    "kml": ExportTypeInfo("kml", "KML", [], "GDAL"),
    "gpx": ExportTypeInfo("gpx", "GPX", [], "GDAL"),
    "parquet": ExportTypeInfo("parquet", "PARQUET", [], "PARQUET"),
}


class DatasetConfig(BaseModel):
    """
    Model for dataset configuration settings.

    Fields:
    - private (bool): Make dataset private. By default False, public is recommended.
    - subnational (bool): Make it true if the dataset doesn't cover the nation/country.
    - update_frequency (str): Update frequency to be added on uploads.
    - dataset_title (str): Dataset title that appears at the top of the page.
    - dataset_prefix (str): Dataset prefix to be appended before the category name. Ignored if iso3 is supplied.
    - dataset_locations (List[str]): Valid dataset locations iso3.
    """

    private: bool = Field(
        default=False,
        description="Make dataset private , By default False , Public is recommended",
        example="False",
    )
    subnational: bool = Field(
        default=False,
        description="Make it true if dataset doesn't cover nation/country",
        example="False",
    )
    update_frequency: str = Field(
        default="as needed",
        description="Update frequncy to be added on uploads",
        example="daily",
    )
    dataset_title: str = Field(
        default=None,
        description="Dataset title which appears at top of the page",
        example="Nepal",
    )
    dataset_prefix: str = Field(
        default=None,
        description="Dataset prefix to be appended before category name, Will be ignored if iso3 is supplied",
        example="hotosm_npl",
    )
    dataset_locations: List[str] | None = Field(
        default=None,
        description="Valid dataset locations iso3",
        example="['npl']",
    )
    dataset_folder: str = Field(
        default="ISO3",
        description="Default base folder for the exports",
        example="ISO3",
    )

    @validator("update_frequency")
    def validate_frequency(cls, value):
        """Validates frequency

        Args:
            value (_type_): _description_

        Raises:
            ValueError: _description_

        Returns:
            _type_: _description_
        """
        if ALLOWED_HDX_UPDATE_FREQUENCIES:
            if value.strip() not in ALLOWED_HDX_UPDATE_FREQUENCIES:
                raise ValueError(
                    f"Invalid update frequency , Should be within {ALLOWED_HDX_UPDATE_FREQUENCIES}"
                )
        return value.strip()


class DynamicCategoriesModel(BaseModel, GeometryValidatorMixin):
    """
    Model for dynamic categories.

    Fields:
    - iso3 (Optional[str]): ISO3 Country Code.
    - dataset (Optional[DatasetConfig]): Dataset Configurations for HDX Upload.
    - meta (bool): Dumps Meta db in parquet format & HDX config JSON to S3.
    - hdx_upload (bool): Enable/Disable uploading the dataset to HDX.
    - categories (List[Dict[str, CategoryModel]]): List of dynamic categories.
    - geometry (Optional[Union[Polygon, MultiPolygon]]): Custom polygon geometry.
    """

    iso3: Optional[str] = Field(
        default=None,
        description="ISO3 Country Code",
        min_length=3,
        max_length=3,
        example="USA",
    )
    hdx_upload: bool = Field(
        default=False,
        description="Enable/Disable uploading dataset to hdx, False by default",
    )
    dataset: Optional[DatasetConfig] = Field(
        default=None, description="Dataset Configurations for HDX Upload"
    )
    queue: Optional[str] = Field(
        default="raw_special",
        description="Lets you decide which queue you wanna place your task, Requires admin access",
    )
    meta: bool = Field(
        default=False,
        description="Dumps Meta db in parquet format & hdx config json to s3",
    )
    categories: List[Dict[str, CategoryModel]] = Field(
        ...,
        description="List of dynamic categories.",
        example=[
            {
                "Roads": {
                    "hdx": {
                        "tags": ["roads", "transportation", "geodata"],
                        "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                    },
                    "types": ["lines", "polygons"],
                    "select": ["name", "highway"],
                    "where": "highway IS NOT NULL",
                    "formats": ["geojson"],
                }
            }
        ],
    )
    geometry: Optional[
        Union[Polygon, MultiPolygon, Feature, FeatureCollection]
    ] = Field(
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

    @validator("geometry", pre=True, always=True)
    def set_geometry_or_iso3(cls, value, values):
        """Either geometry or iso3 should be supplied."""
        if value is not None and values.get("iso3") is not None:
            raise ValueError("Only one of geometry or iso3 should be supplied.")
        if value is None and values.get("iso3") is None:
            raise ValueError("Either geometry or iso3 should be supplied.")
        if value is not None:
            dataset = values.get("dataset")
            if values.get("hdx_upload"):
                for category in values.get("categories"):
                    category_name, category_data = list(category.items())[0]
                    if category_data.hdx is None:
                        raise ValueError(f"HDX is missing for category {category}")

            if dataset is None and values.get("hdx_upload"):
                raise ValueError("Dataset config should be supplied for custom polygon")
            if values.get("hdx_upload"):
                for item in dataset:
                    if item is None:
                        raise ValueError(f"Missing, Dataset config : {item}")
        return value
