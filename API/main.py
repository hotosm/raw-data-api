# Copyright (C) 2021 Humanitarian OpenStreetmap Team

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Humanitarian OpenStreetmap Team
# 1100 13th Street NW Suite 800 Washington, D.C. 20005
# <info@hotosm.org>

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
from src.galaxy import config

from .countries.routers import router as countries_router
from .changesets.routers import router as changesets_router
from .data.routers import router as data_router
from .auth.routers import router as auth_router
from .mapathon import router as mapathon_router
from .osm_users import router as osm_users_router
from .data_quality import router as data_quality_router
from .trainings import router as training_router
from .organization import router as organization_router
from .tasking_manager import router as tm_router
from .raw_data import router as raw_data_router
from fastapi import  Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import time
import logging
from src.galaxy.db_session import database_instance
from src.galaxy.config import use_connection_pooling


if config.get("SENTRY","url", fallback=None): # only use sentry if it is specified in config blocks
    sentry_sdk.init(
        config.get("SENTRY", "url"),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=config.get("SENTRY", "rate")
    )

# This is used for local setup for auth login
# import os
# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] ='1'

app = FastAPI()

app.mount("/exports", StaticFiles(directory="exports"), name="exports")

# @app.exception_handler(ValueError)
# async def value_error_exception_handler(request: Request, exc: ValueError):
#     return JSONResponse(
#         status_code=400,
#         content={"Error": str(exc)},
#     )


origins = ["*"]

@app.middleware("http")
async def add_process_time_header(request, call_next):
    """Times request and knows response time and pass it to header in every request

    Args:
        request (_type_): _description_
        call_next (_type_): _description_

    Returns:
        header with process time
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(f'{process_time:0.4f} sec')
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    """Fires up 5 threads on Postgresql with threading pooling before starting the API

    Raises:
        e: if connection is rejected to database
    """
    try:
        if use_connection_pooling:
            database_instance.connect()
    except Exception as e:
        logging.error(e)
        raise e

@app.on_event("shutdown")
async def on_shutdown():
    """Closing all the threads connection from pooling before shuting down the api 
    """
    if use_connection_pooling:
        logging.debug("Shutting down connection pool")
        await database_instance.close_all_connection_pool()


app.include_router(countries_router)
app.include_router(changesets_router)
app.include_router(auth_router)
app.include_router(mapathon_router)
app.include_router(data_router)
app.include_router(osm_users_router)
app.include_router(data_quality_router)
app.include_router(training_router)
app.include_router(organization_router)
app.include_router(tm_router)
app.include_router(raw_data_router)



