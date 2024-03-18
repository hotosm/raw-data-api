import json

from fastapi import APIRouter, Body, Request
from fastapi_versioning import version

from src.app import PolygonStats
from src.config import LIMITER as limiter
from src.config import POLYGON_STATISTICS_API_RATE_LIMIT
from src.validation.models import StatsRequestParams

router = APIRouter(prefix="/stats", tags=["Stats"])

@router.post("/polygon")
@limiter.limit(f"{POLYGON_STATISTICS_API_RATE_LIMIT}/minute")
@version(1)
async def get_polygon_stats(
    request: Request,
    params: StatsRequestParams = Body(
        ...,
        description="Get Summary and raw stats related to polygon",
        openapi_examples={
            "normal_polygon": {
                "summary": "Normal Example of requesting stats",
                "description": "Query to extract stats using Custom Polygon",
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
            "normal_iso": {
                "summary": "Query to extract stats using iso",
                "description": "Extract stats using iso3 only, For eg : for Nepal",
                "value": {"iso3": "npl"},
            },
        },
    ),
):
    """Get statistics for the specified polygon.

    Args:
        request (Request): An HTTP request object.
        params (StatsRequestParams): Parameters for the statistics request, including the polygon geometry.

    Returns:
        dict: A dictionary containing statistics for the specified polygon.
    """
    feature = None
    if params.geometry:
        feature = {
            "type": "Feature",
            "geometry": json.loads(params.geometry.model_dump_json()),
            "properties": {},
        }
    if params.iso3:
        params.iso3 = params.iso3.lower()
    generator = PolygonStats(feature, params.iso3)

    return generator.get_summary_stats()
