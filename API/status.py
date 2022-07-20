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
from src.galaxy.validation.models import DataOutput, DataSource, DataRecencyParams
from src.galaxy.app import Status

router = APIRouter(prefix="/status")

@router.post("/")
def data_recency_status(params: DataRecencyParams):
  """Gives the time lapse since the last update per data source per data output"""
  result = None
  db = Status(params)

  if (params.data_source == DataSource.INSIGHTS.value):
    if (params.data_output == DataOutput.OSM.value):
      result = db.get_osm_recency()
    elif(params.data_output == DataOutput.mapathon_statistics.value):
      result = db.get_mapathon_statistics_recency()
    elif(params.data_output == DataOutput.user_statistics.value):
      result = db.get_user_statistics_recency()

  if (params.data_source == DataSource.UNDERPASS.value):
    if (params.data_output == DataOutput.OSM.value):
      result = db.get_osm_recency()
    elif(params.data_output == DataOutput.data_quality.value):
      result = db.get_user_data_quality_recency()

  return { "time_difference": str(result) if result else None }
