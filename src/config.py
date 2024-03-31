# Standard library imports
import os
from distutils.util import strtobool
from functools import lru_cache
from typing import Optional

# Third party imports
from dotenv import load_dotenv
from pydantic import (
    Field,
    PostgresDsn,
    ValidationInfo,
    field_validator,
    model_validator,
    root_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    """
    Base configuration class to handle environment variables
    and provide a common source for loading and validating settings.
    """

    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=".env", extra="allow", env_file_encoding="utf-8"
    )

    @classmethod
    def _load_env_(cls, info: ValidationInfo):
        """
        Load environment variables from the system or .env file.
        """
        # Load environment variables from the .env file if it exists
        load_dotenv(override=True)

        # Load environment variables from the system
        for key, value in os.environ.items():
            os.environ[key] = value

    @classmethod
    @root_validator(pre=True)
    def _load_environment_variables_(cls, values):
        """
        Load environment variables before validation.
        """
        cls._load_env_(ValidationInfo(values))
        return values

    @classmethod
    def _parse_env_value_(cls, value: str, info: ValidationInfo):
        """
        Parse environment variable value based on the field type.

        Args:
            value (str): The value to parse.
            info (ValidationInfo): The validation information for the field.

        Returns:
            The parsed value.
        """
        mode = info.mode
        if mode == "bool":
            return bool(strtobool(value))
        elif mode == "list":
            return [item.strip() for item in value.split(",")]
        else:
            return info.type_(value)


class CeleryConfig(BaseConfig):
    CELERY_BROKER_URL: str = Field(...)
    CELERY_RESULT_BACKEND: str = Field(...)
    WORKER_PREFETCH_MULTIPLIER: int = Field(1)


class CORSConfig(BaseConfig):
    ALLOWED_ORIGINS: Optional[str] = Field(None)
    ALLOW_CORS_CREDENTIALS: bool = Field(True)
    ALLOWED_CORS_METHODS: Optional[str] = Field(None)
    ALLOWED_CORS_HEADERS: Optional[str] = Field(None)

    @field_validator("ALLOWED_ORIGINS", mode="after")
    def parse_allowed_origins(cls, info: ValidationInfo):
        value = info.data.get("ALLOWED_ORIGINS")
        if value is None:
            return ["*"]
        return [origin.strip() for origin in value.split(",")]

    @field_validator("ALLOWED_CORS_METHODS", mode="after")
    def parse_allowed_methods(cls, info: ValidationInfo):
        value = info.data.get("ALLOWED_CORS_METHODS")
        if value is None:
            return ["*"]
        return [method.strip() for method in value.split(",")]

    @field_validator("ALLOWED_CORS_HEADERS", mode="after")
    def parse_allowed_headers(cls, info: ValidationInfo):
        value = info.data.get("ALLOWED_CORS_HEADERS")
        if value is None:
            return ["*"]
        return [header.strip() for header in value.split(",")]


class APIRateLimitConfig(BaseConfig):
    RATE_LIMIT_PER_MIN: int = Field(default=20)
    RATE_LIMITER_STORAGE_URI: str = Field(...)


class APIExportConfig(BaseConfig):
    EXPORT_MAX_AREA_SQKM: int = Field(100000)
    INDEX_THRESHOLD: int = Field(5000)
    EXPORT_PATH: str = Field("exports")
    EXTRA_README_TXT: str = Field("")
    ALLOW_NON_ZIPPED_EXPORTS: bool = Field(False)
    ENABLE_SOZIP: bool = Field(False)
    ENABLE_TILES: bool = Field(False)


class APIQueueConfig(BaseConfig):
    DEFAULT_QUEUE_NAME: str = Field("raw_daemon")
    ONDEMAND_QUEUE_NAME: str = Field("raw_ondemand")


class APIPolygonStatisticsConfig(BaseConfig):
    ENABLE_POLYGON_STATISTICS_ENDPOINTS: bool = Field(False)
    POLYGON_STATISTICS_API_URL: Optional[str] = Field(None)


