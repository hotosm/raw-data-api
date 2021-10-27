from typing import List, Union
from pydantic import validator
from .. import BaseModel
from datetime import datetime, date, timedelta


class MappedFeature(BaseModel):
    feature: str
    action: str
    count: int


class MapathonContributor(BaseModel):
    user_id: int
    username: str
    total_buildings: int
    mapped_tasks: int
    validated_tasks: int
    editors: str


class MappedFeatureWithUser(MappedFeature):
    username: str


class MapathonSummary(BaseModel):
    total_contributors: int
    mapped_features: List[MappedFeature]


class MapathonDetail(BaseModel):
    mapped_features: List[MappedFeatureWithUser]
    contributors: List[MapathonContributor]


class MapathonRequestParams(BaseModel):
    project_ids: List[int]
    from_timestamp: Union[datetime, date]
    to_timestamp: Union[datetime, date]
    hashtags: List[str]

    @validator("to_timestamp")
    def check_timestamp_diffs(cls, value, values, **kwargs):
        from_timestamp = values.get("from_timestamp")
        timestamp_diff = value - from_timestamp
        if timestamp_diff > timedelta(hours=24):
            raise ValueError(
                "Timestamp difference must be lower than 24 hours"
            )

        return value

    @validator("hashtags")
    def check_hashtag_filter(cls, value, values, **kwargs):
        project_ids = values.get("project_ids")
        if len(project_ids) == 0 and len(value) == 0:
            raise ValueError(
                "Empty lists found for both hashtags and project_ids params"
            )

        return value
