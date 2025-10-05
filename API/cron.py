# Standard library imports
from typing import Dict, List

# Third party imports
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi_versioning import version
from sqlalchemy.orm import Session

# Reader imports
from src.config import LIMITER as limiter
from src.config import RATE_LIMIT_PER_MIN
from src.db_session import get_db
from src.models import cron as cron_service

from .auth import AuthUser, admin_required, staff_required


router = APIRouter(prefix="/cron", tags=["Cron"])


@router.post("/", response_model=dict)
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def create_cron(
    request: Request,
    cron_data: dict,
    user_data: AuthUser = Depends(staff_required),
    db: Session = Depends(get_db)
):
    return cron_service.create_cron(cron_data, db)


@router.get("/", response_model=List[dict])
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def read_cron_list(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    filters = {}
    for key, values in request.query_params.items():
        if key not in ["skip", "limit"]:
            filters[key] = values
    
    return cron_service.get_cron_list(skip, limit, filters, db)


@router.get("/search/", response_model=List[dict])
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def search_cron(
    request: Request,
    dataset_title: str = Query(..., description="The title of the dataset to search for."),
    skip: int = Query(0, description="Number of entries to skip."),
    limit: int = Query(10, description="Maximum number of entries to retrieve."),
    db: Session = Depends(get_db)
):
    return cron_service.search_cron_by_dataset_title(dataset_title, skip, limit, db)


@router.get("/{cron_id}", response_model=dict)
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def read_cron(request: Request, cron_id: int, db: Session = Depends(get_db)):
    return cron_service.get_cron_by_id(cron_id, db)


@router.put("/{cron_id}", response_model=dict)
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def update_cron(
    request: Request,
    cron_id: int,
    cron_data: dict,
    user_data: AuthUser = Depends(staff_required),
    db: Session = Depends(get_db)
):
    return cron_service.update_cron(cron_id, cron_data, db)


@router.patch("/{cron_id}", response_model=Dict)
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def patch_cron(
    request: Request,
    cron_id: int,
    cron_data: Dict,
    user_data: AuthUser = Depends(staff_required),
    db: Session = Depends(get_db)
):
    return cron_service.patch_cron(cron_id, cron_data, db)


@router.delete("/{cron_id}", response_model=dict)
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def delete_cron(
    request: Request,
    cron_id: int,
    user_data: AuthUser = Depends(admin_required),
    db: Session = Depends(get_db)
):
    return cron_service.delete_cron(cron_id, db)