class APITaskLimitConfig(BaseConfig):
    DEFAULT_SOFT_TASK_LIMIT: int = Field(2 * 60 * 60)
    DEFAULT_HARD_TASK_LIMIT: int = Field(3 * 60 * 60)
    ONDEMAND_SOFT_TASK_LIMIT: int = Field(5 * 60 * 60)
    ONDEMAND_HARD_TASK_LIMIT: int = Field(6 * 60 * 60)


class APIDuckDBConfig(BaseConfig):
    USE_DUCK_DB_FOR_CUSTOM_EXPORTS: bool = Field(False)
    DUCK_DB_MEMORY_LIMIT: Optional[str] = Field(None)
    DUCK_DB_THREAD_LIMIT: Optional[str] = Field(None)


class APICustomExportsConfig(BaseConfig):
    ENABLE_CUSTOM_EXPORTS: bool = Field(False)
    PROCESS_SINGLE_CATEGORY_IN_POSTGRES: bool = Field(False)
    PROCESS_CATEGORIES_IN_PARALLEL: bool = Field(True)


class APIConfig(BaseConfig):
    LOG_LEVEL: str = Field("debug")
    rate_limit: APIRateLimitConfig | None = None
    export: APIExportConfig | None = None
    cors: CORSConfig | None = None
    queue: APIQueueConfig | None = None
    polygon_statistics: APIPolygonStatisticsConfig | None = None
    task_limit: APITaskLimitConfig | None = None
    duckdb: APIDuckDBConfig | None = None
    custom_exports: APICustomExportsConfig | None = None


class HDXConfig(BaseConfig):
    ENABLE_HDX_EXPORTS: bool = False
    HDX_SITE: Optional[str] = Field(None)
    HDX_API_KEY: Optional[str] = Field(None)
    HDX_OWNER_ORG: Optional[str] = Field(None)
    HDX_MAINTAINER: Optional[str] = Field(None)
    ALLOWED_HDX_TAGS: Optional[list[str]] = Field(None)
    ALLOWED_HDX_UPDATE_FREQUENCIES: Optional[list[str]] = Field(None)

    @field_validator("ENABLE_HDX_EXPORTS", mode="after")
    def check_hdx_configs(cls, values, info: ValidationInfo):
        if info.data.get("ENABLE_HDX_EXPORTS"):
            required_fields = [
                "HDX_SITE",
                "HDX_API_KEY",
                "HDX_OWNER_ORG",
                "HDX_MAINTAINER",
            ]
            missing_fields = [
                field for field in required_fields if not field in info.data
            ]
            if missing_fields:
                raise ValueError(
                    f"The following fields are required when ENABLE_HDX_EXPORTS is True: {', '.join(missing_fields)}"
                )
        return values


class DatabaseConfig(BaseConfig):
    PGHOST: Optional[str] = None
    PGPORT: Optional[str] = None
    PGDATABASE: Optional[str] = None
    PGUSER: Optional[str] = None
    PGPASSWORD: Optional[str] = None
    REMOTE_DB: Optional[dict] = None
    POSTGRES_DSN: Optional[PostgresDsn] = None

    @property
    def connection_string(self) -> str:
        """Constructs and returns the PostgreSQL connection string."""
        if self.POSTGRES_DSN:
            return self.POSTGRES_DSN
        return f"postgresql://{self.PGUSER}:{self.PGPASSWORD}@{self.PGHOST}:{self.PGPORT}/{self.PGDATABASE}"

    @staticmethod
    def update_from_remote_db(values):
        """Update the values from the REMOTE_DB dict."""
        if values.get("REMOTE_DB"):
            remote_db = values["REMOTE_DB"]
            remote_db.pop("dbinstanceidentifier")
            remote_db.pop("engine")
            values["PGUSER"] = remote_db.pop("username", None)
            values.update(
                {
                    k.upper(): v
                    for k, v in remote_db.items()
                    if k.upper().startswith("PG")
                }
            )
        return values

    @root_validator(pre=True)
    def validate_database_config(cls, values):
        """
        Validate that at least one of the required fields is present and
        there is no duplication of fields.
        """
        required_fields = [
            "POSTGRES_DSN",
            "REMOTE_DB",
            ("PGHOST", "PGDATABASE", "PGPORT", "PGUSER", "PGPASSWORD"),
        ]
        present_fields = []
        for field in required_fields:
            if isinstance(field, str):
                if values.get(field) is not None:
                    present_fields.append(field)
            else:
                if all(values.get(f) is not None for f in field):
                    present_fields.append(field)

        if not present_fields:
            raise ValueError("At least one of the required fields must be present.")
        elif len(present_fields) > 1:
            raise ValueError("Only one of the required fields can be present.")

        if values.get("REMOTE_DB"):
            values = cls.update_from_remote_db(values)

        return values


