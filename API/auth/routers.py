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
    """Login URL generates Login URL for Authorization , In Simple Meaning It will make request to osm Using Galaxy API Client ID and login redirect URL and gets Login URL using which user can enter their credentials and redirected to redirection URL. During Local setup You can register Galaxy as application in Osm oauth2 , get Client ID and redirect URL followed by sample config.txt , so that osm will provide correct login URL for you. This endpoint will act as bridge translating user request to osm for login URL ( as Galaxy as registered APP of OSM Oauth2) , The provided response will be osm login URL but encoded with galaxy API redirectURL since galaxy is registered on osm as oauth2 osm will know in which endpoint to redirect once login is successful with the token to desearilze : osm link will call /auth/callback"""
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
    """This endpoint will perform token exchange Between osm ~ Galaxy API,When osm makes callback. Core will use Oauth Secret Key from configuration while deserializing token , Provides access token that can be used on authorized endpoint"""
    # Perform token exchange.
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
    """This is the simple endpoint which will read the access token and provides the user details from osm user’s api endpoint , also now integrated with underpass : provides admin or non admin option for hot staff defined in table"""
    return user_data
