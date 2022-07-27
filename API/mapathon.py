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

from fastapi import APIRouter, Depends
from fastapi_versioning import  version
from src.galaxy.app import Mapathon
from src.galaxy.validation.models import (
    MapathonSummary,
    MapathonRequestParams,
    MapathonDetail,
)
from .auth import login_required

router = APIRouter(prefix="/mapathon")

@router.post("/detail", response_model=MapathonDetail)
@version(1,0)
def get_mapathon_detailed_report(params: MapathonRequestParams,
                                 user_data=Depends(login_required)):
    mapathon = Mapathon(params,"insight")
    return mapathon.get_detailed_report()

@router.post("/summary", response_model=MapathonSummary)
@version(1,0)
def get_mapathon_summary(params: MapathonRequestParams):
   
    if params.source == "underpass":
        mapathon = Mapathon(params,"underpass")
    else:
        mapathon = Mapathon(params,"insight")
    return mapathon.get_summary()