class OAuthConfig(BaseConfig):
    OSM_URL: str = Field("https://www.openstreetmap.org")
    OSM_CLIENT_ID: Optional[str]
    OSM_CLIENT_SECRET: Optional[str]
    APP_SECRET_KEY: str
    LOGIN_REDIRECT_URI: str = Field("http://127.0.0.1:8000/v1/auth/callback")
    OSM_PERMISSION_SCOPE: str = Field("read_prefs")
    REMOTE_OAUTH: Optional[dict] = None

    @staticmethod
    def update_from_remote_oauth(values):
        if values.get("REMOTE_OAUTH"):
            oauth = values["REMOTE_OAUTH"]

            values.update(
                {k.upper(): v for k, v in oauth.items() if k.upper() != "OSM_URL"}
            )
        return values

    @root_validator(pre=True)
    def validate_oauth_config(cls, values):
        """
        Validate that at least one of the required fields is present and
        there is no duplication of fields.
        """
        required_fields = [
            "REMOTE_OAUTH",
            (
                "OSM_CLIENT_ID",
                "OSM_CLIENT_SECRET",
                "LOGIN_REDIRECT_URI",
                "OSM_PERMISSION_SCOPE",
            ),
        ]
        present_fields = []
        for field in required_fields:
            if isinstance(field, str):
                if values.get(field) is not None:
                    present_fields.append(field)
            else:
                if all(values.get(f) is not None for f in field):
                    present_fields.append(field)

        if not present_fields:
            raise ValueError("At least one of the required fields must be present.")
        elif len(present_fields) > 1:
            raise ValueError("Only one of the required fields can be present.")

        if values.get("REMOTE_OAUTH"):
            values = cls.update_from_remote_oauth(values)

        return values


class ExportUploadConfig(BaseConfig):
    FILE_UPLOAD_METHOD: str = Field("disk")
    BUCKET_NAME: Optional[str] = Field(None)
    AWS_ACCESS_KEY_ID: Optional[str] = Field(None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(None)

    @field_validator("FILE_UPLOAD_METHOD", mode="before")
    def validate_file_upload_method(cls, v):
        if v.lower() not in ["s3", "disk"]:
            raise ValueError("Value not supported for file_upload_method")
        return v


class SentryConfig(BaseConfig):
    SENTRY_DSN: Optional[str] = Field(None)
    SENTRY_RATE: Optional[str] = Field(None)


@lru_cache()
def get_settings(ask_for=None):
    """
    Retrieve configuration settings, optionally limited to specific configurations.

    This function caches the settings to avoid repeatedly loading them from the environment.
    If 'ask_for' is provided, only the requested configurations are returned.

    Args:
        ask_for (list, optional): A list of configuration names to retrieve. If None, all configurations are returned.

    Returns:
        tuple: A tuple containing instances of the requested configuration classes.
    """
    all_configs = {
        "celery": CeleryConfig(),
        "api": APIConfig(),
        "hdx": HDXConfig(),
        "db": DatabaseConfig(),
        "oauth": OAuthConfig(),
        "export_upload": ExportUploadConfig(),
        "sentry": SentryConfig(),
    }
    print(all_configs)

    if ask_for is None:
        #  return all
        return tuple(all_configs.values())
    else:
        return tuple(all_configs[name] for name in ask_for if name in all_configs)
