from pydantic import BaseModel


class AuthUser(BaseModel):
    id: int
    username: str
    img_url: str


class Login(BaseModel):
    url: str


class Token(BaseModel):
    access_token: str
