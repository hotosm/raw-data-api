
from fastapi import Request, APIRouter, Depends
from . import AuthUser, login_required , osm_auth
import json

router = APIRouter(prefix="/auth")


@router.get("/login/")
def login_url(request: Request):
    """Generate Login URL for authentication using OAuth2 Application registered with OpenStreetMap.
    Click on the download url returned to get access_token.

    Parameters: None

    Returns:
    - login_url (string) - URL to authorize user to the application via. Openstreetmap
        OAuth2 with client_id, redirect_uri, and permission scope as query_string parameters
    """
    login_url=osm_auth.login()
    return json.loads(login_url)


@router.get("/callback/")
def callback(request: Request):
    """Performs token exchange between OpenStreetMap and Export tool API

    Core will use Oauth secret key from configuration while deserializing token,
    provides access token that can be used for authorized endpoints.

    Parameters: None

    Returns:
    - access_token (string)
    """
    access_token=osm_auth.callback(str(request.url))

    return json.loads(access_token)


@router.get("/me/", response_model=AuthUser)
def my_data(user_data: AuthUser = Depends(login_required)):
    """Read the access token and provide  user details from OSM user's API endpoint,
    also integrated with underpass .

    Parameters:None

    Returns: user_data
    """
    return user_data
