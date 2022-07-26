#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

from configparser import ConfigParser
import logging

CONFIG_FILE_PATH = "src/config.txt"

config = ConfigParser()
config.read(CONFIG_FILE_PATH)

log_level = config.get("API_CONFIG", "log_level",fallback=None) # get log level from config

if log_level is None or log_level.lower() == 'debug':  # default will go to debug
    level=logging.DEBUG 
elif log_level.lower() == 'info' :
    level=logging.INFO
elif log_level.lower() == 'error' :
    level= logging.ERROR
elif log_level.lower() == 'warning':
    level = logging.WARNING
else :
    logging.error("logging config is not supported , Supported fields are : debug,error,warning,info , Logging to default :debug")
    level = logging.DEBUG

logging.getLogger("fiona").propagate = False  # disable fiona logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=level)
logging.getLogger('boto3').propagate = False # disable boto3 logging

logger = logging.getLogger('galaxy')

export_path=config.get('API_CONFIG', 'export_path', fallback=None)
if export_path is None : 
    export_path = "exports/"
if export_path.endswith("/") is False : 
    export_path=f"""{export_path}/"""

AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY , BUCKET_NAME =None , None , None
#check either to use connection pooling or not 
use_connection_pooling = config.getboolean("API_CONFIG","use_connection_pooling", fallback=False)

#check either to use s3 raw data exports file uploading or not 
if  config.get("EXPORT_UPLOAD", "FILE_UPLOAD_METHOD",fallback=None).lower() == "s3" :
    use_s3_to_upload=True
    try :
        AWS_ACCESS_KEY_ID=config.get("EXPORT_UPLOAD", "AWS_ACCESS_KEY_ID") 
        AWS_SECRET_ACCESS_KEY=config.get("EXPORT_UPLOAD", "AWS_SECRET_ACCESS_KEY")
    except :
        logging.debug("No aws credentials supplied")
    BUCKET_NAME = config.get("EXPORT_UPLOAD", "BUCKET_NAME",fallback=None)
    if BUCKET_NAME is None : 
        BUCKET_NAME="exports-stage.hotosm.org" # default 
elif config.get("EXPORT_UPLOAD", "FILE_UPLOAD_METHOD",fallback=None).lower() == "disk":
    use_s3_to_upload=False
else:
    logging.error("value not supported for file_upload_method , switching to default disk method")
    use_s3_to_upload=False


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
        logging.error(f"Invalid dbIdentifier. Pick one of {ALLOWED_SECTION_NAMES}")
        return None
    try:
        connection_params = dict(config.items(dbIdentifier))
        return connection_params
    except Exception as ex :
        logging.error(f"""Can't find DB credentials on config :{dbIdentifier}""")
        return None