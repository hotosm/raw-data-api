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

# Standard library imports
import logging
import os
from configparser import ConfigParser
from distutils.util import strtobool

# Third party imports
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_bool_env_var(key, default=False):
    value = os.environ.get(key, default)
    return bool(strtobool(str(value)))


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

WORKER_PREFETCH_MULTIPLIER = int(
    os.environ.get("WORKER_PREFETCH_MULTIPLIER")
    or config.get("CELERY", "WORKER_PREFETCH_MULTIPLIER", fallback=1)
)

### API CONFIG BLOCK #######################

RATE_LIMIT_PER_MIN = os.environ.get("RATE_LIMIT_PER_MIN") or int(
    config.get("API_CONFIG", "RATE_LIMIT_PER_MIN", fallback=20)
)

RATE_LIMITER_STORAGE_URI = os.environ.get("RATE_LIMITER_STORAGE_URI") or config.get(
    "API_CONFIG", "RATE_LIMITER_STORAGE_URI", fallback="redis://localhost:6379"
)

EXPORT_MAX_AREA_SQKM = os.environ.get("EXPORT_MAX_AREA_SQKM") or int(
    config.get("API_CONFIG", "EXPORT_MAX_AREA_SQKM", fallback=100000)
)


INDEX_THRESHOLD = os.environ.get("INDEX_THRESHOLD") or int(
    config.get("API_CONFIG", "INDEX_THRESHOLD", fallback=5000)
)

MAX_WORKERS = os.environ.get("MAX_WORKERS") or config.get(
    "API_CONFIG", "MAX_WORKERS", fallback=os.cpu_count()
)

# get log level from config
LOG_LEVEL = os.environ.get("LOG_LEVEL") or config.get(
    "API_CONFIG", "LOG_LEVEL", fallback="debug"
)


