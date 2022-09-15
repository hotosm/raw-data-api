import base64
from typing import Union

from pydantic import BaseModel
from itsdangerous.url_safe import URLSafeSerializer
from itsdangerous import BadSignature, SignatureExpired
from fastapi import Header, HTTPException, status

from src.galaxy import config
from src.galaxy.validation.models import UserRole

class AuthUser(BaseModel):
    id: int
    username: str
    img_url: Union[str, None]
    role: str


class Login(BaseModel):
    url: str


class Token(BaseModel):
    access_token: str


def deserialize_access_token(access_token: str):
    deserializer = URLSafeSerializer(config.get("OAUTH", "secret_key"))

    try:
        decoded_token = base64.b64decode(access_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not decode token",
        )

    try:
        user_data = deserializer.loads(decoded_token)
    except (SignatureExpired, BadSignature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    return user_data


def login_required(access_token: str = Header(...)):
    return deserialize_access_token(access_token)


def is_staff_member(access_token: str = Header(...)):
    user_data = deserialize_access_token(access_token)

    if UserRole[user_data["role"]] not in (UserRole.STAFF, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not staff member"
        )

    return user_data

