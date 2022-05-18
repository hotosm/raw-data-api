from fastapi import Request, APIRouter

from os.path import join
from requests_oauthlib import OAuth2Session
from fastapi.responses import RedirectResponse, FileResponse

from src.galaxy import config

router = APIRouter(prefix="/data")


@router.get("/download/{db_name}")
def login_url(db_name: str, request: Request):
    osm_url = config.get("OAUTH", "url")
    authorize_url = f"{osm_url}/oauth2/authorize/"
    scope = config.get("OAUTH", "scope").split(",")

    redirect_path = config.get("DUMP", "redirect_uri")
    redirect_uri = f"{redirect_path}/{db_name}"

    oauth = OAuth2Session(
        config.get("OAUTH", "client_id"),
        redirect_uri=redirect_uri,
        scope=scope,
    )

    login_url, _ = oauth.authorization_url(authorize_url)

    return RedirectResponse(login_url)


@router.get("/callback/{db_name}")
def callback(db_name: str, request: Request):
    # Perform token exchange.
    osm_url = config.get("OAUTH", "url")
    token_url = f"{osm_url}/oauth2/token"
    redirect_path = config.get("DUMP", "redirect_uri")
    redirect_uri = f"{redirect_path}/{db_name}"

    oauth = OAuth2Session(
        config.get("OAUTH", "client_id"),
        redirect_uri=redirect_uri,
        state=request.query_params.get("state"),
    )

    oauth.fetch_token(
        token_url,
        authorization_response=str(request.url),
        client_secret=config.get("OAUTH", "client_secret"),
    )

    file_name = config.get("DUMP", db_name)
    file_path = join(config.get("DUMP", "path"), file_name)

    return FileResponse(file_path, filename=file_name)
