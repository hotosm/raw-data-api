from enum import Enum
from geojson_pydantic.geometries import Polygon
from pydantic import BaseModel, ValidationError, validator
from typing import Union

class PolygonFilter(Enum):
    iso3 = "iso3"
    geojson = "geojson"


class FilterParams(BaseModel):
    type: PolygonFilter
    value: Union[str, Polygon]

    @validator("type", "value")
    def matching_types(cls, v, values, **kwargs):
        type_val = values.get("type")
        if "type" in values and values["type"].value == PolygonFilter.iso3.value and type(v) is not str:
            raise ValueError("Value must be ISO3 code")

        if "type" in values and values["type"].value == PolygonFilter.iso3.value and len(v) != 3:
            raise ValueError("Invalid ISO3 code")

        if "type" in values and values["type"].value == PolygonFilter.geojson.value and type(v) is not Polygon:
            raise ValueError("Value must be geojson polygon")

        return v


'''
{
    "type": "custom",
    "value": {
        "type": "Polygon",
        "coordinates": [
            [
                [-74.91995705, 10.91624758],
                [-74.75556731, 10.91624758],
                [-74.75556731, 11.10768916],
                [-74.91995705, 11.10768916],
                [-74.91995705, 10.91624758]
            ]
        ]
    }
}

'''