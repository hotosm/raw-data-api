from enum import Enum
from typing import Dict, List

from fastapi import APIRouter, Body, Query, Request
from fastapi_versioning import version
from pydantic import BaseModel, Field, validator

from src.app import HDX
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
        ...,
        description="Caveats for the HDX model.",
        example="OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
    )


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
        example=["gpkg", "fgb"],
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
    "gpkg": ExportTypeInfo("gpkg", "GeoPackage", [], "GDAL"),
    "sqlite": ExportTypeInfo("sqlite", "SQLite", [], "GDAL"),
    "fgb": ExportTypeInfo("fgb", "FlatGeobuf", ["VERIFY_BUFFERS=NO"], "GDAL"),
    "mvt": ExportTypeInfo("mvt", "MVT", [], "GDAL"),
    "kl": ExportTypeInfo("kml", "KML", [], "GDAL"),
    "gpx": ExportTypeInfo("gpx", "GPX", [], "GDAL"),
    "parquet": ExportTypeInfo("parquet", "PARQUET", [], "PARQUET"),
}


class DynamicCategoriesModel(BaseModel):
    iso3: str = Field(
        ...,
        description="ISO3 Country Code.",
        min_length=3,
        max_length=3,
        example="USA",
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
                    "formats": ["fgb"],
                }
            }
        ],
    )


@router.post("/submit/")
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def process_data(
    request: Request,
    params: DynamicCategoriesModel = Body(
        ...,
        description="Input parameters including ISO3 country code and dynamic categories.",
        openapi_examples={
            "normal": {
                "summary": "Example: Road extraction set",
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
                                "where": "tags['highway'][1] IS NOT NULL",
                                "formats": ["fgb"],
                            }
                        }
                    ],
                },
            },
            "fullset": {
                "summary": "Full HDX Dataset default",
                "description": "Full yaml conversion for dataset",
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
                                "where": "tags['building'][1] IS NOT NULL",
                                "formats": ["fgb"],
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
                                "where": "tags['highway'][1] IS NOT NULL",
                                "formats": ["fgb"],
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
                                "where": "tags['waterway'][1] IS NOT NULL OR tags['water'][1] IS NOT NULL OR tags['natural'][1] IN ('water','wetland','bay')",
                                "formats": ["fgb"],
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
                                "where": "tags['amenity'][1] IS NOT NULL OR tags['man_made'][1] IS NOT NULL OR tags['shop'][1] IS NOT NULL OR tags['tourism'][1] IS NOT NULL",
                                "formats": ["fgb"],
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
                                "where": "tags['aeroway'][1] IS NOT NULL OR tags['building'][1] = 'aerodrome' OR tags['emergency:helipad'][1] IS NOT NULL OR tags['emergency'][1] = 'landing_site'",
                                "formats": ["fgb"],
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
                                "where": "tags['amenity'][1] = 'ferry_terminal' OR tags['building'][1] = 'ferry_terminal' OR tags['port'][1] IS NOT NULL",
                                "formats": ["fgb"],
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
                                "where": "tags['amenity'][1] IN ('kindergarten', 'school', 'college', 'university') OR building IN ('kindergarten', 'school', 'college', 'university')",
                                "formats": ["fgb"],
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
                                "where": "tags['healthcare'][1] IS NOT NULL OR tags['amenity'][1] IN ('doctors', 'dentist', 'clinic', 'hospital', 'pharmacy')",
                                "formats": ["fgb"],
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
                                "where": "tags['place'][1] IN ('isolated_dwelling', 'town', 'village', 'hamlet', 'city')",
                                "formats": ["fgb"],
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
                                "where": "tags['amenity'][1] IN ('mobile_money_agent','bureau_de_change','bank','microfinance','atm','sacco','money_transfer','post_office')",
                                "formats": ["fgb"],
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
                                "where": "tags['railway'][1] IN ('rail','station')",
                                "formats": ["fgb"],
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
    hdx_set = HDX(params.iso3).process_hdx_tags(params)
    return {"message": "Data processed successfully"}
