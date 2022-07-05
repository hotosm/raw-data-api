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

@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"Error": str(exc)},
    )

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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



