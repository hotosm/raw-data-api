from enum import Enum
from typing import Union

from fastapi import Depends, Header, HTTPException
from osm_login_python.core import Auth
from pydantic import BaseModel, Field

from src.config import ADMIN_IDS, get_oauth_credentials


class UserRole(Enum):
    ADMIN = 1
    STAFF = 2
    GUEST = 3


class AuthUser(BaseModel):
    id: int
    username: str
    img_url: Union[str, None]
    role: UserRole = Field(default=UserRole.GUEST.value)


osm_auth = Auth(*get_oauth_credentials())


def is_admin(osm_id: int):
    admin_ids = [int(admin_id) for admin_id in ADMIN_IDS]
    return osm_id in admin_ids


def login_required(access_token: str = Header(...)):
    user = AuthUser(**osm_auth.deserialize_access_token(access_token))
    if is_admin(user.id):
        user.role = UserRole.ADMIN
    return user


def get_optional_user(access_token: str = Header(default=None)) -> AuthUser:
    if access_token:
        user = AuthUser(**osm_auth.deserialize_access_token(access_token))
        if is_admin(user.id):
            user.role = UserRole.ADMIN
        return user
    else:
        # If no token provided, return a user with limited options or guest user
        return AuthUser(id=0, username="guest", img_url=None)


def admin_required(user: AuthUser = Depends(login_required)):
    if not is_admin(user.id):
        raise HTTPException(status_code=403, detail="User is not an admin")
    return user
