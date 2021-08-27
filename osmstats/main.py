from fastapi import FastAPI

from .countries.routers import router as countries_router
from .changesets.routers import router as changesets_router
from .data.routers import router as data_router


app = FastAPI()

app.include_router(countries_router)
app.include_router(changesets_router)
app.include_router(data_router)
