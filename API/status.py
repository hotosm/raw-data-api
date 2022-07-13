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

"""
  Router Responsible for Data Source Update Status
"""

from fastapi import APIRouter
from src.galaxy.validation.models import DataSource
from src.galaxy.app import Status

router = APIRouter(prefix="/status")

@router.get("/{data_source}")
def get_current_database_status(data_source: DataSource):
    """Gives the database update status depending on the source"""
    status = Status(data_source)
    result = None

    if data_source == DataSource.INSIGHTS.value:
      result = status.check_insights_status()

    if data_source == DataSource.UNDERPASS.value:
      result = status.check_underpass_status()

    # result = result/60 #convert to minutes

    # if int(result) == 0:
    #   response = "less than a minute ago"
    # elif int(result) == 1:
    #    response = "1 minute ago"
    # else:
    #   response = f"""{int(result)} minutes ago"""

    # return { "last_updated": response }
    return { "last_updated_seconds": result }