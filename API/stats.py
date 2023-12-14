from fastapi import APIRouter, Request
from fastapi_versioning import version

from src.app import PolygonStats
from src.config import LIMITER as limiter
from src.config import POLYGON_STATISTICS_API_RATE_LIMIT
from src.validation.models import StatsRequestParams

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.post("/polygon/")
@limiter.limit(f"{POLYGON_STATISTICS_API_RATE_LIMIT}/minute")
@version(1)
async def get_polygon_stats(request: Request, params: StatsRequestParams):
    """Get statistics for the specified polygon.

    Args:
        request (Request): An HTTP request object.
        params (StatsRequestParams): Parameters for the statistics request, including the polygon geometry.

    Returns:
        dict: A dictionary containing statistics for the specified polygon.
    """
    generator = PolygonStats(params.geometry)

    return generator.get_summary_stats()
