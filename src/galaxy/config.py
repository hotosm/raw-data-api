#!/usr/bin/env python
# -*- coding: utf-8 -*-

from configparser import ConfigParser
import logging

CONFIG_FILE_PATH = "src/config.txt"

config = ConfigParser()
config.read(CONFIG_FILE_PATH)

#check either to use connection pooling or not 
if config.get('EXPORT_CONFIG', 'use_connection_pooling', fallback=None): 
    use_connection_pooling=True
else:
    use_connection_pooling=False

def get_db_connection_params(dbIdentifier: str) -> dict:
    """Return a python dict that can be passed to psycopg2 connections
    to authenticate to Postgres Databases

    Params: dbIdentifier: Section name of the INI config file containing
            database connection parameters

    Returns: connection_params (dict): PostgreSQL connection parameters
             corresponding to the configuration section.

    """

    ALLOWED_SECTION_NAMES = ('INSIGHTS', 'TM', 'UNDERPASS' , 'RAW_DATA')

    if dbIdentifier not in ALLOWED_SECTION_NAMES:
        print(f"Invalid dbIdentifier. Pick one of {ALLOWED_SECTION_NAMES}")
        return None
    try:
        connection_params = dict(config.items(dbIdentifier))
        return connection_params
    except Exception as ex :
        logging.error(f"""Can't find DB credentials on config :{dbIdentifier}""")
        return None