from fastapi import APIRouter
from typing import List
from configparser import ConfigParser

from src.galaxy.validation.models import UsersListParams, User, UserStatsParams, MappedFeature
from src.galaxy.app import UserStats
from src.galaxy import config

router = APIRouter(prefix="/osm-users")


@router.post("/ids", response_model=List[User])
def list_users(params: UsersListParams):
    return UserStats().list_users(params)


@router.post("/statistics/", response_model=List[MappedFeature])
def user_statistics(params: UserStatsParams):
    user_stats = UserStats(dict(config.items("INSIGHTS_PG")))

    if len(params.hashtags) > 0:
        return user_stats.get_statistics_with_hashtags(params)

    return user_stats.get_statistics(params)
