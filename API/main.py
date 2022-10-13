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
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
from .auth.routers import router as auth_router
from .raw_data import router as raw_data_router
from .tasks import router as tasks_router
from src.galaxy.db_session import database_instance
from src.galaxy.config import limiter, export_path, use_connection_pooling, use_s3_to_upload, logger as logging, config
from fastapi_versioning import VersionedFastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi.staticfiles import StaticFiles

# only use sentry if it is specified in config blocks
if config.get("SENTRY", "dsn", fallback=None):
    sentry_sdk.init(
        dsn=config.get("SENTRY", "dsn"),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=config.get("SENTRY", "rate")
    )


run_env = config.get("API_CONFIG", "env", fallback='prod')
if run_env.lower() == 'dev':
    # This is used for local setup for auth login
    import os
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = FastAPI(title="Galaxy API")
app.include_router(auth_router)
app.include_router(raw_data_router)
app.include_router(tasks_router)


app = VersionedFastAPI(app, enable_latest=True,
                       version_format='{major}', prefix_format='/v{major}')

if use_s3_to_upload is False:
    # only mount the disk if config is set to disk
    app.mount("/exports", StaticFiles(directory=export_path), name="exports")

app.state.limiter = limiter
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
    """Fires up 3 idle conenction with threaded connection pooling before starting the API

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
def on_shutdown():
    """Closing all the threads connection from pooling before shuting down the api
    """
    if use_connection_pooling:
        logging.debug("Shutting down connection pool")
        database_instance.close_all_connection_pool()
