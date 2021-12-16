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

from fastapi import APIRouter
from typing import List


from src.galaxy.validation.models import UsersListParams, User, UserStatsParams, MappedFeature
from src.galaxy.app import UserStats


router = APIRouter(prefix="/osm-users")


@router.post("/ids", response_model=List[User])
def list_users(params: UsersListParams):
    return UserStats().list_users(params)


@router.post("/statistics", response_model=List[MappedFeature])
def user_statistics(params: UserStatsParams):
    user_stats = UserStats()

    if len(params.hashtags) > 0:
        return user_stats.get_statistics_with_hashtags(params)

    return user_stats.get_statistics(params)
