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
from fastapi import APIRouter, Depends
from fastapi_versioning import  version
from src.galaxy.app import OrganizationHashtags
from src.galaxy.validation.models import OrganizationHashtag, OrganizationOutputtype,OrganizationHashtagParams
from .auth import login_required
from typing import List
from fastapi.responses import StreamingResponse
import io
from datetime import datetime

router = APIRouter(prefix="/hashtags")


@router.post("/statistics/",response_model=List[OrganizationHashtag])
@version(1)
# def get_organisations_list(user_data=Depends(login_required)):
def get_hashtag_stats(params:OrganizationHashtagParams):
    """Monitors the statistics made in some speciifc set of hashtag periodically , Provides statistics frequency weekly quarterly monthly ! For this you need to request tech team to get you hashtag registered for monitoring 

    Args:
            {
            "hashtags": [
                "string" # list of hashtags statistics you want 
            ],
            "frequency": "w", # based on this counts will be aggregated and displayed , supported :     WEEKLY = "w",MONTHLY = "m",QUARTERLY = "q",YEARLY = "y"
            "outputType": "json", # supoprted json and csv 
            "startDate": "2022-07-28",
            "endDate": "2022-07-28"
            }

    Returns:

    Based on the frequency it will have following set of  result for each frequency
            [
            {
                "hashtag": "string",
                "frequency": "string",
                "startDate": "2022-07-28",
                "endDate": "2022-07-28",
                "totalNewBuildings": 0,
                "totalUniqueContributors": 0,
                "totalNewRoadMeters": 0,
                "totalNewAmenities": 0,
                "totalNewPlaces": 0
            }
            ]
    
    Example Request : 
    1. To get weekly stats 

        {
            "hashtags": [
                "msf"
            ],
            "frequency": "w",
            "outputType": "json",
            "startDate": "2020-10-22",
            "endDate": "2020-12-22"
        }
    2. To get monthly stats

        {
            "hashtags": [
                "msf"
            ],
            "frequency": "m",
            "outputType": "json",
            "startDate": "2020-10-22",
            "endDate": "2020-12-22"
        }
    
    Example Response :
    
        [
        {
            "hashtag": "msf",
            "frequency": "w",
            "startDate": "2020-10-23",
            "endDate": "2020-10-30",
            "totalNewBuildings": 7937,
            "totalUniqueContributors": 80,
            "totalNewRoadMeters": 15376,
            "totalNewAmenities": 33,
            "totalNewPlaces": 3
        },
        {
            "hashtag": "msf",
            "frequency": "w",
            "startDate": "2020-10-30",
            "endDate": "2020-11-06",
            "totalNewBuildings": 12744,
            "totalUniqueContributors": 116,
            "totalNewRoadMeters": 38274,
            "totalNewAmenities": 2,
            "totalNewPlaces": 0
        },
        {
            "hashtag": "msf",
            "frequency": "w",
            "startDate": "2020-11-06",
            "endDate": "2020-11-13",
            "totalNewBuildings": 9147,
            "totalUniqueContributors": 52,
            "totalNewRoadMeters": 31882,
            "totalNewAmenities": 0,
            "totalNewPlaces": 1
        },
        {
            "hashtag": "msf",
            "frequency": "w",
            "startDate": "2020-11-13",
            "endDate": "2020-11-20",
            "totalNewBuildings": 41900,
            "totalUniqueContributors": 371,
            "totalNewRoadMeters": 19981,
            "totalNewAmenities": 79,
            "totalNewPlaces": 16
        },
        {
            "hashtag": "msf",
            "frequency": "w",
            "startDate": "2020-11-20",
            "endDate": "2020-11-27",
            "totalNewBuildings": 26645,
            "totalUniqueContributors": 152,
            "totalNewRoadMeters": 85923,
            "totalNewAmenities": 6,
            "totalNewPlaces": 1
        },
        {
            "hashtag": "msf",
            "frequency": "w",
            "startDate": "2020-11-27",
            "endDate": "2020-12-04",
            "totalNewBuildings": 31186,
            "totalUniqueContributors": 228,
            "totalNewRoadMeters": 27537,
            "totalNewAmenities": 54,
            "totalNewPlaces": 0
        },
        {
            "hashtag": "msf",
            "frequency": "w",
            "startDate": "2020-12-04",
            "endDate": "2020-12-11",
            "totalNewBuildings": 35996,
            "totalUniqueContributors": 206,
            "totalNewRoadMeters": 83153,
            "totalNewAmenities": 0,
            "totalNewPlaces": 1
        },
        {
            "hashtag": "msf",
            "frequency": "w",
            "startDate": "2020-12-11",
            "endDate": "2020-12-18",
            "totalNewBuildings": 27088,
            "totalUniqueContributors": 70,
            "totalNewRoadMeters": 261235,
            "totalNewAmenities": 0,
            "totalNewPlaces": 0
        }
        ]
    """
    organization= OrganizationHashtags(params)
    if params.output_type == OrganizationOutputtype.JSON.value:
        return organization.get_report()
    stream = io.StringIO()
    exportname =f"Hashtags_Organization_{datetime.now().isoformat()}"
    organization.get_report_as_csv(stream)
    response = StreamingResponse(iter([stream.getvalue()]),
                            media_type="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename="+exportname+".csv"
    return response
