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

from typing import List, Union ,Optional
from pydantic import validator
from datetime import datetime, date, timedelta
from pydantic import BaseModel as PydanticModel

from pydantic import conlist
from geojson_pydantic import Feature, FeatureCollection, Point

from datetime import datetime

from enum import Enum


def to_camel(string: str) -> str:
    split_string = string.split("_")

    return "".join(
        [split_string[0], *[w.capitalize() for w in split_string[1:]]])


class BaseModel(PydanticModel):
    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True
        use_enum_values = True


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


class TimeStampParams(BaseModel):
    from_timestamp: Union[datetime, date]
    to_timestamp: Union[datetime, date]

    @validator("to_timestamp",allow_reuse=True)
    def check_timestamp_diffs(cls, value, values, **kwargs):
        '''checks the timestap difference '''

        from_timestamp = values.get("from_timestamp")

        # if from_timestamp > datetime.now() or value > datetime.now():
        #     raise ValueError(
        #         "Can not exceed current date and time")
        timestamp_diff = value - from_timestamp
        if from_timestamp > value :
            raise ValueError(
                "Timestamp difference should be in order")
        if timestamp_diff > timedelta(hours=24):
            raise ValueError(
                "Timestamp difference must be lower than 24 hours")

        return value


invalid_request_parameters=[" ",'"','""','" "']
class MapathonRequestParams(TimeStampParams):
    '''validation class for mapathon request parameter provided by user '''

    project_ids: List[int]
    hashtags: List[str]
    source: Optional[str]

    @validator("hashtags",allow_reuse=True)
    def check_hashtag_filter(cls, value, values, **kwargs):
        '''check the hashtag existence''' 

        project_ids = values.get("project_ids")
        if len(project_ids) == 0 and len(value) == 0:
            raise ValueError(
                "Empty lists found for both hashtags and project_ids params")
        for v in value :
            if  v =="":
                raise ValueError("Hashtag value contains unsupported character")
        return value

    @validator("source", allow_reuse=True)
    def check_source(cls, value, **kwargs):
        '''checks the either source  is supported or not '''
        if value is None or value == "insight" or value == "underpass":
            return value
        else:
            raise ValueError('Source '+str(value)+" does not exist")   

class UsersListParams(BaseModel):
    user_names: List[str]
    from_timestamp: Union[datetime, date]
    to_timestamp: Union[datetime, date]


class UserStatsParams(TimeStampParams):
    user_id: int
    hashtags: List[str]
    project_ids: List[int] = []


class User(BaseModel):
    user_id: int
    user_name: str

class IssueType(Enum):
    BAD_GEOM = "badgeom"
    BAD_VALUE = "badvalue"
    INCOMPLETE = "incomplete_tags"


class OutputType(Enum):
    CSV = "csv"
    GEOJSON = "geojson"

class DataQuality_TM_RequestParams(BaseModel):
    '''Request Parameteres validation for DataQuality Class Tasking Manager Project ID
    
    Parameters:
            “project_ids”:[int],
            “issue_type”: ["badgeom", "badvalue", "all"]
    
    Acceptance Criteria : 
            project_ids: Required, Array can contain integer value only , Array can not be empty
            issue_type: Required, Only accepted value under supported issues ,Array can not be empty

    '''
    #using conlist of pydantic to refuse empty list
    project_ids: conlist(int, min_items=1)
    issue_types: List[IssueType]
    output_type: OutputType

class DataQuality_username_RequestParams(TimeStampParams):
    '''Request Parameteres validation for DataQuality Class Username
    
    Parameters:
            osm_usernames:[str],
            “issue_type”: ["badgeom", "badvalue", "all"]
            from_timestamp and to_timestamp
    '''
    #using conlist of pydantic to refuse empty list

    osm_usernames: conlist(str, min_items=1)
    issue_types: List[IssueType]
    output_type: OutputType


class DataQualityProp(BaseModel):
    Osm_id: int
    Changeset_id: int
    Changeset_timestamp: Union[datetime, date]
    Issue_type: str


class DataQualityPointFeature(Feature):
    geometry: Point
    properties: DataQualityProp


class DataQualityPointCollection(FeatureCollection):
    """geojson pydantic models for data quality , Note : Not required if we will be using OUTPUT Class

    Args:
        FeatureCollection ([type]): [description]
    """
    features: List[DataQualityPointFeature]


class DataQualityHashtagParams(TimeStampParams):
    hashtags: List[str]
    issue_type: List[IssueType]
    output_type: OutputType

class Source(Enum):
    UNDERPASS ="underpass"
    INSIGHT = "insight"

class TrainingOrganisations(BaseModel):
    id: int
    name: str

class Trainings(BaseModel):
    tid: int
    name: str
    location :str = None
    organization : str = None 
    eventtype : str = None
    topictype : str = None
    topics : str = None 
    hours : int = None
    date : date

class EventType(Enum):
    VIRTUAL = "virtual"
    IN_PERSON = "inperson"

class TopicType(Enum):
    # JOSM = "josm"
    # ID_EDITOR = "ideditor"
    # VALIDATION = "validation"
    REMOTE = "remote"
    FIELD = "field"
    OTHER = "other"

class TrainingParams(BaseModel):
    """[Training Post API Parameter Validation Model]

    Args:
        BaseModel ([type]): [Pydantic Model]

    Raises:
        ValueError: [Timestamp difference should be in order]
        Unprocessable Entity: [If any skill type or event type is out of predefined Enum values]
    Returns:
        [value]: [Validated Parameters]
    """
    from_datestamp: Optional[date] = None
    to_datestamp: Optional[date] = None
    oid: Optional[int] = None
    topic_type : Optional[List[TopicType]] = None
    event_type : Optional[EventType] = None
    
    @validator("to_datestamp",allow_reuse=True)
    def check_timestamp_order(cls, value, values, **kwargs):
        '''checks the datestamps order '''
        from_datestamp = values.get("from_datestamp")
        if from_datestamp :
            if from_datestamp > value :
                raise ValueError(
                    "Timestamp should be in order")
        return value


