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

import json

from typing import List, Union ,Optional
import geojson
from pydantic import validator
from datetime import datetime, date, timedelta
from pydantic import BaseModel as PydanticModel

from pydantic import conlist , Json
from geojson_pydantic import Feature, FeatureCollection, Point, Polygon , MultiPolygon

from datetime import datetime

from enum import Enum

from area import area
import re

MAX_POLYGON_AREA = 5000 # km^2

# this as argument in compile method
SPECIAL_CHARACTER = '[@!#$%^&*() <>?/\|}{~:,"]'
ORGANIZATIONAL_FREQUENCY =  {"w" : 7,"m" : 30, "q": 90, "y":365}

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

class DateStampParams(BaseModel):
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
        if timestamp_diff > timedelta(days=30):
            raise ValueError(
                "Statistics is available for a maximum period of 1 month")

        return value
class UserStatsParams(DateStampParams):
    user_id: int
    hashtags: List[str]
    project_ids: List[int] = []
    
    


class User(BaseModel):
    user_id: int
    user_name: str

class IssueType(Enum):
    BAD_GEOM = "badgeom"
    BAD_VALUE = "badvalue"
    INCOMPLETE = "incomplete"
    NO_TAGS = "notags"
    COMPLETE = "complete"
    ORPHAN = "orphan"
    OVERLAPPING = "overlaping"
    DUPLICATE = "duplicate" 


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

class DataQuality_username_RequestParams(DateStampParams):
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
    hashtags: Optional[List[str]]
    issue_type: List[IssueType]
    output_type: OutputType
    geometry: Optional[Polygon]

    @validator("geometry", always=True)
    def check_not_defined_fields(cls, value, values):
        hashtags = values.get("hashtags")

        if value is None and (hashtags is None or len(hashtags) == 0):
            raise ValueError("'geometry' and 'hashtags' fields not provided")

        if value is None:
            return

        area_m2 = area(json.loads(value.json()))
        area_km2 = area_m2 * 1E-6

        if area_km2 > MAX_POLYGON_AREA:
            raise ValueError("Polygon Area is higher than 5000 km^2")

        return value


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

class Frequency(Enum):
    WEEKLY = "w"
    MONTHLY = "m"
    QUARTERLY = "q"
    YEARLY = "y"

class OrganizationOutputtype(Enum):
    JSON = "json"
    CSV = "csv"
    
class OrganizationHashtagParams(BaseModel):
    hashtags : conlist(str, min_items=1)
    frequency : Frequency
    output_type: OrganizationOutputtype
    start_date :  Optional[date] = None
    end_date : Optional[date] = None

    @validator("hashtags",allow_reuse=True)
    def check_hashtag_string(cls, value, values, **kwargs):
        regex = re.compile(SPECIAL_CHARACTER)
        for v in value :
            v= v.strip()
            if len(v) < 2 :
                raise ValueError(
                   "Hash tag value " +v+" is not allowed")
                
            if(regex.search(v) != None):
                raise ValueError(
                   "Hash tag contains special character or space : " +v+" ,Which is not allowed")
        return value 

    @validator("end_date",allow_reuse=True)
    def check_date_difference(cls, value, values, **kwargs):
        start_date = values.get("start_date")
        if start_date:      
            frequency = values.get("frequency")
            difference= value-start_date
            
            if difference < timedelta(days = ORGANIZATIONAL_FREQUENCY[frequency]):
                raise ValueError(f"""Minimum Date Difference is of {ORGANIZATIONAL_FREQUENCY[frequency]} days for """)
        return value


class OrganizationHashtag(BaseModel):
    hashtag: str
    frequency: str
    start_date :date
    end_date : date  
    total_new_buildings : int
    total_unique_contributors : int
    total_new_road_meters : int 

class RawDataOutputType ( Enum):
    GEOJSON ="geojson"
    KML = "kml"
    SHAPEFILE = "shp"

class HashtagParams(BaseModel):
    hashtags : Optional[List[str]]
    @validator("hashtags",allow_reuse=True)
    def check_hashtag_string(cls, value, values, **kwargs):
        regex = re.compile(SPECIAL_CHARACTER)
        for v in value :
            v= v.strip()
            if len(v) < 2 :
                raise ValueError(
                   "Hash tag value " +v+" is not allowed")
                
            if(regex.search(v) != None):
                raise ValueError(
                   "Hash tag contains special character or space : " +v+" ,Which is not allowed")
        return value 



