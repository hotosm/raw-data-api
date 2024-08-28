from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Path
from fastapi_versioning import version

from src.app import HDX
from src.config import LIMITER as limiter
from src.config import RATE_LIMIT_PER_MIN

from .auth import AuthUser, admin_required, staff_required

from src.validation.models import ErrorMessage, common_responses


router = APIRouter(prefix="/hdx", tags=["HDX"])


@router.post(
    "",
    response_model=dict,
    responses={
        "200": {"content": {"application/json": {"example": {"create": True}}}},
        **common_responses,
    },
)
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def create_hdx(
    request: Request, hdx_data: dict, user_data: AuthUser = Depends(staff_required)
):
    """
    Create a new HDX entry.

    Args:
        request (Request): The request object.\n
        hdx_data (dict): Data for creating the HDX entry.\n
        user_data (AuthUser): User authentication data.

    Returns:
        dict: Result of the HDX creation process.
    """
    hdx_instance = HDX()
    return hdx_instance.create_hdx(hdx_data)


@router.get("", response_model=List[dict], responses={"500": {"model": ErrorMessage}})
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def read_hdx_list(
    request: Request,
    skip: int = Query(0, description="Number of entries to skip."),
    limit: int = Query(10, description="Maximum number of entries to retrieve."),
):
    """
    Retrieve a list of HDX entries based on provided filters.

    Args:
        request (Request): The request object.
        skip (int): Number of entries to skip.
        limit (int): Maximum number of entries to retrieve.

    Returns:
        List[dict]: List of HDX entries.
    """
    hdx_instance = HDX()
    filters = {}
    for key, values in request.query_params.items():
        if key not in ["skip", "limit"]:
            if key in ["iso3", "id", "queue", "meta", "hdx_upload", "cid"]:
                filters[f"{key} = %s"] = values
                continue
            filters[f"dataset->>'{key}' = %s"] = values
    try:
        hdx_list = hdx_instance.get_hdx_list_with_filters(skip, limit, filters)
    except Exception:
        raise HTTPException(status_code=422, detail=[{"msg": "Couldn't process query"}])
    return hdx_list


@router.get(
    "/search",
    response_model=List[dict],
    responses={"404": {"model": ErrorMessage}, "500": {"model": ErrorMessage}},
)
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def search_hdx(
    request: Request,
    dataset_title: str = Query(
        ..., description="The title of the dataset to search for."
    ),
    skip: int = Query(0, description="Number of entries to skip."),
    limit: int = Query(10, description="Maximum number of entries to retrieve."),
):
    """
    Search for HDX entries by dataset title.

    Args:
        request (Request): The request object.
        dataset_title (str): The title of the dataset to search for.
        skip (int): Number of entries to skip.
        limit (int): Maximum number of entries to retrieve.

    Returns:
        List[dict]: List of HDX entries matching the dataset title.
    """
    hdx_instance = HDX()
    hdx_list = hdx_instance.search_hdx_by_dataset_title(dataset_title, skip, limit)
    return hdx_list


@router.get(
    "/{hdx_id}",
    response_model=dict,
    responses={"404": {"model": ErrorMessage}, "500": {"model": ErrorMessage}},
)
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def read_hdx(
    request: Request, hdx_id: int = Path(description="ID of the HDX entry to retrieve")
):
    """
    Retrieve a specific HDX entry by its ID.

    Args:
        request (Request): The request object.
        hdx_id (int): ID of the HDX entry to retrieve.

    Returns:
        dict: Details of the requested HDX entry.

    Raises:
        HTTPException 404: If the HDX entry is not found.
    """
    hdx_instance = HDX()
    hdx = hdx_instance.get_hdx_by_id(hdx_id)
    if hdx:
        return hdx
    raise HTTPException(status_code=404, detail=[{"msg": "HDX not found"}])


@router.put(
    "/{hdx_id}",
    response_model=dict,
    responses={**common_responses, "404": {"model": ErrorMessage}},
)
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def update_hdx(
    request: Request,
    hdx_data: dict,
    hdx_id: int = Path(description="ID of the HDX entry to update"),
    user_data: AuthUser = Depends(staff_required),
):
    """
    Update an existing HDX entry.

    Args:
        request (Request): The request object.\n
        hdx_id (int): ID of the HDX entry to update.\n
        hdx_data (dict): Data for updating the HDX entry.\n
        user_data (AuthUser): User authentication data.

    Returns:
        dict: Result of the HDX update process.

    Raises:
        HTTPException 404: If the HDX entry is not found.
    """
    hdx_instance = HDX()
    existing_hdx = hdx_instance.get_hdx_by_id(hdx_id)
    if not existing_hdx:
        raise HTTPException(status_code=404, detail=[{"msg": "HDX not found"}])
    hdx_instance_update = HDX()
    return hdx_instance_update.update_hdx(hdx_id, hdx_data)


@router.patch(
    "/{hdx_id}",
    response_model=Dict,
    responses={**common_responses, "404": {"model": ErrorMessage}},
)
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def patch_hdx(
    request: Request,
    hdx_data: Dict,
    hdx_id: int = Path(description="ID of the HDX entry to update"),
    user_data: AuthUser = Depends(staff_required),
):
    """
    Partially update an existing HDX entry.

    Args:
        request (Request): The request object.\n
        hdx_id (int): ID of the HDX entry to update.\n
        hdx_data (Dict): Data for partially updating the HDX entry.\n
        user_data (AuthUser): User authentication data.

    Returns:
        Dict: Result of the HDX update process.

    Raises:
        HTTPException 404: If the HDX entry is not found.
    """
    hdx_instance = HDX()
    existing_hdx = hdx_instance.get_hdx_by_id(hdx_id)
    if not existing_hdx:
        raise HTTPException(status_code=404, detail=[{"msg": "HDX not found"}])
    patch_instance = HDX()
    return patch_instance.patch_hdx(hdx_id, hdx_data)


@router.delete(
    "/{hdx_id}",
    response_model=dict,
    responses={**common_responses, "404": {"model": ErrorMessage}},
)
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def delete_hdx(
    request: Request,
    hdx_id: int = Path(description="ID of the HDX entry to delete"),
    user_data: AuthUser = Depends(admin_required),
):
    """
    Delete an existing HDX entry.

    Args:
        request (Request): The request object.\n
        hdx_id (int): ID of the HDX entry to delete.\n
        user_data (AuthUser): User authentication data.

    Returns:
        dict: Result of the HDX deletion process.

    Raises:
        HTTPException 404: If the HDX entry is not found.
    """
    hdx_instance = HDX()
    existing_hdx = hdx_instance.get_hdx_by_id(hdx_id)
    if not existing_hdx:
        raise HTTPException(status_code=404, detail=[{"msg": "HDX not found"}])

    return hdx_instance.delete_hdx(hdx_id)
