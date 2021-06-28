from fastapi import FastAPI
from configparser import ConfigParser

from .countries.routers import router as countries_router

app = FastAPI()
config = ConfigParser()
config.read("config.txt")

app.include_router(countries_router)
