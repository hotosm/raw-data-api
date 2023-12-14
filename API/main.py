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
import time

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_versioning import VersionedFastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.config import (
    ENABLE_POLYGON_STATISTICS_ENDPOINTS,
    EXPORT_PATH,
    LIMITER,
    LOG_LEVEL,
    SENTRY_DSN,
    SENTRY_RATE,
    USE_CONNECTION_POOLING,
    USE_S3_TO_UPLOAD,
)
from src.config import logger as logging
from src.db_session import database_instance

from .auth.routers import router as auth_router
from .raw_data import router as raw_data_router
from .tasks import router as tasks_router

if ENABLE_POLYGON_STATISTICS_ENDPOINTS:
    from .stats import router as stats_router

# only use sentry if it is specified in config blocks
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=SENTRY_RATE,
    )

if LOG_LEVEL.lower() == "debug":
    # This is used for local setup for auth login
    import os

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

app = FastAPI(title="Raw Data API ")
app.include_router(auth_router)
app.include_router(raw_data_router)
app.include_router(tasks_router)
if ENABLE_POLYGON_STATISTICS_ENDPOINTS:
    app.include_router(stats_router)

app.openapi = {
    "info": {
        "title": "Raw Data API",
        "version": "1.0",
    },
    "security": [{"OAuth2PasswordBearer": []}],
}

app = VersionedFastAPI(
    app, enable_latest=False, version_format="{major}", prefix_format="/v{major}"
)

if USE_S3_TO_UPLOAD is False:
    # only mount the disk if config is set to disk
    app.mount("/exports", StaticFiles(directory=EXPORT_PATH), name="exports")

app.state.limiter = LIMITER
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    response.headers["X-Process-Time"] = str(f"{process_time:0.4f} sec")
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
    """Fires up 3 idle conenction with threaded connection pooling before starting the API

    Raises:
        e: if connection is rejected to database
    """
    try:
        if USE_CONNECTION_POOLING:
            database_instance.connect()
    except Exception as e:
        logging.error(e)
        raise e


@app.on_event("shutdown")
def on_shutdown():
    """Closing all the threads connection from pooling before shuting down the api"""
    if USE_CONNECTION_POOLING:
        logging.debug("Shutting down connection pool")
        database_instance.close_all_connection_pool()
