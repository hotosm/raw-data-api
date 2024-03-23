import json


from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from src.app import Users
from src.error_module import ErrorMessage, common_responses, login_responses

from . import AuthUser, admin_required, login_required, osm_auth, staff_required

router = APIRouter(prefix="/auth", tags=["Auth"])

class ErrorMessage(BaseModel):
    detail: str

responses = {
    200: {"model": ErrorMessage,
          "content": {"application/json": {"example": {"detail": "OK"}}}},
    400: {"model": ErrorMessage,
          "content": {"application/json": {"example": {"detail": "Bad Request"}}}},
    403: {"model": ErrorMessage,
          "content": {"application/json": {"example": {"detail": "Forbidden"}}}},
    408: {"model": ErrorMessage,
          "content": {"application/json": {"example": {"detail": "Request Timeout"}}}},
    422: {"model": ErrorMessage,
          "content": {"application/json": {"example": {"detail": "Validation Error"}}}},
    500: {"model": ErrorMessage,
          "content": {"application/json": {"example": {"detail": "Internal Server Error"}}}}
}


@router.get("/login", responses = {500: {"model": ErrorMessage},
                                   200: {"content": {"application/json": {"example": {"login_url": "OK"}}}}})
def login_url(request: Request):
    """Generate Login URL for authentication using OAuth2 Application registered with OpenStreetMap.
    Click on the download url returned to get access_token.

    Parameters: None

    Returns:
    - login_url (dict) - URL to authorize user to the application via. Openstreetmap
        OAuth2 with client_id, redirect_uri, and permission scope as query_string parameters
    """
    login_url = osm_auth.login()
    return login_url


@router.get("/callback", responses = {500: {"model": ErrorMessage}})
def callback(request: Request):
    """Performs token exchange between OpenStreetMap and Raw Data API

    Core will use Oauth secret key from configuration while deserializing token,
    provides access token that can be used for authorized endpoints.

    Parameters: None

    Returns:
    - access_token (string)
    """
    access_token = osm_auth.callback(str(request.url))
    return access_token


@router.get("/me", response_model=AuthUser, responses = {**responses})
def my_data(user_data: AuthUser = Depends(login_required)):
    """Read the access token and provide  user details from OSM user's API endpoint,
    also integrated with underpass .

    Parameters:None

    Returns: user_data
            User Role :
                ADMIN = 1
                STAFF = 2
                GUEST = 3
    """
    return user_data


class User(BaseModel):
    osm_id: int
    role: int


# Create user
@router.post("/users", response_model=dict, responses= {**responses})
async def create_user(params: User, user_data: AuthUser = Depends(admin_required)):
    """
    Creates a new user and returns the user's information.
    User Role :
        ADMIN = 1
        STAFF = 2
        GUEST = 3

    Args:
    - params (User): The user data including osm_id and role.

    Returns:
    - Dict[str, Any]: A dictionary containing the osm_id of the newly created user.

    Raises:
    - HTTPException 403: If the user has unauthorized access
    - HTTPException 500: If the access is denied due to internal server error
    """
    auth = Users()
    return auth.create_user(params.osm_id, params.role)


# Read user by osm_id
@router.get("/users{osm_id}", response_model=dict, responses= {**responses})
async def read_user(osm_id: int, user_data: AuthUser = Depends(staff_required)):
    """
    Retrieves user information based on the given osm_id.
    User Role :
        ADMIN = 1
        STAFF = 2
        GUEST = 3

    Args:
    - osm_id (int): The OSM ID of the user to retrieve.

    Returns:
    - Dict[str, Any]: A dictionary containing user information.

    Raises:
    - HTTPException 403: If the user has unauthorized access
    - HTTPException 500: If the access is denied due to internal server error
    """
    auth = Users()

    return auth.read_user(osm_id)


# Update user by osm_id
@router.put("/users{osm_id}", response_model=dict, responses = {**responses, 404: {"model": ErrorMessage}})
async def update_user(
    osm_id: int, update_data: User, user_data: AuthUser = Depends(admin_required)
):
    """
    Updates user information based on the given osm_id.
    User Role :
        ADMIN = 1
        STAFF = 2
        GUEST = 3
    Args:
    - osm_id (int): The OSM ID of the user to update.
    - update_data (User): The data to update for the user.

    Returns:
    - Dict[str, Any]: A dictionary containing the updated user information.

    Raises:
    - HTTPException 403: If the user has unauthorized access.
    - HTTPException 404: If the user cannot be found.
    - HTTPException 408: If the access is denied due to request timeout
    - HTTPException 500: If access is denied due to internal server error.

    """
    auth = Users()
    return auth.update_user(osm_id, update_data)


# Delete user by osm_id
@router.delete("/users{osm_id}", response_model=dict, responses = {**responses, 404: {"model": ErrorMessage}})
async def delete_user(osm_id: int, user_data: AuthUser = Depends(admin_required)):
    """
    Deletes a user based on the given osm_id.

    Args:
    - osm_id (int): The OSM ID of the user to delete.

    Returns:
    - Dict[str, Any]: A dictionary containing the deleted user information.

    Raises:
    - HTTPException 404: If the user with the given osm_id is not found.
    """
    auth = Users()
    return auth.delete_user(osm_id)


# Get all users
@router.get("/users", response_model=list, responses = {**responses})
async def read_users(
    skip: int = 0, limit: int = 10, user_data: AuthUser = Depends(staff_required)
):
    """
    Retrieves a list of users with optional pagination.

    Args:
    - skip (int): The number of users to skip (for pagination).
    - limit (int): The maximum number of users to retrieve (for pagination).

    Returns:
    - List[Dict[str, Any]]: A list of dictionaries containing user information.
    """
    auth = Users()
    return auth.read_users(skip, limit)
