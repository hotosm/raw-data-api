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


@router.post("/statistics",response_model=List[OrganizationHashtag])
@version(1,0)
# def get_organisations_list(user_data=Depends(login_required)):
def get_ogranization_stat(params:OrganizationHashtagParams):
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
