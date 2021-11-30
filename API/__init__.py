from pydantic import BaseModel as PydanticModel
import os

config = ConfigParser()
config.read("data/config.txt")
_F_DBCFG_FILE = True
_F_DBCFG_JSON = False
_F_DBCFG_PARAM = False
try:
    """Get JSON from AWS secrets manager
    and set a flag indicating Connection Parameters have been supplied.
    JSON Format = { host=<host>, user=<user>, password=<password>,
                    dbName=<db>, port=<port> }

    """
    import json

    POSTGRES_CONNECTION_PARAMS = json.loads(os.getenv("POSTGRES_CONNECTION_PARAMS"))
    del POSTGRES_CONNECTION_PARAMS["dbinstanceidentifier"]
    del POSTGRES_CONNECTION_PARAMS["engine"]
    _F_DBCFG_JSON = True
except:
    """TODO: Use libpq friendly envvars
    https://www.postgresql.org/docs/current/static/libpq-envars.html

    PGHOST, PGUSER, PGPASSWORD, PGPORT, PGDATABASE
    """
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT")
    POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE")
    POSTGRES_CONNECTION_PARAMS = dict(
        host=POSTGRES_HOST,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        port=POSTGRES_PORT,
        name=POSTGRES_DATABASE,
    )
    _F_DBCFG_PARAM = True
    _F_DBCFG_JSON = _F_DBCFG_FILE = False


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
