from enum import Enum
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, Body, Query, Request
from fastapi_versioning import version
from geojson_pydantic import MultiPolygon, Polygon
from pydantic import BaseModel, Field, validator

from src.app import HDX
from src.config import ALLOWED_HDX_TAGS, ALLOWED_HDX_UPDATE_FREQUENCIES
from src.config import LIMITER as limiter
from src.config import RATE_LIMIT_PER_MIN

router = APIRouter(prefix="/hdx", tags=["HDX"])


class HDXModel(BaseModel):
    tags: List[str] = Field(
        ...,
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
        for item in value:
            if item.strip() not in ALLOWED_HDX_TAGS:
                raise ValueError(
                    f"Invalid tag {item.strip()} , Should be within {ALLOWED_HDX_TAGS}"
                )
        return value


class CategoryModel(BaseModel):
    hdx: HDXModel
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
        allowed_types = {"points", "lines", "polygons"}
        for item in value:
            if item not in allowed_types:
                raise ValueError(
                    f"Invalid type: {item}. Allowed types are {', '.join(allowed_types)}"
                )
        return value

    @validator("formats")
    def validate_export_types(cls, value):
        for export_type in value:
            if export_type not in EXPORT_TYPE_MAPPING:
                raise ValueError(f"Unsupported export type: {export_type}")
        return [EXPORT_TYPE_MAPPING[export_type] for export_type in value]


class ExportTypeInfo:
    def __init__(self, suffix, driver_name, layer_creation_options, format_option):
        self.suffix = suffix
        self.driver_name = driver_name
        self.layer_creation_options = layer_creation_options
        self.format_option = format_option


EXPORT_TYPE_MAPPING = {
    "geojson": ExportTypeInfo("geojson", "GeoJSON", [], "GDAL"),
    "shp": ExportTypeInfo("shp", "ESRI Shapefile", [], "GDAL"),
    "gpkg": ExportTypeInfo("gpkg", "GPKG", [], "GDAL"),
    "sqlite": ExportTypeInfo("sqlite", "SQLite", [], "GDAL"),
    "fgb": ExportTypeInfo("fgb", "FlatGeobuf", ["VERIFY_BUFFERS=NO"], "GDAL"),
    "mvt": ExportTypeInfo("mvt", "MVT", [], "GDAL"),
    "kml": ExportTypeInfo("kml", "KML", [], "GDAL"),
    "gpx": ExportTypeInfo("gpx", "GPX", [], "GDAL"),
    "parquet": ExportTypeInfo("parquet", "PARQUET", [], "PARQUET"),
}


class DatasetConfig(BaseModel):
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
    dataset_locations: List[str] = Field(
        default=None,
        description="Valid dataset locations iso3",
        example="['npl']",
    )

    @validator("update_frequency")
    def validate_frequency(cls, value):
        if value.strip() not in ALLOWED_HDX_UPDATE_FREQUENCIES:
            raise ValueError(
                f"Invalid update frequency , Should be within {ALLOWED_HDX_UPDATE_FREQUENCIES}"
            )
        return value.strip()


class DynamicCategoriesModel(BaseModel):
    iso3: Optional[str] = Field(
        default=None,
        description="ISO3 Country Code",
        min_length=3,
        max_length=3,
        example="USA",
    )
    dataset: Optional[DatasetConfig] = Field(
        default=None, description="Dataset Configurations for HDX Upload"
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
    geometry: Optional[Union[Polygon, MultiPolygon]] = Field(
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
            dataset = values.get("dataset").dict()
            if dataset is None:
                raise ValueError("Dataset config should be supplied for custom polygon")

            for item in dataset.keys():
                if dataset.get(item) is None:
                    raise ValueError(f"Missing, Dataset config : {item}")
        return value


@router.post("/submit/")
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def process_data(
    request: Request,
    params: DynamicCategoriesModel = Body(
        ...,
        description="Input parameters including ISO3 country code and dynamic categories.",
        openapi_examples={
            "normal_iso": {
                "summary": "Example: Road extraction using iso3",
                "description": "Query to extract road in Nepal",
                "value": {
                    "iso3": "NPL",
                    "categories": [
                        {
                            "Roads": {
                                "hdx": {
                                    "tags": ["roads", "transportation", "geodata"],
                                    "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                                },
                                "types": ["lines"],
                                "select": ["name", "highway"],
                                "where": "tags['highway'] IS NOT NULL",
                                "formats": ["geojson"],
                            }
                        }
                    ],
                },
            },
            "normal_iso_multiple_format": {
                "summary": "Example: Road extraction using iso3 Multiple format",
                "description": "Query to extract road in Nepal Multiple format",
                "value": {
                    "iso3": "NPL",
                    "categories": [
                        {
                            "Roads": {
                                "hdx": {
                                    "tags": ["roads", "transportation", "geodata"],
                                    "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                                },
                                "types": ["lines"],
                                "select": ["name", "highway"],
                                "where": "tags['highway'] IS NOT NULL",
                                "formats": ["geojson", "gpkg", "kml", "shp"],
                            }
                        }
                    ],
                },
            },
            "normal_polygon": {
                "summary": "Example: Road extraction set using custom polygon",
                "description": "Query to extract road in Pokhara, Nepal",
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
                    },
                    "dataset": {
                        "subnational": True,
                        "dataset_title": "Pokhara",
                        "dataset_prefix": "hotosm_pkr",
                        "dataset_locations": ["npl"],
                    },
                    "categories": [
                        {
                            "Roads": {
                                "hdx": {
                                    "tags": ["roads", "transportation", "geodata"],
                                    "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                                },
                                "types": ["lines"],
                                "select": ["name", "highway"],
                                "where": "tags['highway'] IS NOT NULL",
                                "formats": ["geojson"],
                            }
                        }
                    ],
                },
            },
            "fullset": {
                "summary": "Full HDX Dataset default",
                "description": "Full yaml conversion for dataset with iso3 example",
                "value": {
                    "iso3": "NPL",
                    "categories": [
                        {
                            "Buildings": {
                                "hdx": {
                                    "tags": [
                                        "facilities-infrastructure",
                                        "geodata",
                                    ],
                                    "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                                },
                                "types": ["polygons"],
                                "select": [
                                    "name",
                                    "building",
                                    "building:levels",
                                    "building:materials",
                                    "addr:full",
                                    "addr:housenumber",
                                    "addr:street",
                                    "addr:city",
                                    "office",
                                    "source",
                                ],
                                "where": "tags['building'] IS NOT NULL",
                                "formats": ["geojson"],
                            }
                        },
                        {
                            "Roads": {
                                "hdx": {
                                    "tags": ["transportation", "geodata"],
                                    "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                                },
                                "types": ["lines"],
                                "select": [
                                    "name",
                                    "highway",
                                    "surface",
                                    "smoothness",
                                    "width",
                                    "lanes",
                                    "oneway",
                                    "bridge",
                                    "layer",
                                    "source",
                                ],
                                "where": "tags['highway'] IS NOT NULL",
                                "formats": ["geojson"],
                            }
                        },
                        {
                            "Waterways": {
                                "hdx": {
                                    "tags": ["hydrology", "geodata"],
                                    "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                                },
                                "types": ["lines", "polygons"],
                                "select": [
                                    "name",
                                    "waterway",
                                    "covered",
                                    "width",
                                    "depth",
                                    "layer",
                                    "blockage",
                                    "tunnel",
                                    "natural",
                                    "water",
                                    "source",
                                ],
                                "where": "tags['waterway'] IS NOT NULL OR tags['water'] IS NOT NULL OR tags['natural'] IN ('water','wetland','bay')",
                                "formats": ["geojson"],
                            }
                        },
                        {
                            "Points of Interest": {
                                "hdx": {
                                    "tags": [
                                        "facilities-infrastructure",
                                        "points-of-interest-poi",
                                        "geodata",
                                    ],
                                    "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                                },
                                "types": ["points", "polygons"],
                                "select": [
                                    "name",
                                    "amenity",
                                    "man_made",
                                    "shop",
                                    "tourism",
                                    "opening_hours",
                                    "beds",
                                    "rooms",
                                    "addr:full",
                                    "addr:housenumber",
                                    "addr:street",
                                    "addr:city",
                                    "source",
                                ],
                                "where": "tags['amenity'] IS NOT NULL OR tags['man_made'] IS NOT NULL OR tags['shop'] IS NOT NULL OR tags['tourism'] IS NOT NULL",
                                "formats": ["geojson"],
                            }
                        },
                        {
                            "Airports": {
                                "hdx": {
                                    "tags": [
                                        "aviation",
                                        "facilities-infrastructure",
                                        "geodata",
                                    ],
                                    "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                                },
                                "types": ["points", "lines", "polygons"],
                                "select": [
                                    "name",
                                    "aeroway",
                                    "building",
                                    "emergency",
                                    "emergency:helipad",
                                    "operator:type",
                                    "capacity:persons",
                                    "addr:full",
                                    "addr:city",
                                    "source",
                                ],
                                "where": "tags['aeroway'] IS NOT NULL OR tags['building'] = 'aerodrome' OR tags['emergency:helipad'] IS NOT NULL OR tags['emergency'] = 'landing_site'",
                                "formats": ["geojson"],
                            }
                        },
                        {
                            "Sea Ports": {
                                "hdx": {
                                    "tags": [
                                        "facilities-infrastructure",
                                        "geodata",
                                    ],
                                    "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                                },
                                "types": ["points", "lines", "polygons"],
                                "select": [
                                    "name",
                                    "amenity",
                                    "building",
                                    "port",
                                    "operator:type",
                                    "addr:full",
                                    "addr:city",
                                    "source",
                                ],
                                "where": "tags['amenity'] = 'ferry_terminal' OR tags['building'] = 'ferry_terminal' OR tags['port'] IS NOT NULL",
                                "formats": ["geojson"],
                            }
                        },
                        {
                            "Education Facilities": {
                                "hdx": {
                                    "tags": [
                                        "education-facilities-schools",
                                        "geodata",
                                    ],
                                    "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                                },
                                "types": ["points", "polygons"],
                                "select": [
                                    "name",
                                    "amenity",
                                    "building",
                                    "operator:type",
                                    "capacity:persons",
                                    "addr:full",
                                    "addr:city",
                                    "source",
                                ],
                                "where": "tags['amenity'] IN ('kindergarten', 'school', 'college', 'university') OR building IN ('kindergarten', 'school', 'college', 'university')",
                                "formats": ["geojson"],
                            }
                        },
                        {
                            "Health Facilities": {
                                "hdx": {
                                    "tags": ["geodata"],
                                    "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                                },
                                "types": ["points", "polygons"],
                                "select": [
                                    "name",
                                    "amenity",
                                    "building",
                                    "healthcare",
                                    "healthcare:speciality",
                                    "operator:type",
                                    "capacity:persons",
                                    "addr:full",
                                    "addr:city",
                                    "source",
                                ],
                                "where": "tags['healthcare'] IS NOT NULL OR tags['amenity'] IN ('doctors', 'dentist', 'clinic', 'hospital', 'pharmacy')",
                                "formats": ["geojson"],
                            }
                        },
                        {
                            "Populated Places": {
                                "hdx": {
                                    "tags": [
                                        "populated-places-settlements",
                                        "geodata",
                                    ],
                                    "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                                },
                                "types": ["points"],
                                "select": [
                                    "name",
                                    "place",
                                    "population",
                                    "is_in",
                                    "source",
                                ],
                                "where": "tags['place'] IN ('isolated_dwelling', 'town', 'village', 'hamlet', 'city')",
                                "formats": ["geojson"],
                            }
                        },
                        {
                            "Financial Services": {
                                "hdx": {
                                    "tags": ["economics", "geodata"],
                                    "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                                },
                                "types": ["points", "polygons"],
                                "select": [
                                    "name",
                                    "amenity",
                                    "operator",
                                    "network",
                                    "addr:full",
                                    "addr:city",
                                    "source",
                                ],
                                "where": "tags['amenity'] IN ('mobile_money_agent','bureau_de_change','bank','microfinance','atm','sacco','money_transfer','post_office')",
                                "formats": ["geojson"],
                            }
                        },
                        {
                            "Railways": {
                                "hdx": {
                                    "tags": [
                                        "facilities-infrastructure",
                                        "railways",
                                        "transportation",
                                        "geodata",
                                    ],
                                    "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                                },
                                "types": ["lines"],
                                "select": [
                                    "name",
                                    "railway",
                                    "ele",
                                    "operator:type",
                                    "layer",
                                    "addr:full",
                                    "addr:city",
                                    "source",
                                ],
                                "where": "tags['railway'] IN ('rail','station')",
                                "formats": ["geojson"],
                            }
                        },
                    ],
                },
            },
        },
    ),
):
    """
    Process data based on dynamic categories.

    Args:
        request: FastAPI Request object.
        params (DynamicCategoriesModel): Input parameters including ISO3 country code and dynamic categories.

    Returns:
        dict: Result message.
    """
    if not params.dataset:
        params.dataset = DatasetConfig()
    hdx_set = HDX(params).process_hdx_tags()
    return {"message": "Data processed successfully"}
