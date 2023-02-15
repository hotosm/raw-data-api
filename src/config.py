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

if os.path.exists(CONFIG_FILE_PATH) is False:
    logging.error(
        FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), CONFIG_FILE_PATH)
    )

config = ConfigParser()
config.read(CONFIG_FILE_PATH)


### CELERY BLOCK ####################
CELERY_BROKER_URL = config.get(
    "CELERY",
    "CELERY_BROKER_URL",
    fallback=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379"),
)
CELERY_RESULT_BACKEND = config.get(
    "CELERY",
    "CELERY_RESULT_BACKEND",
    fallback=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379"),
)

### API CONFIG BLOCK #######################

RATE_LIMIT_PER_MIN = int(
    config.get(
        "API_CONFIG",
        "RATE_LIMIT_PER_MIN",
        fallback=os.environ.get("RATE_LIMIT_PER_MIN", 5),
    )
)

RATE_LIMITER_STORAGE_URI = config.get(
    "API_CONFIG",
    "RATE_LIMITER_STORAGE_URI",
    fallback=os.environ.get("RATE_LIMITER_STORAGE_URI", "redis://localhost:6379"),
)

EXPORT_MAX_AREA_SQKM = os.environ.get(
    "EXPORT_MAX_AREA_SQKM",
    int(
        config.get(
            "API_CONFIG",
            "EXPORT_MAX_AREA_SQKM",
            fallback=os.environ.get("EXPORT_MAX_AREA_SQKM", 100000),
        )
    ),
)

GRID_INDEX_THRESHOLD = int(
    config.get(
        "API_CONFIG", "GRID_INDEX_THRESHOLD", fallback=os.environ.get("LOG_LEVEL", 5000)
    )
)

# get log level from config
LOG_LEVEL = config.get(
    "API_CONFIG", "LOG_LEVEL", fallback=os.environ.get("LOG_LEVEL", "debug")
)

ALLOW_BIND_ZIP_FILTER = config.get(
    "API_CONFIG",
    "ALLOW_BIND_ZIP_FILTER",
    fallback=os.environ.get("ALLOW_BIND_ZIP_FILTER", None),
)

####################

### EXPORT_UPLOAD CONFIG BLOCK
FILE_UPLOAD_METHOD = config.get(
    "EXPORT_UPLOAD",
    "FILE_UPLOAD_METHOD",
    fallback=os.environ.get("FILE_UPLOAD_METHOD", "disk"),
).lower()


if FILE_UPLOAD_METHOD not in ["s3", "disk"]:
    logging.error(
        "value not supported for file_upload_method ,switching to default disk method"
    )
    USE_S3_TO_UPLOAD = False

if FILE_UPLOAD_METHOD == "s3":
    USE_S3_TO_UPLOAD = True
    BUCKET_NAME = config.get(
        "EXPORT_UPLOAD", "BUCKET_NAME", fallback=os.environ.get("BUCKET_NAME")
    )
    if not BUCKET_NAME:
        raise ValueError("Value of BUCKET_NAME couldn't found")

##################

## SENTRY BLOCK ########
SENTRY_DSN = os.environ.get(
    "SENTRY_DSN",
    config.get("SENTRY", "SENTRY_DSN", fallback=os.environ.get("SENTRY_DSN", None)),
)
SENTRY_RATE = os.environ.get(
    "SENTRY_RATE",
    config.get("SENTRY", "SENTRY_RATE", fallback=os.environ.get("SENTRY_RATE", None)),
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

EXPORT_PATH = config.get(
    "API_CONFIG", "EXPORT_PATH", fallback=os.environ.get("EXPORT_PATH", "exports")
)

if not os.path.exists(EXPORT_PATH):
    # Create a exports directory because it does not exist
    os.makedirs(EXPORT_PATH)
ALLOW_BIND_ZIP_FILTER = config.get(
    "API_CONFIG",
    "ALLOW_BIND_ZIP_FILTER",
    fallback=os.environ.get("ALLOW_BIND_ZIP_FILTER", None),
)
if ALLOW_BIND_ZIP_FILTER:
    ALLOW_BIND_ZIP_FILTER = True if ALLOW_BIND_ZIP_FILTER.lower() == "true" else False

AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, BUCKET_NAME = None, None, None
# check either to use connection pooling or not
USE_CONNECTION_POOLING = config.getboolean(
    "API_CONFIG",
    "USE_CONNECTION_POOLING",
    fallback=os.environ.get("USE_CONNECTION_POOLING", False),
)


def get_db_connection_params() -> dict:
    """Return a python dict that can be passed to psycopg2 connections
    to authenticate to Postgres Databases


    Returns: connection_params (dict): PostgreSQL connection parameters
             corresponding to the configuration section.

    """
    try:
        connection_params = {
            "host": config.get("DB", "PGHOST", fallback=os.environ.get("PGHOST")),
            "port": config.get("DB", "PGPORT", fallback=os.environ.get("PGPORT")),
            "dbname": config.get(
                "DB", "PGDATABASE", fallback=os.environ.get("PGDATABASE")
            ),
            "user": config.get("DB", "PGUSER", fallback=os.environ.get("PGUSER")),
            "password": config.get(
                "DB", "PGPASSWORD", fallback=os.environ.get("PGPASSWORD")
            ),
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
    osm_url = config.get("OAUTH", "OSM_URL", fallback=os.environ.get("OSM_URL"))

    osm_url = config.get("OAUTH", "OSM_URL", fallback=os.environ.get("OSM_URL"))
    client_id = config.get(
        "OAUTH", "OSM_CLIENT_ID", fallback=os.environ.get("OSM_CLIENT_ID")
    )
    client_secret = config.get(
        "OAUTH", "OSM_CLIENT_SECRET", fallback=os.environ.get("OSM_CLIENT_SECRET")
    )
    secret_key = config.get(
        "OAUTH", "APP_SECRET_KEY", fallback=os.environ.get("APP_SECRET_KEY")
    )
    login_redirect_uri = config.get(
        "OAUTH", "LOGIN_REDIRECT_URI", fallback=os.environ.get("LOGIN_REDIRECT_URI")
    )
    scope = config.get(
        "OAUTH", "OSM_PERMISSION_SCOPE", fallback=os.environ.get("OSM_PERMISSION_SCOPE")
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
