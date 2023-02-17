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

import errno
import logging
import os
from configparser import ConfigParser

from slowapi import Limiter
from slowapi.util import get_remote_address

CONFIG_FILE_PATH = "config.txt"
USE_S3_TO_UPLOAD = False
AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, BUCKET_NAME = None, None, None


config = ConfigParser()
config.read(CONFIG_FILE_PATH)


### CELERY BLOCK ####################
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL") or config.get(
    "CELERY", "CELERY_BROKER_URL", fallback="redis://localhost:6379"
)
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND") or config.get(
    "CELERY", "CELERY_RESULT_BACKEND", fallback="redis://localhost:6379"
)

### API CONFIG BLOCK #######################

RATE_LIMIT_PER_MIN = os.environ.get("RATE_LIMIT_PER_MIN") or int(
    config.get("API_CONFIG", "RATE_LIMIT_PER_MIN", fallback=5)
)

RATE_LIMITER_STORAGE_URI = os.environ.get("RATE_LIMITER_STORAGE_URI") or config.get(
    "API_CONFIG", "RATE_LIMITER_STORAGE_URI", fallback="redis://localhost:6379"
)

EXPORT_MAX_AREA_SQKM = os.environ.get("EXPORT_MAX_AREA_SQKM") or int(
    config.get("API_CONFIG", "EXPORT_MAX_AREA_SQKM", fallback=100000)
)


GRID_INDEX_THRESHOLD = os.environ.get("GRID_INDEX_THRESHOLD") or int(
    config.get("API_CONFIG", "GRID_INDEX_THRESHOLD", fallback=5000)
)

# get log level from config
LOG_LEVEL = os.environ.get("LOG_LEVEL") or config.get(
    "API_CONFIG", "LOG_LEVEL", fallback="debug"
)

ALLOW_BIND_ZIP_FILTER = os.environ.get("ALLOW_BIND_ZIP_FILTER") or config.get(
    "API_CONFIG", "ALLOW_BIND_ZIP_FILTER", fallback=None
)

####################

### EXPORT_UPLOAD CONFIG BLOCK
FILE_UPLOAD_METHOD = os.environ.get("FILE_UPLOAD_METHOD") or config.get(
    "EXPORT_UPLOAD", "FILE_UPLOAD_METHOD", fallback="disk"
)


if FILE_UPLOAD_METHOD.lower() not in ["s3", "disk"]:
    logging.error(
        "value not supported for file_upload_method ,switching to default disk method"
    )
    USE_S3_TO_UPLOAD = False

if FILE_UPLOAD_METHOD.lower() == "s3":
    USE_S3_TO_UPLOAD = True
    BUCKET_NAME = os.environ.get("BUCKET_NAME") or config.get(
        "EXPORT_UPLOAD", "BUCKET_NAME"
    )
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID") or config.get(
        "EXPORT_UPLOAD", "AWS_ACCESS_KEY_ID", fallback=None
    )
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY") or config.get(
        "EXPORT_UPLOAD", "AWS_SECRET_ACCESS_KEY", fallback=None
    )
    if not BUCKET_NAME:
        raise ValueError("Value of BUCKET_NAME couldn't found")

##################

## SENTRY BLOCK ########
SENTRY_DSN = os.environ.get("SENTRY_DSN") or config.get(
    "SENTRY", "SENTRY_DSN", fallback=None
)
SENTRY_RATE = os.environ.get("SENTRY_RATE") or config.get(
    "SENTRY", "SENTRY_RATE", fallback=None
)

# rate limiter for API requests based on the remote ip address and redis as backend
LIMITER = Limiter(key_func=get_remote_address, storage_uri=RATE_LIMITER_STORAGE_URI)


if LOG_LEVEL.lower() == "debug":  # default debug
    level = logging.DEBUG
elif LOG_LEVEL.lower() == "info":
    level = logging.INFO
elif LOG_LEVEL.lower() == "error":
    level = logging.ERROR
elif LOG_LEVEL.lower() == "warning":
    level = logging.WARNING
else:
    logging.error(
        "logging config is not supported , Supported fields are : debug,error,warning,info , Logging to default :debug"
    )
    level = logging.DEBUG

# logging.getLogger("fiona").propagate = False  # disable fiona logging
logging.basicConfig(format="%(asctime)s - %(message)s", level=level)
logging.getLogger("boto3").propagate = False  # disable boto3 logging
logging.getLogger("botocore").propagate = False  # disable boto3 logging
logging.getLogger("s3transfer").propagate = False  # disable boto3 logging
logging.getLogger("boto").propagate = False  # disable boto3 logging


logger = logging.getLogger("raw_data_api")

EXPORT_PATH = os.environ.get("EXPORT_PATH") or config.get(
    "API_CONFIG", "EXPORT_PATH", fallback="exports"
)

if not os.path.exists(EXPORT_PATH):
    # Create a exports directory because it does not exist
    os.makedirs(EXPORT_PATH)
ALLOW_BIND_ZIP_FILTER = os.environ.get("ALLOW_BIND_ZIP_FILTER") or config.getboolean(
    "API_CONFIG", "ALLOW_BIND_ZIP_FILTER", fallback=False
)

# check either to use connection pooling or not
USE_CONNECTION_POOLING = os.environ.get("USE_CONNECTION_POOLING") or config.getboolean(
    "API_CONFIG", "USE_CONNECTION_POOLING", fallback=False
)


def get_db_connection_params() -> dict:
    """Return a python dict that can be passed to psycopg2 connections
    to authenticate to Postgres Databases


    Returns: connection_params (dict): PostgreSQL connection parameters
             corresponding to the configuration section.

    """
    try:
        connection_params = {
            "host": os.environ.get("PGHOST") or config.get("DB", "PGHOST"),
            "port": os.environ.get("PGPORT") or config.get("DB", "PGPORT"),
            "dbname": os.environ.get("PGDATABASE") or config.get("DB", "PGDATABASE"),
            "user": os.environ.get("PGUSER") or config.get("DB", "PGUSER"),
            "password": os.environ.get("PGPASSWORD") or config.get("DB", "PGPASSWORD"),
        }
        if any(value is None for value in connection_params.values()):
            raise ValueError(
                "Connection Params Value Error :  Couldn't be Loaded , Check DB Credentials"
            )
    except Exception as ex:
        logging.error(
            "Can't find database credentials , Either export them as env variable or include in config Block DB"
        )
        raise ex
    return connection_params


def get_oauth_credentials() -> tuple:
    """Gets oauth credentials from the env file and returns a config dict"""
    osm_url = os.environ.get("OSM_URL") or config.get("OAUTH", "OSM_URL")
    client_id = os.environ.get("OSM_CLIENT_ID") or config.get("OAUTH", "OSM_CLIENT_ID")
    client_secret = os.environ.get("OSM_CLIENT_SECRET") or config.get(
        "OAUTH", "OSM_CLIENT_SECRET"
    )
    secret_key = os.environ.get("APP_SECRET_KEY") or config.get(
        "OAUTH", "APP_SECRET_KEY"
    )
    login_redirect_uri = os.environ.get("LOGIN_REDIRECT_URI") or config.get(
        "OAUTH", "LOGIN_REDIRECT_URI"
    )
    scope = os.environ.get("OSM_PERMISSION_SCOPE") or config.get(
        "OAUTH", "OSM_PERMISSION_SCOPE"
    )
    oauth_cred = (
        osm_url,
        client_id,
        client_secret,
        secret_key,
        login_redirect_uri,
        scope,
    )
    if any(item is None for item in oauth_cred):
        raise ValueError("Oauth Credentials can't be loaded")

    return oauth_cred
