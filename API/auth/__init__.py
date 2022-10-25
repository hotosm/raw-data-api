from typing import Union
from src.galaxy import config
from pydantic import BaseModel
from fastapi import Header
from osm_login_python.core import Auth


class AuthUser(BaseModel):
    id: int
    username: str
    img_url: Union[str, None]

osm_auth=Auth(osm_url=config.get("OAUTH", "url"), client_id=config.get("OAUTH", "client_id"),client_secret=config.get("OAUTH", "client_secret"), secret_key=config.get("OAUTH", "secret_key"), login_redirect_uri=config.get("OAUTH", "login_redirect_uri"), scope=config.get("OAUTH", "scope"))


def login_required(access_token: str = Header(...)):
    return osm_auth.deserialize_access_token(access_token)
