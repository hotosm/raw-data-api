from enum import Enum
from typing import Union

from fastapi import Depends, Header, HTTPException
from osm_login_python.core import Auth
from pydantic import BaseModel, Field

from src.app import Users
from src.config import get_oauth_credentials


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


def get_user_from_db(osm_id: int):
    auth = Users()
    user = auth.read_user(osm_id)
    return user


def get_osm_auth_user(access_token):
    try:
        user = AuthUser(**osm_auth.deserialize_access_token(access_token))
    except Exception as ex:
        raise HTTPException(
            status_code=403, detail=[{"msg": "OSM Authentication failed"}]
        )
    db_user = get_user_from_db(user.id)
    user.role = db_user["role"]
    return user


def login_required(access_token: str = Header(...)):
    return get_osm_auth_user(access_token)


def get_optional_user(access_token: str = Header(default=None)) -> AuthUser:
    if access_token:
        return get_osm_auth_user(access_token)
    else:
        # If no token provided, return a user with limited options or guest user
        return AuthUser(id=0, username="guest", img_url=None)


def admin_required(user: AuthUser = Depends(login_required)):
    db_user = get_user_from_db(user.id)
    if not db_user["role"] is UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="User is not an admin")
    return user


def staff_required(user: AuthUser = Depends(login_required)):
    db_user = get_user_from_db(user.id)

    # admin is staff too
    if not (
        db_user["role"] is UserRole.STAFF.value
        or db_user["role"] is UserRole.ADMIN.value
    ):
        raise HTTPException(status_code=403, detail="User is not a staff")
    return user
