# Standard library imports
import os
from distutils.util import strtobool
from functools import lru_cache
from typing import Optional

# Third party imports
from pydantic_settings import BaseSettings, Field, validator


def get_bool_env_var(key, default=False):
    value = os.environ.get(key, default)
    return bool(strtobool(str(value)))


class CeleryConfig(BaseSettings):
    broker_url: str = Field(..., env="CELERY_BROKER_URL")
    result_backend: str = Field(..., env="CELERY_RESULT_BACKEND")
    worker_prefetch_multiplier: int = Field(1, env="WORKER_PREFETCH_MULTIPLIER")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "CELERY_"


class APIRateLimitConfig(BaseSettings):
    rate_limit_per_min: int = Field(20, env="RATE_LIMIT_PER_MIN")
    rate_limiter_storage_uri: str = Field(..., env="RATE_LIMITER_STORAGE_URI")


class APIExportConfig(BaseSettings):
    export_max_area_sqkm: int = Field(100000, env="EXPORT_MAX_AREA_SQKM")
    index_threshold: int = Field(5000, env="INDEX_THRESHOLD")
    export_path: str = Field("exports", env="EXPORT_PATH")
    extra_readme_txt: str = Field("", env="EXTRA_README_TXT")
    allow_bind_zip_filter: bool = Field(False, env="ALLOW_BIND_ZIP_FILTER")
    enable_sozip: bool = Field(False, env="ENABLE_SOZIP")
    enable_tiles: bool = Field(False, env="ENABLE_TILES")
    use_connection_pooling: bool = Field(False, env="USE_CONNECTION_POOLING")


class APIQueueConfig(BaseSettings):
    default_queue_name: str = Field("raw_daemon", env="DEFAULT_QUEUE_NAME")
    ondemand_queue_name: str = Field("raw_ondemand", env="ONDEMAND_QUEUE_NAME")


class APIPolygonStatisticsConfig(BaseSettings):
    enable_polygon_statistics_endpoints: bool = Field(
        False, env="ENABLE_POLYGON_STATISTICS_ENDPOINTS"
    )
    polygon_statistics_api_url: Optional[str] = Field(
        None, env="POLYGON_STATISTICS_API_URL"
    )
    polygon_statistics_api_rate_limit: int = Field(
        5, env="POLYGON_STATISTICS_API_RATE_LIMIT"
    )


class APITaskLimitConfig(BaseSettings):
    default_soft_task_limit: int = Field(2 * 60 * 60, env="DEFAULT_SOFT_TASK_LIMIT")
    default_hard_task_limit: int = Field(3 * 60 * 60, env="DEFAULT_HARD_TASK_LIMIT")


class APIDuckDBConfig(BaseSettings):
    use_duck_db_for_custom_exports: bool = Field(
        False, env="USE_DUCK_DB_FOR_CUSTOM_EXPORTS"
    )
    duck_db_memory_limit: Optional[str] = Field(None, env="DUCK_DB_MEMORY_LIMIT")
    duck_db_thread_limit: Optional[str] = Field(None, env="DUCK_DB_THREAD_LIMIT")


class APICustomExportsConfig(BaseSettings):
    enable_custom_exports: bool = Field(False, env="ENABLE_CUSTOM_EXPORTS")


class APIConfig(BaseSettings):
    log_level: str = Field("debug", env="LOG_LEVEL")
    rate_limit: APIRateLimitConfig
    export: APIExportConfig
    queue: APIQueueConfig
    polygon_statistics: APIPolygonStatisticsConfig
    task_limit: APITaskLimitConfig
    duckdb: APIDuckDBConfig
    custom_exports: APICustomExportsConfig

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "API_"


