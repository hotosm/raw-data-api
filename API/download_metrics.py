# Standard library imports
from datetime import date
from typing import Any, Dict, List, Optional

# Third party imports
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_versioning import version
from pydantic import BaseModel

# Reader imports
from src.app import DownloadMetrics

from .auth import staff_required

router = APIRouter(prefix="/metrics", tags=["Metrics"])


class MetaDownloadItem(BaseModel):
    kwdate: str
    downloads_by_file: Dict[str, int]


class SummaryItem(BaseModel):
    kwdate: str
    total_downloads_count: Any
    total_uploads_count: Any
    total_unique_users: Any
    total_unique_downloads: Any
    total_interactions_count: Any
    total_upload_size: Any
    total_download_size: Any
    total_locations: Dict[str, int]
    total_referrers: Dict[str, int]


@router.get("/summary", response_model=List[SummaryItem])
@version(1)
def get_stats(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(
        None, description="End date (YYYY-MM-DD), defaults to today if omitted"
    ),
    group_by: str = Query(
        "day",
        description="Aggregation interval: day, month, quarter, or year",
        regex=r"^(day|month|quarter|year)$",
    ),
    folders: Optional[str] = Query(
        None,
        description="Comma-separated folder name(s) to filter metrics by",
        examples=["ISO3,HDX"],
    ),
    include_locations: bool = Query(
        False,
        description="Include location breakdown (disabled by default, adds performance cost)",
    ),
    include_referrers: bool = Query(
        False,
        description="Include referrer breakdown (disabled by default, adds performance cost)",
    ),
    _: bool = Depends(staff_required),
) -> List[SummaryItem]:
    """
    Retrieve aggregated download and upload summary statistics.

    **Query Parameters**
    - **start_date**: Required start of the date range (inclusive).
    - **end_date**: Optional end of the date range (inclusive); defaults to today if omitted.
    - **group_by**: Aggregation interval: 'day', 'month', 'quarter', or 'year'.
    - **folders**: Comma-separated list of folder keys to filter metrics by; if omitted, aggregates across all.
    - **include_locations**: If true, includes a JSON breakdown of locations per period (may impact performance).
    - **include_referrers**: If true, includes a JSON breakdown of referrers per period (may impact performance).

    **Response**
    A list of objects each containing:
    - **kwdate**: The truncated date period (ISO string).
    - **total_downloads_count, total_uploads_count, total_unique_users,** etc.
    - **total_locations** and **total_referrers** when requested.

    """
    if not end_date:
        end_date = date.today()
    if start_date > end_date:
        raise HTTPException(400, "start_date must be <= end_date")
    folder_list = (
        [f.strip() for f in folders.split(",") if f.strip()] if folders else None
    )
    metrics = DownloadMetrics()
    return metrics.get_summary_stats(
        start_date.isoformat(),
        end_date.isoformat(),
        group_by,
        folders=folder_list,
        include_locations=include_locations,
        include_referrers=include_referrers,
    )


@router.get("/meta-downloads", response_model=List[MetaDownloadItem])
@version(1)
def get_meta_downloads(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(
        None, description="End date (YYYY-MM-DD), defaults to today if omitted"
    ),
    group_by: str = Query(
        "day",
        description="Aggregation interval: day, month, quarter, or year",
        regex=r"^(day|month|quarter|year)$",
    ),
    key_prefixes: Optional[str] = Query(
        None,
        description="Comma-separated key prefixes to filter meta_downloads by",
        examples=["ISO3/IRN/,ISO3/NPL/"],
    ),
    limit: int = Query(
        100,
        ge=1,
        le=500,
        description="Maximum rows returned per request (enforced in SQL LIMIT)",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of rows to skip (enforced in SQL OFFSET)",
    ),
    _: bool = Depends(staff_required),
) -> List[MetaDownloadItem]:
    """
    Retrieve paginated metadata download counts per file key.

    **Query Parameters**
    - **start_date**: Required start of the date range (inclusive).
    - **end_date**: Optional end of the date range (inclusive); defaults to today if omitted.
    - **group_by**: Aggregation interval: 'day', 'month', 'quarter', or 'year'.
    - **key_prefixes**: Comma-separated list of key prefixes to filter the meta_downloads entries. This is different than folder option in the summmary , summary has clean folder args meanwhile this is meta hence the pattern needs to be there
    - **limit**: Page size for date buckets (default 100, max 500).
    - **offset**: Offset for pagination of date buckets.

    **Response**
    A list of objects each containing:
    - **kwdate**: The truncated date period (ISO string).
    - **downloads_by_file**: Mapping of each matching key to its download count.

    Pagination is enforced at the database level (via SQL LIMIT/OFFSET), ensuring efficient queries.
    """
    if not end_date:
        end_date = date.today()
    if start_date > end_date:
        raise HTTPException(400, "start_date must be <= end_date")
    prefixes = (
        [p.strip() for p in key_prefixes.split(",") if p.strip()]
        if key_prefixes
        else None
    )
    metrics = DownloadMetrics()
    return metrics.get_meta_downloads(
        start_date.isoformat(),
        end_date.isoformat(),
        group_by,
        key_prefixes=prefixes,
        limit=limit,
        offset=offset,
    )
