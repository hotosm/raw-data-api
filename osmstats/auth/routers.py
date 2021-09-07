import base64
from fastapi import Request, APIRouter, Depends, Header, HTTPException, status

from os.path import join
from requests_oauthlib import OAuth2Session
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.security import OAuth2PasswordBearer
from itsdangerous.url_safe import URLSafeSerializer
from itsdangerous import BadSignature, SignatureExpired

from typing import Optional

from .. import config
from . import AuthUser, Login, Token

router = APIRouter(prefix="/auth")


@router.get("/login", response_model=Login)
def login_url(request: Request):
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

    user_data = {
        "id": data.get("id"),
        "username": data.get("display_name"),
        "img_url": data.get("img").get("href"),
    }

    token = serializer.dumps(user_data)
    access_token = base64.b64encode(bytes(token, "utf-8")).decode("utf-8")

    token = Token(access_token=access_token)

    return token


def login_required(access_token: str = Header(...)):
    deserializer = URLSafeSerializer(config.get("OAUTH", "secret_key"))

    try:
        decoded_token = base64.b64decode(access_token)
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not decode token",
        )

    try:
        user_data = deserializer.loads(decoded_token)
    except (SignatureExpired, BadSignature) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    return user_data


@router.get("/me", response_model=AuthUser)
def callback(user_data: AuthUser = Depends(login_required)):
    return user_data