RAWDATA_HISTORICAL_POLYGON_AREA = 100
class RawDataHistoricalParams(HashtagParams):
    from_timestamp :datetime
    to_timestamp : datetime
    geometry : MultiPolygon
    output_type : Optional[RawDataOutputType]
    # geometry_type : Optional[List[FeatureTypeRawData]] = None
    

    @validator("geometry", allow_reuse=True)
    def check_geometry_area(cls, value, values):
        cd=json.loads(value.json())["coordinates"]
        for x in range(len(cd)):
            geom_cd='{"type":"Polygon","coordinates":%s}'% cd[x]  
            area_m2 = area(geom_cd)
            
            area_km2 = area_m2 * 1E-6
            print(area_km2)
            if area_km2 > RAWDATA_HISTORICAL_POLYGON_AREA:
                raise ValueError("Polygon Area %s km^2 is higher than 100 km^2"%area_km2)
        return value
    
    @validator("to_timestamp",allow_reuse=True)
    def check_date_difference(cls, value, values, **kwargs):
        start_date = values.get("from_timestamp")
        hashtags = values.get("hashtags")
        difference= value-start_date
        if start_date > value :
            raise ValueError(f"""From and To timestamps are not in order""")
        if hashtags != None or len(hashtags) != 0:
            acceptedday=365
        else:
            acceptedday=180
        if difference > timedelta(days = acceptedday):
                raise ValueError(f"""You can pass date interval up to maximum {acceptedday} Months""")
        return value

class GeometryTypeRawData ( Enum):
    POINT="point"
    LINESTRING = "linestring"
    POLYGON = "polygon"
    MULTILINESTRING = "multilinestring"
    MULTIPOLYGON = "multipolygon"
    

class OsmElementRawData(Enum):
    NODES = "nodes"
    WAYS = "ways"
    RELATIONS = "relations"

RAWDATA_CURRENT_POLYGON_AREA = 500000
class RawDataCurrentParams(BaseModel):
    geometry : Polygon
    output_type : Optional[RawDataOutputType]
    osm_tags :  Optional[dict]=None
    osm_elements : Optional[List[OsmElementRawData]] = None
    geometry_type : Optional[List[GeometryTypeRawData]] = None
    
    
    @validator("osm_tags", allow_reuse=True)
    def check_value(cls, value, values):
        for key, v in value.items():
            if isinstance(v, list):   
                pass
            else :
                raise ValueError("Value should be of List Type")
        return value

    @validator("geometry_type", always=True)    
    def check_not_defined_fields(cls, value, values):
        osm_elements = values.get("osm_elements")
        if (value is None or len(value) == 0):
                return None
        if osm_elements:  
            if (GeometryTypeRawData.POINT.value in value and OsmElementRawData.NODES.value in osm_elements) or (GeometryTypeRawData.LINESTRING.value in value and OsmElementRawData.WAYS.value in osm_elements) or (GeometryTypeRawData.POLYGON.value in value and OsmElementRawData.WAYS.value in osm_elements) or (OsmElementRawData.RELATIONS.value in osm_elements):
                pass
            else:
                raise ValueError("Mapping between osm_elements and geometry_type is invalid")
            # if osm_elements:
        #     if (value != None or len(value) != 0)  and (osm_elements != None or len(osm_elements) != 0):
        #         raise ValueError("You can not pass both osm_elements and geometry_type")
        return value

    @validator("osm_elements", always=True)    
    def check_null_list(cls, value, values):
        if (value is None or len(value) == 0):
                return None
        return value
    
    @validator("geometry", allow_reuse=True)
    def check_geometry_area(cls, value, values):
        area_m2 = area(json.loads(value.json()))
        area_km2 = area_m2 * 1E-6
        # print(area_km2)
        if area_km2 > RAWDATA_CURRENT_POLYGON_AREA:
                raise ValueError(f"""Polygon Area {int(area_km2)} km^2 is higher than {RAWDATA_CURRENT_POLYGON_AREA} km^2""")
        return value
        # cd=json.loads(value.json())["coordinates"]
        # for x in range(len(cd)):
        #     geom_cd='{"type":"Polygon","coordinates":%s}'% cd[x]  
        #     area_m2 = area(geom_cd)
        #     area_km2 = area_m2 * 1E-6
        #     print(f"""{area_km2} Square Km""")
        #     if area_km2 > RAWDATA_CURRENT_POLYGON_AREA:
        #         raise ValueError("Polygon Area %s km^2 is higher than 10 km^2"%area_km2)

