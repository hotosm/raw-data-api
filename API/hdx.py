from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi_versioning import version

from src.config import LIMITER as limiter
from src.config import RATE_LIMIT_PER_MIN
from src.validation.models import DynamicCategoriesModel

from .api_worker import process_hdx_request
from .auth import AuthUser, UserRole, staff_required

router = APIRouter(prefix="/custom", tags=["Custom Exports"])


@router.post("/snapshot/")
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def process_custom_requests(
    request: Request,
    user: AuthUser = Depends(staff_required),
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
            "normal_iso_non_upload": {
                "summary": "Example: Road extraction using iso3 on raw data api only",
                "description": "Query to extract road in Nepal, without uploading to hdx",
                "value": {
                    "iso3": "NPL",
                    "hdx_upload": False,
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
            "normal_polygon_TM": {
                "summary": "Example: Tasking Manager Mapping type extraction for a Project",
                "description": "Example Query to extract building,roads,waterways and landuse in sample TM Project , Pokhara, Nepal",
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
                    "queue": "raw_default",
                    "dataset": {
                        "dataset_prefix": "hotosm_project_1",
                        "dataset_folder": "TM",
                        "dataset_title": "Tasking Manger Project 1",
                    },
                    "categories": [
                        {
                            "Buildings": {
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
                                "formats": ["geojson", "shp", "kml"],
                            },
                            "Roads": {
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
                                "formats": ["geojson", "shp", "kml"],
                            },
                            "Waterways": {
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
                                "formats": ["geojson", "shp", "kml"],
                            },
                            "Landuse": {
                                "types": ["points", "polygons"],
                                "select": ["name", "amenity", "landuse", "leisure"],
                                "where": "tags['landuse'] IS NOT NULL",
                                "formats": ["geojson", "shp", "kml"],
                            },
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
                                        "points of interest-poi",
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
                                        "education facilities-schools",
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
                                        "populated places-settlements",
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
            "fullset_multiple_formats": {
                "summary": "Full HDX Dataset default Multiple formats",
                "description": "Full yaml conversion for dataset with iso3 example with multiple formats",
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
                                "formats": ["geojson", "shp", "kml"],
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
                                "formats": ["geojson", "shp", "kml"],
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
                                "formats": ["geojson", "shp", "kml"],
                            }
                        },
                        {
                            "Points of Interest": {
                                "hdx": {
                                    "tags": [
                                        "facilities-infrastructure",
                                        "points of interest-poi",
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
                                "formats": ["geojson", "shp", "kml"],
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
                                "formats": ["geojson", "shp", "kml"],
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
                                "formats": ["geojson", "shp", "kml"],
                            }
                        },
                        {
                            "Education Facilities": {
                                "hdx": {
                                    "tags": [
                                        "education facilities-schools",
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
                                "formats": ["geojson", "shp", "kml"],
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
                                "formats": ["geojson", "shp", "kml"],
                            }
                        },
                        {
                            "Populated Places": {
                                "hdx": {
                                    "tags": [
                                        "populated places-settlements",
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
                                "formats": ["geojson", "shp", "kml"],
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
                                "formats": ["geojson", "shp", "kml"],
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
                                "formats": ["geojson", "shp", "kml"],
                            }
                        },
                    ],
                },
            },
        },
    ),
):
    """
    Process data based on dynamic categories, Fully flexible on filtering and select

    Args:
        request: FastAPI Request object.
        params (DynamicCategoriesModel): Input parameters including ISO3 country code and dynamic categories.

    Returns:
        dict: Result message.
    """
    queue_name = params.queue
    if params.queue != "raw_special" and user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=403,
            detail=[{"msg": "Insufficient Permission to choose queue"}],
        )
    task = process_hdx_request.apply_async(
        args=(params.model_dump(),), queue=queue_name, track_started=True
    )
    return JSONResponse({"task_id": task.id, "track_link": f"/tasks/status/{task.id}/"})
