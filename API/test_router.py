from fastapi import APIRouter
from fastapi_versioning import  version

router = APIRouter(prefix="/test")

@router.get("/galaxy/")
@version(1,0)
def galaxy_says_v1():
    return "Hello"


@router.get("/galaxy/")
@version(2,0)
def galaxy_says_v2():
    return "Hi"
