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
@version(1)
def get_mapathon_detailed_report(params: MapathonRequestParams,
                                 user_data=Depends(login_required)):
    """End point to return detailed Mapathon report with the user information with their contribution

    Args:
    
    
        params (MapathonRequestParams): {
                                "fromTimestamp": "from when you want to have data",
                                "toTimestamp": "until when you want to have data ",
                                "projectIds": [
                                    tasking manager project id (only integer) 
                                ],
                                "hashtags": [
                                    "list of hashtags you want to use without # sign"
                                ],
                                "source": "Define source of data : Options are insight,underpass -  currently supports : insight only"
                                }
        user_data (_type_, optional): _description_. Defaults to Depends(login_required). Authentication will be required , access token can be generated from /auth/login


    Returns:
    
    
        json: {
                "mappedFeatures": [
                    {
                    "feature": "string",
                    "action": "string",
                    "count": 0,
                    "username": "string"
                    }
                ],
                "contributors": [
                    {
                    "userId": 0,
                    "username": "string",
                    "totalBuildings": 0,
                    "editors": "string"
                    }
                ],
                "tmStats": [
                    {
                    "tasksMapped": [
                        {
                        "userId": 0,
                        "tasksMapped": 0
                        }
                    ],
                    "tasksValidated": [
                        {
                        "userId": 0,
                        "tasksValidated": 0
                        }
                    ],
                    "timeSpentMapping": [
                        {
                        "userId": 0,
                        "timeSpentMapping": 0
                        }
                    ],
                    "timeSpentValidating": [
                        {
                        "userId": 0,
                        "timeSpentValidating": 0
                        }
                    ]
                    }
                ]
                }
                
                
    Example Request : 
    
    1. Example with hashtag : 
    
        {
            "fromTimestamp":"2022-07-21T18:15:00.461",
            "toTimestamp":"2022-07-22T18:14:59.461",
            "projectIds":[
            ],
            "hashtags":[
                "missingmaps"
            ]
        }
    
    2. Example with tasking manager project id : 
    
        {
            "fromTimestamp":"2022-07-21T18:15:00.461",
            "toTimestamp":"2022-07-22T18:14:59.461",
            "projectIds":[
                8237
            ],
            "hashtags":[
            ]
        }
        
    Note : Passing both tasking manager id and hashtag will work as OR condition for the query
    
    Example Response : 
    
            {
        "mappedFeatures":[
            {
                "feature":"place",
                "action":"create",
                "count":40,
                "username":"#"
            },
            {
                "feature":"landuse",
                "action":"create",
                "count":41,
                "username":"Frans S"
            },
            {
                "feature":"building",
                "action":"create",
                "count":168,
                "username":"#"
            },
            {
                "feature":"place",
                "action":"modify",
                "count":1,
                "username":"#"
            },
            {
                "feature":"landuse",
                "action":"modify",
                "count":1,
                "username":"#"
            },
            {
                "feature":"building",
                "action":"modify",
                "count":18,
                "username":"#"
            },
            {
                "feature":"building",
                "action":"create",
                "count":505,
                "username":"#"
            },
            {
                "feature":"landuse",
                "action":"modify",
                "count":7,
                "username":"#"
            },
            {
                "feature":"building",
                "action":"create",
                "count":21,
                "username":"#"
            },
            {
                "feature":"building",
                "action":"modify",
                "count":1,
                "username":"#"
            },
            {
                "feature":"building",
                "action":"create",
                "count":91,
                "username":"#"
            },
            {
                "feature":"building",
                "action":"modify",
                "count":1,
                "username":"#"
            }
        ],
        "contributors":[
            {
                "userId":1962399,
                "username":"#",
                "totalBuildings":186,
                "editors":"JOSM/1.5 (18513 en),"
            },
            {
                "userId":6854898,
                "username":"#",
                "totalBuildings":505,
                "editors":"JOSM/1.5 (18303 fr),"
            },
            {
                "userId":10514559,
                "username":"#",
                "totalBuildings":22,
                "editors":"iD 2.20.2,JOSM/1.5 (18513 nl),"
            },
            {
                "userId":12564859,
                "username":"#",
                "totalBuildings":92,
                "editors":"iD 2.20.2,"
            }
        ],
        "tmStats":[
            {
                "tasksMapped":[
                    
                ],
                "tasksValidated":[
                    
                ],
                "timeSpentMapping":[
                    
                ],
                "timeSpentValidating":[
                    
                ]
            }
        ]
        }
    """
    mapathon = Mapathon(params,"insight")
    return mapathon.get_detailed_report()

@router.post("/summary", response_model=MapathonSummary)
@version(1)
def get_mapathon_summary(params: MapathonRequestParams):
    """Returns summary of Mapathon , It doesn't require authorization
    Args:
        params (MapathonRequestParams): 
        
                               {
                                "fromTimestamp": "from when you want to have data",
                                "toTimestamp": "until when you want to have data ",
                                "projectIds": [
                                    tasking manager project id (only integer) 
                                ],
                                "hashtags": [
                                    "list of hashtags you want to use without # sign"
                                ],
                                "source": "Define source of data : Options are insight,underpass"
                                }

    Returns:
        json: 
        
            {
            "totalContributors": 0,
            "mappedFeatures": [
                {
                "feature": "string",
                "action": "string",
                "count": 0
                }
            ]
            }
            
    Example Request : 
    1. With hashtag
    
        {
            "fromTimestamp":"2022-07-22T13:15:00.461",
            "toTimestamp":"2022-07-22T14:15:00.461",
            "projectIds":[],
            "hashtags":[
                "missingmaps"
            ]
        }
        
    2. With tasking manager ID : 
    
            {
            "fromTimestamp":"2022-07-21T18:15:00.461",
            "toTimestamp":"2022-07-22T18:14:59.461",
            "projectIds":[
                8237
            ],
            "hashtags":[
            ]
        }
    
    Example Response : 
    
        {
        "totalContributors":4,
        "mappedFeatures":[
            {
                "feature":"building",
                "action":"create",
                "count":785
            },
            {
                "feature":"landuse",
                "action":"create",
                "count":41
            },
            {
                "feature":"place",
                "action":"create",
                "count":40
            },
            {
                "feature":"building",
                "action":"modify",
                "count":20
            },
            {
                "feature":"landuse",
                "action":"modify",
                "count":8
            },
            {
                "feature":"place",
                "action":"modify",
                "count":1
            }
        ]
        }
    """
   
    if params.source == "underpass":
        mapathon = Mapathon(params,"underpass")
    else:
        mapathon = Mapathon(params,"insight")
    return mapathon.get_summary()