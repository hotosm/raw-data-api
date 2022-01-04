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

"""[Router Responsible for Raw data API ]
"""
from fastapi import APIRouter, Depends
from src.galaxy.validation.models import RawDataParams
from .auth import login_required
from src.galaxy.app import RawData
from fastapi.responses import StreamingResponse
from datetime import datetime
import geojson
import io
router = APIRouter(prefix="/rawdata")


@router.post("")
def get_raw_data(params:RawDataParams):
    result= RawData(params).extract_data()
    stream = io.StringIO()
    geojson.dump(result,stream)
    response = StreamingResponse(iter([stream.getvalue()]),media_type="application/geo+json")
    exportname =f"Raw_Data_{datetime.now().isoformat()}"
    response.headers["Content-Disposition"] = f"attachment; filename={exportname}.geojson"
    return response
