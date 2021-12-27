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

from .countries.routers import router as countries_router
from .changesets.routers import router as changesets_router
from .data.routers import router as data_router
from .auth.routers import router as auth_router
from .mapathon import router as mapathon_router
from .osm_users import router as osm_users_router
from .data_quality import router as data_quality_router
from .trainings import router as training_router
from .organization import router as organization_router



app = FastAPI()

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