class HDXConfig(BaseSettings):
    enable_hdx_exports: bool = Field(False, env="ENABLE_HDX_EXPORTS")
    hdx_soft_task_limit: int = Field(5 * 60 * 60, env="HDX_SOFT_TASK_LIMIT")
    hdx_hard_task_limit: int = Field(6 * 60 * 60, env="HDX_HARD_TASK_LIMIT")
    process_single_category_in_postgres: bool = Field(
        False, env="PROCESS_SINGLE_CATEGORY_IN_POSTGRES"
    )
    parallel_processing_categories: bool = Field(
        True, env="PARALLEL_PROCESSING_CATEGORIES"
    )
    hdx_site: Optional[str] = Field(None, env="HDX_SITE")
    hdx_api_key: Optional[str] = Field(None, env="HDX_API_KEY")
    hdx_owner_org: str = Field(
        "225b9f7d-e7cb-4156-96a6-44c9c58d31e3", env="HDX_OWNER_ORG"
    )
    hdx_maintainer: Optional[str] = Field(None, env="HDX_MAINTAINER")
    allowed_hdx_tags: Optional[list[str]] = Field(None, env="ALLOWED_HDX_TAGS")
    allowed_hdx_update_frequencies: Optional[list[str]] = Field(
        None, env="ALLOWED_HDX_UPDATE_FREQUENCIES"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "HDX_"


class DatabaseConfig(BaseSettings):
    host: str
    port: str = Field("5432", env="PGPORT")
    dbname: str
    user: str
    password: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "PG_"

    @classmethod
    @lru_cache()
    def from_env(cls):
        try:
            db_credentials = os.environ["REMOTE_DB"]
            # Standard library imports
            import json

            connection_params = json.loads(db_credentials)
            connection_params["user"] = connection_params.pop("username")
            connection_params.pop("dbinstanceidentifier", None)
            connection_params.pop("engine", None)
            return cls(**connection_params)
        except KeyError:
            return cls()


class OAuthConfig(BaseSettings):
    osm_url: str = Field("https://www.openstreetmap.org", env="OSM_URL")
    app_secret_key: str
    client_id: Optional[str] = Field(None, env="OSM_CLIENT_ID")
    client_secret: Optional[str] = Field(None, env="OSM_CLIENT_SECRET")
    login_redirect_uri: str = Field(
        "http://127.0.0.1:8000/v1/auth/callback", env="LOGIN_REDIRECT_URI"
    )
    scope: str = Field("read_prefs", env="OSM_PERMISSION_SCOPE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "OAUTH_"

    @classmethod
    @lru_cache()
    def from_env(cls):
        try:
            oauth2_credentials = os.environ["REMOTE_OAUTH"]
            # Standard library imports
            import json

            oauth2_credentials_json = json.loads(oauth2_credentials)
            return cls(
                **{
                    k.lower(): v
                    for k, v in oauth2_credentials_json.items()
                    if k.lower() != "osm_url"
                }
            )
        except KeyError:
            return cls()


class ExportUploadConfig(BaseSettings):
    file_upload_method: str = Field("disk", env="FILE_UPLOAD_METHOD")
    bucket_name: Optional[str] = Field(None, env="BUCKET_NAME")
    aws_access_key_id: Optional[str] = Field(None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(None, env="AWS_SECRET_ACCESS_KEY")

    @validator("file_upload_method")
    def validate_file_upload_method(self, cls, v):
        if v.lower() not in ["s3", "disk"]:
            raise ValueError(
                "Value not supported for file_upload_method, switching to default disk method"
            )
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "EXPORT_UPLOAD_"


class SentryConfig(BaseSettings):
    sentry_dsn: Optional[str] = Field(None, env="SENTRY_DSN")
    sentry_rate: Optional[str] = Field(None, env="SENTRY_RATE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "SENTRY_"


@lru_cache()
def get_settings():
    celery_config = CeleryConfig()
    api_config = APIConfig()
    hdx_config = HDXConfig()
    db_config = DatabaseConfig.from_env()
    oauth_config = OAuthConfig.from_env()
    export_upload_config = ExportUploadConfig()
    sentry_config = SentryConfig()

    return (
        celery_config,
        api_config,
        hdx_config,
        db_config,
        oauth_config,
        export_upload_config,
        sentry_config,
    )


# Initialize rate limiter
# LIMITER = Limiter(key_func=get_remote_address, storage_uri=api_config.rate_limit.rate_limiter_storage_uri)

# Configure logging
# if api_config.log_level.lower() == "debug":
#     level = logging.DEBUG
# elif api_config.log_level.lower() == "info":
#     level = logging.INFO
# elif api_config.log_level.lower() == "
