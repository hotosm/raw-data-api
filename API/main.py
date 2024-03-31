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

# Standard library imports
# Humanitarian OpenStreetmap Team
# 1100 13th Street NW Suite 800 Washington, D.C. 20005
# <info@hotosm.org>
# Standard library imports
# Standard library imports
import logging
import os
import time
from typing import Callable

# Third party imports
import asyncpg
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi_versioning import VersionedFastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Reader imports
from src.__version__ import __version__
from src.config import get_settings

from .auth.routers import router as auth_router
from .raw_data import router as raw_data_router
from .tasks import router as tasks_router

# Initialize settings
(
    celery_config,
    api_config,
    hdx_config,
    db_config,
    oauth_config,
    export_upload_config,
    sentry_config,
) = get_settings()

# Configure logging
logging.basicConfig(level=api_config.log_level.upper())

# Configure Sentry if enabled
if sentry_config.sentry_dsn:
    # Third party imports
    import sentry_sdk

    sentry_sdk.init(
        dsn=sentry_config.sentry_dsn,
        traces_sample_rate=sentry_config.sentry_rate,
    )


# Create FastAPI app
app = FastAPI(
    title="Raw Data API",
    version=__version__,
    swagger_ui_parameters={"syntaxHighlight": False},
)

# Include routers
app.include_router(auth_router)
app.include_router(raw_data_router)
app.include_router(tasks_router)

# Include additional routers based on configurations
if api_config.custom_exports.enable_custom_exports:
    from .custom_snapshot import router as custom_exports_router

    app.include_router(custom_exports_router)

if api_config.polygon_statistics.enable_polygon_statistics_endpoints:
    from .stats import router as stats_router

    app.include_router(stats_router)

if hdx_config.enable_hdx_exports:
    from .hdx import router as hdx_router

    app.include_router(hdx_router)

if export_upload_config.file_upload_method.lower() == "s3":
    from .s3 import router as s3_router

    app.include_router(s3_router)

# Configure OpenAPI documentation
app.openapi = {
    "info": {
        "title": "Raw Data API",
        "version": __version__,
    },
    "security": [{"OAuth2PasswordBearer": []}],
}

# Versioning
app = VersionedFastAPI(
    app, enable_latest=True, version_format="{major}", prefix_format="/v{major}"
)

# Mount static files if not using S3
if export_upload_config.file_upload_method.lower() != "s3":
    app.mount(
        "/exports", StaticFiles(directory=api_config.export.export_path), name="exports"
    )

# Configure rate limiting

# Configure rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=api_config.rate_limit.rate_limiter_storage_uri,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

cors_config = api_config.cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config.allowed_origins,
    allow_credentials=cors_config.allow_credentials,
    allow_methods=cors_config.allowed_methods,
    allow_headers=cors_config.allowed_headers,
)


# Add middleware to log request processing time
@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Callable):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(f"{process_time:0.4f} sec")
    return response


# Add exception handler for request validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f"{exc}".replace("\n", " ").replace("\r", " ")
    logging.error(f"{request}: {exc_str}")
    content = {"status_code": 422, "message": exc_str, "data": None}
    return JSONResponse(content=content, status_code=422)


# Startup event to initialize database tables
@app.on_event("startup")
async def on_startup():
    try:
        # Open SQL file
        sql_file_path = os.path.join(
            os.path.realpath(os.path.dirname(__file__)), "data/tables.sql"
        )
        with open(sql_file_path, "r", encoding="UTF-8") as sql_file:
            create_tables_sql = sql_file.read()

        # Connect to the database and execute SQL statements
        conn = await asyncpg.connect(**db_config.dict())
        await conn.execute(create_tables_sql)
        await conn.close()
        logging.info("Database tables initialized successfully.")

    except Exception as e:
        logging.error("Error initializing database tables: %s", e)
        raise e


# Shutdown event to log application shutdown
@app.on_event("shutdown")
async def on_shutdown():
    logging.info("Application shutdown.")


# Redirect root path to swagger documentation
@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url=f"/docs")
