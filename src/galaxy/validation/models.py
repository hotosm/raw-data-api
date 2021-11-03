from typing import List, Union
from pydantic import validator
from datetime import datetime, date, timedelta
from pydantic import BaseModel as PydanticModel
from pydantic import conlist
from geojson_pydantic import Feature,FeatureCollection, Point

supported_issue_types=["bad_geometry", "bad_value", "incomplete_tags", "all"]


def to_camel(string: str) -> str:
    split_string = string.split("_")

    return "".join(
        [split_string[0], *[w.capitalize() for w in split_string[1:]]])


class BaseModel(PydanticModel):
    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True


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
    '''validation class for mapathon request parameter provided by user '''

    project_ids: List[int]
    from_timestamp: Union[datetime, date]
    to_timestamp: Union[datetime, date]
    hashtags: List[str]

    @validator("to_timestamp",allow_reuse=True)
    def check_timestamp_diffs(cls, value, values, **kwargs):
        '''checks the timestap difference '''

        from_timestamp = values.get("from_timestamp")
        timestamp_diff = value - from_timestamp
        if timestamp_diff > timedelta(hours=24):
            raise ValueError(
                "Timestamp difference must be lower than 24 hours")

        return value

    @validator("hashtags",allow_reuse=True)
    def check_hashtag_filter(cls, value, values, **kwargs):
        '''check the hashtag existence''' 

        project_ids = values.get("project_ids")
        if len(project_ids) == 0 and len(value) == 0:
            raise ValueError(
                "Empty lists found for both hashtags and project_ids params")

        return value

class DataQualityRequestParams(BaseModel):
    '''Request Parameteres validation for DataQuality Class
    Parameters:
            “project_ids”:[int],
            “issue_type”: ["bad_geometry", "bad_value", "incomplete_tags", "all"]
    Acceptance Criteria : 
            project_ids: Required, Array can contain integer value only , Array can not be empty
            issue_type: Required, Only accepted value under supported issues ,Array can not be empty

    '''
    #using conlist of pydantic to refuse empty list 

    project_ids: conlist(int, min_items=1)
    issue_type: conlist(str, min_items=1)

    @validator("issue_type",allow_reuse=True)
    def match_value(cls, value,**kwargs):
        '''checks the either passed value is valid or not '''
        if not value in supported_issue_types:
            raise ValueError('Issue type  must be in : '+ str(supported_issue_types))
        return value

class DataQualityProp(BaseModel):
    Osm_id: int
    Changeset_id: int
    Changeset_timestamp: Union[datetime, date]
    Issue_type: str

class DataQualityPointFeature(Feature):
    geometry: Point
    properties: DataQualityProp

class DataQualityPointCollection(FeatureCollection):
   features: List[DataQualityPointFeature]

