import base64
from fastapi import Request, APIRouter, Depends

from itsdangerous.url_safe import URLSafeSerializer
from requests_oauthlib import OAuth2Session

from src.galaxy import config
from src.galaxy.app import Underpass
from . import AuthUser, Login, Token, login_required, is_staff_member

router = APIRouter(prefix="/auth")


@router.get("/login", response_model=Login)
def login_url(request: Request):
    """Generate Login URL for authentication using OAuth2 Application registered to OpenStreetMap

    Parameters: None

    Returns:
    - login_url (string) - URL to authorize user to the application via. Openstreetmap 
        OAuth2 with client_id, redirect_uri, and permission scope as query_string parameters  
    """
    osm_url = config.get("OAUTH", "url")
    authorize_url = f"{osm_url}/oauth2/authorize/"
    scope = config.get("OAUTH", "scope").split(",")

    oauth = OAuth2Session(
        config.get("OAUTH", "client_id"),
        redirect_uri=config.get("OAUTH", "login_redirect_uri"),
        scope=scope,
    )

    login_url, _ = oauth.authorization_url(authorize_url)

    return Login(url=login_url)


@router.get("/callback", response_model=Token)
def callback(request: Request):
    """Performs token exchange between OpenStreetMap and Galaxy API

    Core will use Oauth secret key from configuration while deserializing token, 
    provides access token that can be used on authorized endpoint

    Parameters: None 

    Returns:
    - access_token (string)
    """
    osm_url = config.get("OAUTH", "url")
    token_url = f"{osm_url}/oauth2/token"

    oauth = OAuth2Session(
        config.get("OAUTH", "client_id"),
        redirect_uri=config.get("OAUTH", "login_redirect_uri"),
        state=request.query_params.get("state"),
    )

    oauth.fetch_token(
        token_url,
        authorization_response=str(request.url),
        client_secret=config.get("OAUTH", "client_secret"),
    )

    api_url = f"{osm_url}/api/0.6/user/details.json"

    resp = oauth.get(api_url)

    if resp.status_code != 200:
        raise ValueError("Invalid response from OSM")

    data = resp.json().get("user")

    serializer = URLSafeSerializer(config.get("OAUTH", "secret_key"))

    user_id = data.get("id")
    user_role =Underpass().get_user_role(user_id)

    user_data = {
        "id": user_id,
        "username": data.get("display_name"),
        "img_url": data.get("img").get("href") if data.get("img") else None,
        "role": user_role.name,
    }

    token = serializer.dumps(user_data)
    access_token = base64.b64encode(bytes(token, "utf-8")).decode("utf-8")

    token = Token(access_token=access_token)

    return token


@router.get("/me", response_model=AuthUser)
def my_data(user_data: AuthUser = Depends(is_staff_member)):
    """Read the access token and provide  user details from OSM user's API endpoint,
    also integrated with underpass .

    Parameters:None

    Returns: user_data
    """
    return user_data
