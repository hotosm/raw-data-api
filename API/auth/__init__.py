from typing import Union

from fastapi import Header
from osm_login_python.core import Auth
from pydantic import BaseModel

from src.config import get_oauth_credentials


class AuthUser(BaseModel):
    id: int
    username: str
    img_url: Union[str, None]


osm_auth = Auth(*get_oauth_credentials())


def login_required(access_token: str = Header(...)):
    return osm_auth.deserialize_access_token(access_token)
