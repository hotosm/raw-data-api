# Standard library imports
from typing import Dict, List

# Third party imports
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi_versioning import version

# Reader imports
from src.app import Cron
from src.config import LIMITER as limiter
from src.config import RATE_LIMIT_PER_MIN

from .auth import AuthUser, admin_required, staff_required

# from src.validation.models import DynamicCategoriesModel


router = APIRouter(prefix="/cron", tags=["Cron"])


@router.post("/", response_model=dict)
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def create_cron(
    request: Request, cron_data: dict, user_data: AuthUser = Depends(staff_required)
):
    """
    Create a new Cron entry.

    Args:
        request (Request): The request object.
        cron_data (dict): Data for creating the cron entry.
        user_data (AuthUser): User authentication data.

    Returns:
        dict: Result of the cron creation process.
    """
    cron_instance = Cron()
    return cron_instance.create_cron(cron_data)


@router.get("/", response_model=List[dict])
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def read_cron_list(
    request: Request,
    skip: int = 0,
    limit: int = 10,
):
    """
    Retrieve a list of Cron entries based on provided filters.

    Args:
        request (Request): The request object.
        skip (int): Number of entries to skip.
        limit (int): Maximum number of entries to retrieve.

    Returns:
        List[dict]: List of Cron entries.
    """
    cron_instance = Cron()
    filters = {}
    for key, values in request.query_params.items():
        if key not in ["skip", "limit"]:
            if key in ["iso3", "id", "queue", "meta", "cron_upload", "cid"]:
                filters[f"{key} = %s"] = values
                continue
            filters[f"dataset->>'{key}' = %s"] = values
    try:
        cron_list = cron_instance.get_cron_list_with_filters(skip, limit, filters)
    except Exception as ex:
        raise HTTPException(status_code=422, detail="Couldn't process query")
    return cron_list


@router.get("/search/", response_model=List[dict])
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def search_cron(
    request: Request,
    dataset_title: str = Query(
        ..., description="The title of the dataset to search for."
    ),
    skip: int = Query(0, description="Number of entries to skip."),
    limit: int = Query(10, description="Maximum number of entries to retrieve."),
):
    """
    Search for Cron entries by dataset title.

    Args:
        request (Request): The request object.
        dataset_title (str): The title of the dataset to search for.
        skip (int): Number of entries to skip.
        limit (int): Maximum number of entries to retrieve.

    Returns:
        List[dict]: List of Cron entries matching the dataset title.
    """
    cron_instance = Cron()
    cron_list = cron_instance.search_cron_by_dataset_title(dataset_title, skip, limit)
    return cron_list


@router.get("/{cron_id}", response_model=dict)
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def read_cron(request: Request, cron_id: int):
    """
    Retrieve a specific cron entry by its ID.

    Args:
        request (Request): The request object.
        cron_id (int): ID of the cron entry to retrieve.

    Returns:
        dict: Details of the requested cron entry.

    Raises:
        HTTPException: If the cron entry is not found.
    """
    cron_instance = Cron()
    cron = cron_instance.get_cron_by_id(cron_id)
    if cron:
        return cron
    raise HTTPException(status_code=404, detail="cron not found")


@router.put("/{cron_id}", response_model=dict)
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def update_cron(
    request: Request,
    cron_id: int,
    cron_data: dict,
    user_data: AuthUser = Depends(staff_required),
):
    """
    Update an existing cron entry.

    Args:
        request (Request): The request object.
        cron_id (int): ID of the cron entry to update.
        cron_data (dict): Data for updating the cron entry.
        user_data (AuthUser): User authentication data.

    Returns:
        dict: Result of the cron update process.

    Raises:
        HTTPException: If the cron entry is not found.
    """
    cron_instance = Cron()
    existing_cron = cron_instance.get_cron_by_id(cron_id)
    if not existing_cron:
        raise HTTPException(status_code=404, detail="cron not found")
    cron_instance_update = Cron()
    return cron_instance_update.update_cron(cron_id, cron_data)


@router.patch("/{cron_id}", response_model=Dict)
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def patch_cron(
    request: Request,
    cron_id: int,
    cron_data: Dict,
    user_data: AuthUser = Depends(staff_required),
):
    """
    Partially update an existing cron entry.

    Args:
        request (Request): The request object.
        cron_id (int): ID of the cron entry to update.
        cron_data (Dict): Data for partially updating the cron entry.
        user_data (AuthUser): User authentication data.

    Returns:
        Dict: Result of the cron update process.

    Raises:
        HTTPException: If the cron entry is not found.
    """
    cron_instance = Cron()
    existing_cron = cron_instance.get_cron_by_id(cron_id)
    if not existing_cron:
        raise HTTPException(status_code=404, detail="cron not found")
    patch_instance = Cron()
    return patch_instance.patch_cron(cron_id, cron_data)


@router.delete("/{cron_id}", response_model=dict)
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def delete_cron(
    request: Request, cron_id: int, user_data: AuthUser = Depends(admin_required)
):
    """
    Delete an existing cron entry.

    Args:
        request (Request): The request object.
        cron_id (int): ID of the cron entry to delete.
        user_data (AuthUser): User authentication data.

    Returns:
        dict: Result of the cron deletion process.

    Raises:
        HTTPException: If the cron entry is not found.
    """
    cron_instance = Cron()
    existing_cron = cron_instance.get_cron_by_id(cron_id)
    if not existing_cron:
        raise HTTPException(status_code=404, detail="cron not found")

    return cron_instance.delete_cron(cron_id)
