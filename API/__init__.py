from pydantic import BaseModel as PydanticModel
import os

config = ConfigParser()
config.read("src/config.txt")


def to_camel(string: str) -> str:
    """formats underscore seperated words with camel case

    So this: hello_world_goodbye_new_york
    becomes this: helloWorldGoodbyeNewYork
    """
    split_string = string.split("_")

    return "".join([split_string[0], *[w.capitalize() for w in split_string[1:]]])


class BaseModel(PydanticModel):
    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True
