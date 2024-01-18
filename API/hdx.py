from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi_versioning import version

from src.app import HDX
from src.config import LIMITER as limiter
from src.config import RATE_LIMIT_PER_MIN

from .auth import AuthUser, admin_required, staff_required

# from src.validation.models import DynamicCategoriesModel


router = APIRouter(prefix="/hdx", tags=["HDX"])


@router.post("/", response_model=dict)
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def create_hdx(
    request: Request, hdx_data: dict, user_data: AuthUser = Depends(staff_required)
):
    hdx_instance = HDX()

    return hdx_instance.create_hdx(hdx_data)


@router.get("/", response_model=List[dict])
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def read_hdx_list(request: Request, skip: int = 0, limit: int = 10):
    hdx_instance = HDX()

    return hdx_instance.get_hdx_list(skip, limit)


@router.get("/{hdx_id}", response_model=dict)
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def read_hdx(request: Request, hdx_id: int):
    hdx_instance = HDX()

    hdx = hdx_instance.get_hdx_by_id(hdx_id)
    if hdx:
        return hdx
    raise HTTPException(status_code=404, detail="HDX not found")


@router.put("/{hdx_id}", response_model=dict)
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def update_hdx(
    request: Request,
    hdx_id: int,
    hdx_data: dict,
    user_data: AuthUser = Depends(staff_required),
):
    hdx_instance = HDX()

    existing_hdx = hdx_instance.get_hdx_by_id(hdx_id)
    if not existing_hdx:
        raise HTTPException(status_code=404, detail="HDX not found")

    return hdx_instance.update_hdx(hdx_id, hdx_data)


@router.delete("/{hdx_id}", response_model=dict)
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def delete_hdx(
    request: Request, hdx_id: int, user_data: AuthUser = Depends(admin_required)
):
    hdx_instance = HDX()

    existing_hdx = hdx_instance.get_hdx_by_id(hdx_id)
    if not existing_hdx:
        raise HTTPException(status_code=404, detail="HDX not found")

    return hdx_instance.delete_hdx(hdx_id)
