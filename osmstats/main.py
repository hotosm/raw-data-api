from fastapi import FastAPI

from .countries.routers import router as countries_router

app = FastAPI()

app.include_router(countries_router)
