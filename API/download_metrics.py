# Standard library imports
from datetime import datetime
from typing import Optional

# Third party imports
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_versioning import version

# Reader imports
from src.app import DownloadMetrics

from .auth import staff_required

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/summary")
@version(1)
def get_stats(
    start_date: str = Query(
        ...,
        description="Start date (YYYY-MM-DD)",
        regex=r"^\d{4}-\d{2}-\d{2}$",
        example="2023-04-01",
    ),
    end_date: str = Query(
        ...,
        description="End date (YYYY-MM-DD)",
        regex=r"^\d{4}-\d{2}-\d{2}$",
        example="2023-04-30",
    ),
    group_by: str = Query(
        "day",
        description="Group by: day, month, or quarter",
        regex=r"^(day|month|quarter|year)$",
    ),
    folder: Optional[str] = Query(
        None,
        description="Folder to filter metrics by",
        example="TM",
    ),
    _: bool = Depends(staff_required),
):
    """
    Retrieve download metrics summary statistics.

    - **start_date**: The start date for the metrics, in the format "YYYY-MM-DD".
    - **end_date**: The end date for the metrics, in the format "YYYY-MM-DD".
    - **group_by**: The time period to group the metrics by. Can be "day", "month", "quarter", or "year".

    The API requires admin authentication to access.
    """
    if group_by not in ["day", "month", "quarter", "year"]:
        raise HTTPException(
            status_code=400, detail={"error": "Invalid group_by parameter"}
        )

    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"error": "Invalid date format, expected YYYY-MM-DD"},
        )

    metrics = DownloadMetrics()
    return metrics.get_summary_stats(start_date, end_date, group_by, folder)