def not_raises(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
        return True
    except Exception as ex:
        logging.error(ex)
        return False


####################

# EXPORT_UPLOAD CONFIG BLOCK
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


## Readme txt


logger = logging.getLogger("raw_data_api")

EXPORT_PATH = os.environ.get("EXPORT_PATH") or config.get(
    "API_CONFIG", "EXPORT_PATH", fallback="exports"
)

if not os.path.exists(EXPORT_PATH):
    # Create a exports directory because it does not exist
    os.makedirs(EXPORT_PATH)


DEFAULT_README_TEXT = """Exported through Raw-data-api (https://github.com/hotosm/raw-data-api) using OpenStreetMap data.\n Exports are made available under the Open Database License: http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual contents of the database are licensed under the Database Contents License: http://opendatacommons.org/licenses/dbcl/1.0/. \n Learn more about OpenStreetMap and its data usage policy : https://www.openstreetmap.org/about \n"""

EXTRA_README_TXT = os.environ.get("EXTRA_README_TXT") or config.get(
    "API_CONFIG", "EXTRA_README_TXT", fallback=""
)
DEFAULT_README_TEXT += EXTRA_README_TXT

ALLOW_BIND_ZIP_FILTER = get_bool_env_var(
    "ALLOW_BIND_ZIP_FILTER",
    config.getboolean("API_CONFIG", "ALLOW_BIND_ZIP_FILTER", fallback=False),
)

ENABLE_SOZIP = get_bool_env_var(
    "ENABLE_SOZIP",
    config.getboolean("API_CONFIG", "ENABLE_SOZIP", fallback=False),
)

ENABLE_TILES = get_bool_env_var(
    "ENABLE_TILES", config.getboolean("API_CONFIG", "ENABLE_TILES", fallback=False)
)

# check either to use connection pooling or not
USE_CONNECTION_POOLING = get_bool_env_var(
    "USE_CONNECTION_POOLING",
    config.getboolean("API_CONFIG", "USE_CONNECTION_POOLING", fallback=False),
)

# Queue

DEFAULT_QUEUE_NAME = os.environ.get("DEFAULT_QUEUE_NAME") or config.get(
    "API_CONFIG", "DEFAULT_QUEUE_NAME", fallback="raw_daemon"
)
ONDEMAND_QUEUE_NAME = os.environ.get("ONDEMAND_QUEUE_NAME") or config.get(
    "API_CONFIG", "ONDEMAND_QUEUE_NAME", fallback="raw_ondemand"
)

# Polygon statistics which will deliver the stats of approx buildings/ roads in the area

ENABLE_POLYGON_STATISTICS_ENDPOINTS = get_bool_env_var(
    "ENABLE_POLYGON_STATISTICS_ENDPOINTS",
    config.getboolean(
        "API_CONFIG", "ENABLE_POLYGON_STATISTICS_ENDPOINTS", fallback=False
    ),
)
POLYGON_STATISTICS_API_URL = os.environ.get("POLYGON_STATISTICS_API_URL") or config.get(
    "API_CONFIG", "POLYGON_STATISTICS_API_URL", fallback=None
)

POLYGON_STATISTICS_API_RATE_LIMIT = os.environ.get(
    "POLYGON_STATISTICS_API_RATE_LIMIT"
) or config.get("API_CONFIG", "POLYGON_STATISTICS_API_RATE_LIMIT", fallback=5)

# task limit

DEFAULT_SOFT_TASK_LIMIT = os.environ.get("DEFAULT_SOFT_TASK_LIMIT") or config.get(
    "API_CONFIG", "DEFAULT_SOFT_TASK_LIMIT", fallback=2 * 60 * 60
)
DEFAULT_HARD_TASK_LIMIT = os.environ.get("DEFAULT_HARD_TASK_LIMIT") or config.get(
    "API_CONFIG", "DEFAULT_HARD_TASK_LIMIT", fallback=3 * 60 * 60
)

# duckdb

USE_DUCK_DB_FOR_CUSTOM_EXPORTS = get_bool_env_var(
    "USE_DUCK_DB_FOR_CUSTOM_EXPORTS",
    config.getboolean("API_CONFIG", "USE_DUCK_DB_FOR_CUSTOM_EXPORTS", fallback=False),
)

logger.info(
    "USE_DUCK_DB_FOR_CUSTOM_EXPORTS %s ", USE_DUCK_DB_FOR_CUSTOM_EXPORTS is True
)

if USE_DUCK_DB_FOR_CUSTOM_EXPORTS:
    DUCK_DB_MEMORY_LIMIT = os.environ.get("DUCK_DB_MEMORY_LIMIT") or config.get(
        "API_CONFIG", "DUCK_DB_MEMORY_LIMIT", fallback=None
    )
    DUCK_DB_THREAD_LIMIT = os.environ.get("DUCK_DB_THREAD_LIMIT") or config.get(
        "API_CONFIG", "DUCK_DB_THREAD_LIMIT", fallback=None
    )

# hdx and custom exports
ENABLE_CUSTOM_EXPORTS = get_bool_env_var(
    "ENABLE_CUSTOM_EXPORTS",
    config.getboolean("API_CONFIG", "ENABLE_CUSTOM_EXPORTS", fallback=False),
)

HDX_SOFT_TASK_LIMIT = os.environ.get("HDX_SOFT_TASK_LIMIT") or config.get(
    "HDX", "HDX_SOFT_TASK_LIMIT", fallback=5 * 60 * 60
)
HDX_HARD_TASK_LIMIT = os.environ.get("HDX_HARD_TASK_LIMIT") or config.get(
    "HDX", "HDX_HARD_TASK_LIMIT", fallback=6 * 60 * 60
)

ENABLE_HDX_EXPORTS = get_bool_env_var(
    "ENABLE_HDX_EXPORTS", config.getboolean("HDX", "ENABLE_HDX_EXPORTS", fallback=False)
)

PROCESS_SINGLE_CATEGORY_IN_POSTGRES = get_bool_env_var(
    "PROCESS_SINGLE_CATEGORY_IN_POSTGRES",
    config.getboolean("HDX", "PROCESS_SINGLE_CATEGORY_IN_POSTGRES", fallback=False),
)

PARALLEL_PROCESSING_CATEGORIES = get_bool_env_var(
    "PARALLEL_PROCESSING_CATEGORIES",
    config.getboolean("HDX", "PARALLEL_PROCESSING_CATEGORIES", fallback=True),
)


if ENABLE_HDX_EXPORTS:
    try:
        hdx_credentials = os.environ["REMOTE_HDX"]

    except KeyError:
        logger.debug("EnvVar: REMOTE_HDX not supplied; Falling back to other means")
        HDX_SITE = os.environ.get("HDX_SITE") or config.get(
            "HDX", "HDX_SITE", fallback="demo"
        )
        HDX_API_KEY = os.environ.get("HDX_API_KEY") or config.get(
            "HDX", "HDX_API_KEY", fallback=None
        )
        HDX_OWNER_ORG = os.environ.get("HDX_OWNER_ORG") or config.get(
            "HDX", "HDX_OWNER_ORG", fallback="225b9f7d-e7cb-4156-96a6-44c9c58d31e3"
        )
        HDX_MAINTAINER = os.environ.get("HDX_MAINTAINER") or config.get(
            "HDX", "HDX_MAINTAINER", fallback=None
        )

    else:
        # Standard library imports
        import json

        hdx_credentials_json = json.loads(hdx_credentials)

        HDX_SITE = hdx_credentials_json["HDX_SITE"]
        HDX_API_KEY = hdx_credentials_json["HDX_API_KEY"]
        HDX_OWNER_ORG = hdx_credentials_json["HDX_OWNER_ORG"]
        HDX_MAINTAINER = hdx_credentials_json["HDX_MAINTAINER"]

        if None in (HDX_SITE, HDX_API_KEY, HDX_OWNER_ORG, HDX_MAINTAINER):
            raise ValueError("HDX Remote Credentials Malformed")

    # Third party imports
    from hdx.api.configuration import Configuration

    try:
        HDX_URL_PREFIX = Configuration.create(
            hdx_site=HDX_SITE,
            hdx_key=HDX_API_KEY,
            user_agent="HDXPythonLibrary/6.2.0-HOTOSM OSM Exports",
        )
        logging.debug(HDX_URL_PREFIX)
    except Exception as e:
        logging.error(
            "Error creating HDX configuration: %s, Disabling the hdx exports feature", e
        )
        ENABLE_HDX_EXPORTS = False

if ENABLE_HDX_EXPORTS:
    # Third party imports
    from hdx.data.dataset import Dataset
    from hdx.data.vocabulary import Vocabulary

    parse_list = lambda value, delimiter=",": (
        value.split(delimiter) if isinstance(value, str) else value or []
    )

    ALLOWED_HDX_TAGS = parse_list(
        os.environ.get("ALLOWED_HDX_TAGS")
        or config.get("HDX", "ALLOWED_HDX_TAGS", fallback=None)
        or (
            Vocabulary.approved_tags() if not_raises(Vocabulary.approved_tags) else None
        )
    )
    ALLOWED_HDX_UPDATE_FREQUENCIES = parse_list(
        os.environ.get("ALLOWED_HDX_UPDATE_FREQUENCIES")
        or config.get("HDX", "ALLOWED_HDX_UPDATE_FREQUENCIES", fallback=None)
        or (
            Dataset.list_valid_update_frequencies()
            if not_raises(Dataset.list_valid_update_frequencies)
            else None
        )
    )


def get_db_connection_params() -> dict:
    """Return a python dict that can be passed to psycopg2 connections
    to authenticate to Postgres Databases

    Returns: connection_params (dict): PostgreSQL connection parameters
             corresponding to the configuration section.

    """
    # This block fetches PostgreSQL (database) credentials passed as
    # environment variables as a JSON object, from AWS Secrets Manager or
    # Azure Key Vault.
    try:
        db_credentials = os.environ["REMOTE_DB"]

    except KeyError:
        logger.debug("EnvVar: REMOTE_DB not supplied; Falling back to other means")

        connection_params = dict(
            host=os.environ.get("PGHOST") or config.get("DB", "PGHOST"),
            port=os.environ.get("PGPORT")
            or config.get("DB", "PGPORT", fallback="5432"),
            dbname=os.environ.get("PGDATABASE") or config.get("DB", "PGDATABASE"),
            user=os.environ.get("PGUSER") or config.get("DB", "PGUSER"),
            password=os.environ.get("PGPASSWORD") or config.get("DB", "PGPASSWORD"),
        )

    else:
        # Standard library imports
        import json

        connection_params = json.loads(db_credentials)

        connection_params["user"] = connection_params["username"]
        for k in ("dbinstanceidentifier", "engine", "username"):
            connection_params.pop(k, None)

    if None in connection_params.values():
        raise ValueError(
            "Connection Params Value Error :  Couldn't be Loaded , Check DB Credentials"
        )
        logging.error(
            "Can't find database credentials , Either export them as env variable or include in config Block DB"
        )

    return connection_params


def get_oauth_credentials() -> tuple:
    """Get OAuth2 credentials from env file and return a config dict

    Return an ordered python tuple that can be passed to functions that
    authenticate to OSM.

    Order of precedence:
    1. Environment Variables
    2. Config File
    3. Default fallback

    Returns: oauth2_credentials (tuple): Tuple containing OAuth2 client
             secret, client ID, and redirect URL.

    """
    # This block fetches OSM OAuth2 app credentials passed as
    # environment variables as a JSON object, from AWS Secrets Manager or
    # Azure Key Vault.
    osm_url = os.environ.get("OSM_URL") or config.get(
        "OAUTH", "OSM_URL", fallback="https://www.openstreetmap.org"
    )
    secret_key = os.environ.get("APP_SECRET_KEY") or config.get(
        "OAUTH", "APP_SECRET_KEY"
    )

    try:
        oauth2_credentials = os.environ["REMOTE_OAUTH"]
    except KeyError:
        logger.debug("EnvVar: REMOTE_OAUTH not supplied; Falling back to other means")

        client_id = os.environ.get("OSM_CLIENT_ID") or config.get(
            "OAUTH", "OSM_CLIENT_ID"
        )
        client_secret = os.environ.get("OSM_CLIENT_SECRET") or config.get(
            "OAUTH", "OSM_CLIENT_SECRET"
        )
        login_redirect_uri = os.environ.get("LOGIN_REDIRECT_URI") or config.get(
            "OAUTH",
            "LOGIN_REDIRECT_URI",
            fallback="http://127.0.0.1:8000/v1/auth/callback",
        )
        scope = os.environ.get("OSM_PERMISSION_SCOPE") or config.get(
            "OAUTH", "OSM_PERMISSION_SCOPE", fallback="read_prefs"
        )

    else:
        # Standard library imports
        import json

        oauth2_credentials_json = json.loads(oauth2_credentials)

        client_id = oauth2_credentials_json["OSM_CLIENT_ID"]
        client_secret = oauth2_credentials_json["OSM_CLIENT_SECRET"]
        login_redirect_uri = oauth2_credentials_json["LOGIN_REDIRECT_URI"]
        scope = oauth2_credentials_json["OSM_PERMISSION_SCOPE"]

    oauth_cred = (
        osm_url,
        client_id,
        client_secret,
        secret_key,
        login_redirect_uri,
        scope,
    )

    if None in oauth_cred:
        raise ValueError("Oauth Credentials can't be loaded")

    return oauth_cred
