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

"""[Router Responsible for Organizational data API ]
"""
from fastapi import APIRouter, Depends,Response
from fastapi_versioning import  version
# from .auth import login_required

from src.galaxy.tasking_manager.models import ValidatorStatsRequest
from src.galaxy.app import TaskingManager

from fastapi.responses import StreamingResponse

from datetime import datetime


router = APIRouter(prefix="/tasking-manager")

@router.post("/validators/")
@version(1)
def get_validator_stats(request: ValidatorStatsRequest):
    """Endpoint returns statistics of validators reading tasking manager database 

    Args:
    
    
        year: int =                             Compulsory field , you need to supply year in integer . Applies filter on project creation date within that year and includes mapping activity associated to those projects irrespect of activity date
        country: Optional[str] =                Optional filter , case insensitive 
        organisation: Optional[List[int]] =     Takes organisation id to filter output , can support multiple organisation as list organisation id can be retrived from Tasking manager /api/organisations 
        status : Optional[ProjectStatus] =      Only takes integer which represents : 
                                                ARCHIVED = 0
                                                PUBLISHED = 1
                                                DRAFT = 2

    Returns:
        csv : Stats
        404 Error : If no data found for the request 
    
    Example Request : 

        1) To extract all stats within year 
            {
                "year": 2012
            }
            
        2) To extract data of specific country for that year 
            {
                "year": 2012,
                "country": "indonesia"
            }
        3) To extract  data of some organisation 
            {
                "year": 2012,
                "organisation": [
                    73
                ]
            }
        4) To get data for the projects in indonesia created by organisation : HOT which are archived 
            {
                "year": 2012,
                "country": "indonesia",
                "organisation": [
                    73
                ],
                "status": 0
            }
        
    """
    tm = TaskingManager(request)
    csv_stream = tm.get_validators_stats()
    if csv_stream:
        response = StreamingResponse(csv_stream)
        name =f"ValidatorStats_{datetime.now().isoformat()}"
        response.headers["Content-Disposition"] = f"attachment; filename={name}.csv"

        return response
    return Response("No Data Found", status_code=404)


@router.get("/teams/")
@version(1)
def get_teams():
    csv_stream = TaskingManager().list_teams()

    response = StreamingResponse(csv_stream)
    name =f"Teams_{datetime.now().isoformat()}"
    response.headers["Content-Disposition"] = f"attachment; filename={name}.csv"

    return response


@router.get("/teams/individual/")
@version(1)
def get_specific_team():
    csv_stream = TaskingManager().list_teams_metadata()

    response = StreamingResponse(csv_stream)
    name =f"Teams_{datetime.now().isoformat()}"
    response.headers["Content-Disposition"] = f"attachment; filename={name}.csv"

    return response
