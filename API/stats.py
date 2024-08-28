# Standard library imports
import json

# Third party imports
from area import area
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi_versioning import version
from .auth import AuthUser, UserRole, get_optional_user

# Reader imports
from src.app import PolygonStats
from src.config import LIMITER as limiter
from src.config import POLYGON_STATISTICS_API_RATE_LIMIT
from src.validation.models import StatsRequestParams, stats_response

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.post(
    "/polygon",
    responses={**stats_response},
)
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
    user: AuthUser = Depends(get_optional_user),
):
    """Get statistics for the specified polygon.

    Args:
        request (Request): An HTTP request object.
        params (StatsRequestParams): Parameters for the statistics request, including the polygon geometry.

    Returns:
        dict: A dictionary containing statistics for the specified polygon.
    """
    if not (user.role is UserRole.STAFF.value or user.role is UserRole.ADMIN.value):
        if params.geometry:
            area_m2 = area(json.loads(params.geometry.model_dump_json()))
            area_km2 = area_m2 * 1e-6
            limit = 10000
            if area_km2 > limit:
                raise HTTPException(
                    status_code=400,
                    detail=[
                        {
                            "msg": f"""Polygon Area {int(area_km2)} Sq.KM is higher than Threshold : {limit} Sq.KM"""
                        }
                    ],
                )
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
