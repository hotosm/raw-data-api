
# Configuring the API service

Raw Data API can be setup using two configuration options. You can choose based on your convenience 
- *config.txt* : You can follow  `config.txt.sample` in dir and documentation below to set your configurations 
- *.env* : Another option is from OS Environment variable, You can export all your env variables (They are same as you put in config without blocks) and pass it to API, API will pick it up automatically.

## What you need to start?

- A working [Postgres](https://www.postgresql.org/) instance with [Postgis](https://postgis.net/) module enabled.
- A working [Redis](https://redis.io/) instance.

The default configuration file is an ini-style text file named `config.txt` in the project root.

## Users Table

Users table is present on ```backend/sql/users.sql``` Make sure you have it before moving forward

```
psql -a -f backend/sql/users.sql
```
& Add your admin's OSM ID as admin 

```
INSERT INTO users (osm_id, role) VALUES (1234, 1);
```

## Sections

The following sections are recognised.

- `[DB]` - For database connection information. Required.
- `[OAUTH]` - For connecting to OpenStreetMap using an OAuth2 app. Required.
- `[CELERY]` - For task queues on Redis. Required.
- `[API_CONFIG]` - API service related configuration. Required.
- `[EXPORT_UPLOAD]` - For external file hosts like S3. Optional.
- `[SENTRY]` - Sentry monitoring configuration. Optional.
- `[HDX]` - HDX Exports related configuration. Optional.

The following are the different configuration options that are accepted.

| Config option | ENVVAR | Section | Defaults | Description | Required? |
|---------------|---------|----------|--------|-------------|-----------|
| `PGHOST` | `PGHOST` | `[DB]` | _none_  | PostgreSQL hostname or IP | REQUIRED |
| `PGPORT` | `PGPORT` | `[DB]` | `5432` | PostgreSQL connection port | OPTIONAL |
| `PGUSER` | `PGUSER` | `[DB]` | _none_ | PostgreSQL user/role | REQUIRED |
| `PGPASSWORD` | `PGPASSWORD` | `[DB]` | _none_ | PostgreSQL user/role password | REQUIRED |
| `PGDATABASE` | `PGDATABASE` | `[DB]` | _none_ | PostgreSQL database name | REQUIRED |
| `OSM_CLIENT_ID` | `OSM_CLIENT_ID` | `[OAUTH]` | _none_ | Client ID of OSM OAuth2 application | REQIRED |
| `OSM_CLIENT_SECRET` | `OSM_CLIENT_SECRET` | `[OAUTH]` | _none_ | Client Secret of OSM OAuth2 application | REQUIRED |
| `OSM_PERMISSION_SCOPE` | `OSM_PERMISSION_SCOPE` | `[OAUTH]` | `read_prefs` | OSM access permission for OAuth2 application | OPTIONAL |
| `LOGIN_REDIRECT_URI` | `LOGIN_REDIRECT_URI` | `[OAUTH]` | _none_ | Redirect URL set in the OAuth2 application | REQUIRED |
| `APP_SECRET_KEY` | `APP_SECRET_KEY` | `[OAUTH]` | _none_ | High-entropy string generated for the application | REQUIRED |
| `OSM_URL` | `OSM_URL` | `[OAUTH]` | `https://www.openstreetmap.org` | OSM instance Base URL | OPTIONAL |
| `LOG_LEVEL` | `LOG_LEVEL` | `[API_CONFIG]` | `debug` | Application log level; info,debug,warning,error | OPTIONAL |
| `RATE_LIMITER_STORAGE_URI` | `RATE_LIMITER_STORAGE_URI` | `[API_CONFIG]` | `redis://redis:6379` | Redis connection string for rate-limiter data | OPTIONAL |
| `RATE_LIMIT_PER_MIN` | `RATE_LIMIT_PER_MIN` | `[API_CONFIG]` | `5` | Number of requests per minute before being rate limited | OPTIONAL |
| `EXPORT_PATH` | `EXPORT_PATH` | `[API_CONFIG]` | `exports`? |  Local path to store exports | OPTIONAL |
| `EXPORT_MAX_AREA_SQKM` | `EXPORT_MAX_AREA_SQKM` | `[API_CONFIG]` | `100000` | max area in sq. km. to support for rawdata input | OPTIONAL |
| `USE_CONNECTION_POOLING` | `USE_CONNECTION_POOLING` | `[API_CONFIG]` | `false` | Enable psycopg2 connection pooling | OPTIONAL |
| `ALLOW_BIND_ZIP_FILTER` | `ALLOW_BIND_ZIP_FILTER` | `[API_CONFIG]` | `true` | Enable zip compression for exports | OPTIONAL |
| `EXTRA_README_TXT` | `EXTRA_README_TXT` | `[API_CONFIG]` | `` | Append extra string to export readme.txt | OPTIONAL |
| `ENABLE_TILES` | `ENABLE_TILES` | `[API_CONFIG]` | `false` | Enable Tile Output (Pmtiles and Mbtiles) | OPTIONAL |
| `ENABLE_SOZIP` | `ENABLE_SOZIP` | `[API_CONFIG]` | `false` | Enables sozip compression | OPTIONAL |
| `DEFAULT_QUEUE_NAME` | `DEFAULT_QUEUE_NAME` | `[API_CONFIG]` | `raw_daemon` | Option to define default queue name| OPTIONAL |
| `ONDEMAND_QUEUE_NAME` | `ONDEMAND_QUEUE_NAME` | `[API_CONFIG]` | `raw_ondemand` | Option to define daemon queue name for scheduled and long exports | OPTIONAL |
| `ENABLE_POLYGON_STATISTICS_ENDPOINTS` | `ENABLE_POLYGON_STATISTICS_ENDPOINTS` | `[API_CONFIG]` | `False` | Option to enable endpoints related the polygon statistics about the approx buildings,road length in passed polygon| OPTIONAL |
| `ENABLE_CUSTOM_EXPORTS` | `ENABLE_CUSTOM_EXPORTS` | `[API_CONFIG]` | False | Enables custom exports endpoint and imports | OPTIONAL |
| `POLYGON_STATISTICS_API_URL` | `POLYGON_STATISTICS_API_URL` | `[API_CONFIG]` | `None` | API URL for the polygon statistics to fetch the metadata , Currently tested with graphql query endpoint of Kontour , Only required if it is enabled from ENABLE_POLYGON_STATISTICS_ENDPOINTS | OPTIONAL |
| `POLYGON_STATISTICS_API_URL` | `POLYGON_STATISTICS_API_RATE_LIMIT` | `[API_CONFIG]` | `5` | Rate limit to be applied for statistics endpoint per minute, Defaults to 5 request is allowed per minute | OPTIONAL |
| `WORKER_PREFETCH_MULTIPLIER` | `WORKER_PREFETCH_MULTIPLIER` | `[CELERY]` | `1` | No of tasks that worker can prefetch at a time | OPTIONAL |
| `DEFAULT_SOFT_TASK_LIMIT` | `DEFAULT_SOFT_TASK_LIMIT` | `[API_CONFIG]` | `7200` | Soft task time limit signal for celery workers in seconds.It will gently remind celery to finish up the task and terminate, Defaults to 2 Hour| OPTIONAL |
| `DEFAULT_HARD_TASK_LIMIT` | `DEFAULT_HARD_TASK_LIMIT` | `[API_CONFIG]` | `10800` | Hard task time limit signal for celery workers in seconds. It will immediately kill the celery task.Defaults to 3 Hour| OPTIONAL |
| `USE_DUCK_DB_FOR_CUSTOM_EXPORTS` | `USE_DUCK_DB_FOR_CUSTOM_EXPORTS` | `[API_CONFIG]` | `False` | Enable this setting to use duckdb , By default duck db is disabled and postgres is used| OPTIONAL |
| `CELERY_BROKER_URL` | `CELERY_BROKER_URL` | `[CELERY]` | `redis://localhost:6379/0` | Redis connection string for the broker | OPTIONAL |
| `CELERY_RESULT_BACKEND` | `CELERY_RESULT_BACKEND` | `[CELERY]` | `redis://localhost:6379/0` | Redis/psotgresql connection string for the result backend, eg : db+postgresql://username:password@localhost:5432/db_name  | OPTIONAL |
| `FILE_UPLOAD_METHOD` | `FILE_UPLOAD_METHOD` | `[EXPORT_UPLOAD]` | `disk` | File upload method; Allowed values - disk, s3 | OPTIONAL |
| `BUCKET_NAME` | `BUCKET_NAME` | `[EXPORT_UPLOAD]` | _none_ | AWS S3 Bucket name | CONDITIONAL |
| `AWS_ACCESS_KEY_ID` | `AWS_ACCESS_KEY_ID` | `[EXPORT_UPLOAD]` | _none_ | AWS Access Key ID for S3 access | CONDITIONAL |
| `AWS_SECRET_ACCESS_KEY` | `AWS_SECRET_ACCESS_KEY` | `[EXPORT_UPLOAD]` | _none_ | AWS Secret Access Key for S3 access | CONDITIONAL |
| `SENTRY_DSN` | `SENTRY_DSN` | `[SENTRY]` | _none_ | Sentry Data Source Name | OPTIONAL |
| `SENTRY_RATE` | `SENTRY_RATE` | `[SENTRY]` | `1.0` | Sample rate percentage for shipping errors to sentry; Allowed values between 0 (0%) to 1 (100%)| OPTIONAL |
| `ENABLE_HDX_EXPORTS` | `ENABLE_HDX_EXPORTS` | `[HDX]` | False | Enables hdx related endpoints and imports | OPTIONAL |
| `HDX_SITE` | `HDX_SITE` | `[HDX]` | 'demo' | HDX site to point , By default demo site , use prod for production | CONDITIONAL |
| `HDX_API_KEY` | `HDX_API_KEY` | `[HDX]` | None | Your API Secret key for hdx upload , should have write access and it is compulsory if ENABLE_HDX_EXPORTS is True | CONDITIONAL |
| `HDX_OWNER_ORG` | `HDX_OWNER_ORG` | `[HDX]` | None | Your HDX organization ID| CONDITIONAL |
| `HDX_MAINTAINER` | `HDX_MAINTAINER` | `[HDX]` | None | Your HDX Maintainer ID | CONDITIONAL |
| `DUCK_DB_MEMORY_LIMIT` | `DUCK_DB_MEMORY_LIMIT` | `[API_CONFIG]` | None | Duck DB max memory limit , 80 % of your RAM eg : '5GB'| CONDITIONAL |
| `DUCK_DB_THREAD_LIMIT` | `DUCK_DB_THREAD_LIMIT` | `[API_CONFIG]` | None | Duck DB max threads limit ,n of your cores eg : 2 | CONDITIONAL |
| `HDX_SOFT_TASK_LIMIT` | `HDX_SOFT_TASK_LIMIT` | `[HDX]` | `18000` | Soft task time limit signal for celery workers in seconds.It will gently remind celery to finish up the task and terminate, Defaults to 5 Hour| OPTIONAL |
| `HDX_HARD_TASK_LIMIT` | `HDX_HARD_TASK_LIMIT` | `[HDX]` | `21600` | Hard task time limit signal for celery workers in seconds. It will immediately kill the celery task.Defaults to 6 Hour| OPTIONAL |
| `PROCESS_SINGLE_CATEGORY_IN_POSTGRES` | `PROCESS_SINGLE_CATEGORY_IN_POSTGRES` | `[HDX]` | False | Recommended for workers with low memory or CPU usage, This will process single category request like buildings only, Roads only in postgres itself and avoid extraction from duckdb| OPTIONAL |
| `PARALLEL_PROCESSING_CATEGORIES` | `PARALLEL_PROCESSING_CATEGORIES` | `[HDX]` | True | Enable parallel processing for multiple categories and export formats , Disable this if you have single cpu and limited RAM , Enabled by default| OPTIONAL |

**Note :** HDX_API_KEY 

In order to generate HDX_API_KEY , You need to be logged in to https://data.humdata.org/ .
Follow the following navigation to generate tokens: 
  - Your profile section > User settings > API Tokens

API Tokens have expiry date, It is `important to update API Tokens manually each year` for hosted api service ! 

## Which Service uses which settings?

| Parameter | Config Section | API | Worker |
|-----------|----------------|-----|--------|
| `PGHOST` | `[DB]` | Yes | Yes |
| `PGPORT` | `[DB]` | Yes | Yes |
| `PGUSER` | `[DB]` | Yes | Yes |
| `PGPASSWORD` | `[DB]` | Yes | Yes |
| `PGDATABASE` | `[DB]` | Yes | Yes |
| `OSM_CLIENT_ID` | `[OAUTH]` | Yes | No |
| `OSM_CLIENT_SECRET` | `[OAUTH]` | Yes | No |
| `OSM_PERMISSION_SCOPE` | `[OAUTH]` | Yes | No |
| `LOGIN_REDIRECT_URI` | `[OAUTH]` | Yes | No |
| `APP_SECRET_KEY` | `[OAUTH]` | Yes | No |
| `OSM_URL` | `[OAUTH]` | Yes | No |
| `LOG_LEVEL` | `[API_CONFIG]` | Yes | Yes |
| `RATE_LIMITER_STORAGE_URI` | `[API_CONFIG]` | Yes | No |
| `RATE_LIMIT_PER_MIN` | `[API_CONFIG]` | Yes | No |
| `EXPORT_PATH` | `[API_CONFIG]` | Yes (Not needed for upload_s3) | Yes |
| `EXPORT_MAX_AREA_SQKM` | `[API_CONFIG]` | Yes | No |
| `USE_CONNECTION_POOLING` | `[API_CONFIG]` | Yes | Yes |
| `ENABLE_TILES` | `[API_CONFIG]` | Yes | Yes |
| `ENABLE_SOZIP` | `[API_CONFIG]` | Yes | Yes |
| `ALLOW_BIND_ZIP_FILTER` | `[API_CONFIG]` | Yes | Yes |
| `EXTRA_README_TXT` | `[API_CONFIG]` | No | Yes |
| `INDEX_THRESHOLD` | `[API_CONFIG]` | No | Yes |
| `DEFAULT_QUEUE_NAME` | `[API_CONFIG]` | Yes | No |
| `ONDEMAND_QUEUE_NAME` | `[API_CONFIG]` | Yes | No |
| `ENABLE_POLYGON_STATISTICS_ENDPOINTS` | `[API_CONFIG]` | Yes | Yes |
| `POLYGON_STATISTICS_API_URL` | `[API_CONFIG]` | Yes | Yes |
| `POLYGON_STATISTICS_API_RATE_LIMIT` | `[API_CONFIG]` | Yes | No |
| `DEFAULT_SOFT_TASK_LIMIT` | `[API_CONFIG]` | No | Yes |
| `DEFAULT_HARD_TASK_LIMIT` | `[API_CONFIG]` | No | Yes |
| `USE_DUCK_DB_FOR_CUSTOM_EXPORTS` | `[API_CONFIG]` | Yes | Yes |
| `DUCK_DB_MEMORY_LIMIT` | `[API_CONFIG]` | Yes | Yes |
| `DUCK_DB_THREAD_LIMIT` | `[API_CONFIG]` | Yes | Yes |
| `ENABLE_CUSTOM_EXPORTS` | `[API_CONFIG]` | Yes | Yes |
| `CELERY_BROKER_URL` | `[CELERY]` | Yes | Yes |
| `CELERY_RESULT_BACKEND` | `[CELERY]` | Yes | Yes |
| `WORKER_PREFETCH_MULTIPLIER` | `[CELERY]` | Yes | Yes |
| `FILE_UPLOAD_METHOD` | `[EXPORT_UPLOAD]` | Yes | Yes |
| `BUCKET_NAME` | `[EXPORT_UPLOAD]` | Yes | Yes |
| `AWS_ACCESS_KEY_ID` | `[EXPORT_UPLOAD]` | Yes | Yes |
| `AWS_SECRET_ACCESS_KEY` | `[EXPORT_UPLOAD]` | Yes | Yes |
| `SENTRY_DSN` | `[SENTRY]` | Yes | No |
| `SENTRY_RATE` | `[SENTRY]` | Yes | No |
| `ENABLE_HDX_EXPORTS` | `[HDX]` | Yes | Yes |
| `HDX_SITE` | `[HDX]` | Yes | Yes |
| `HDX_API_KEY` | `[HDX]` | Yes | Yes |
| `HDX_OWNER_ORG` | `[HDX]` | Yes | Yes |
| `HDX_MAINTAINER` | `[HDX]` | Yes | Yes |
| `HDX_SOFT_TASK_LIMIT` | `[HDX]` | No | Yes |
| `HDX_HARD_TASK_LIMIT` | `[HDX]` | No | Yes |
| `PROCESS_SINGLE_CATEGORY_IN_POSTGRES` | `[HDX]` | No | Yes |
| `PARALLEL_PROCESSING_CATEGORIES` | `[HDX]` | No | Yes |



## Compulsory Configuration

### Create `config.txt` inside root directory.

It should be on the same place where `config.txt.sample`

### Prepare your OSM Snapshot Data

Initialize rawdata from [here](https://github.com/hotosm/underpass/tree/master/raw) OR Create database "raw" in your local postgres and insert sample dump from

```
/tests/fixtures/pokhara.sql
```

```
psql -U postgres -h localhost raw < pokhara.sql
```

Put your credentials on Rawdata block

```
[DB]
PGHOST=localhost
PGUSER=postgres
PGPASSWORD=admin
PGDATABASE=raw
PGPORT=5432
```

### Setup Oauth for Authentication

Login to [OSM](https://www.openstreetmap.org/) , Click on My Settings and register your local galaxy app to Oauth2applications

![image](https://user-images.githubusercontent.com/36752999/188452619-aababf28-b685-4141-b381-9c25d0367b57.png)

Check on read user preferences and Enter redirect URI as following

```
http://127.0.0.1:8000/v1/auth/callback/
```

Grab Client ID and Client Secret and put it inside config.txt as OAUTH Block , you can generate secret key for your application by yourself

```
[OAUTH]
OSM_CLIENT_ID= your client id
OSM_CLIENT_SECRET= your client secret
OSM_URL=https://www.openstreetmap.org
OSM_PERMISSION_SCOPE=read_prefs
LOGIN_REDIRECT_URI=http://127.0.0.1:8000/v1/auth/callback/
APP_SECRET_KEY=your generated secret key
```

### Configure celery and redis

API uses [Celery 5](https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html) and [Redis 6](https://redis.io/download/#redis-stack-downloads) for task queue management, Currently implemented for Rawdata endpoint. 6379 is the default port . if you are running redis on same machine your broker could be `redis://localhost:6379/`. You can change the port according to your configuration for the current docker compose use following

```
[CELERY]
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### Finalizing config.txt

Insert your config blocks with the database credentials where you have underpass ,insight and rawdata in your database along with oauth block

Summary of command :

Considering You have PSQL-POSTGIS setup with user **postgres** host **localhost** on port **5432** as password **admin**

```
  export PGPASSWORD='admin';
  psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE raw;"

  cd tests/fixtures/
  psql -U postgres -h localhost -p 5432 raw  < pokhara.sql
```

Your config.txt will look like this

```
[DB]
PGHOST=localhost
PGUSER=postgres
PGPASSWORD=admin
PGDATABASE=raw
PGPORT=5432

[OAUTH]
OSM_CLIENT_ID= your client id
OSM_CLIENT_SECRET= your client secret
OSM_URL=https://www.openstreetmap.org
OSM_PERMISSION_SCOPE=read_prefs
LOGIN_REDIRECT_URI=http://127.0.0.1:8000/v1/auth/callback/
APP_SECRET_KEY=jnfdsjkfndsjkfnsdkjfnskfn

[API_CONFIG]
LOG_LEVEL=debug
RATE_LIMITER_STORAGE_URI=redis://redis:6379

[CELERY]
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

```

**Tips** : Follow .github/workflows/[unit-test](https://github.com/hotosm/export-tool-api/blob/feature/celery/.github/workflows/unit-test.yml) If you have any confusion on implementation of config file .

## Optional Configuration [ You can skip this part for basic installation ]

You can further customize API if you wish with API_CONFIG Block

```
[API_CONFIG]
EXPORT_PATH=exports # used to store export path
EXPORT_MAX_AREA_SQKM=100000 # max area to support for rawdata input
USE_CONNECTION_POOLING=True # default it will not use connection pooling but you can configure api to use to for psycopg2 connections
LOG_LEVEL=info #options are info,debug,warning,error
ALLOW_BIND_ZIP_FILTER=true # option to configure export output zipped/unzipped Default all output will be zipped
RATE_LIMITER_STORAGE_URI=redis://localhost:6379 # API uses redis as backend for rate limiting
INDEX_THRESHOLD=5000 # value in sqkm to apply grid/country index filter
RATE_LIMIT_PER_MIN=5 # no of requests per minute - default is 5 requests per minute
```

Based on your requirement you can also customize rawdata exports parameter using EXPORT_UPLOAD block

```
[EXPORT_UPLOAD]
FILE_UPLOAD_METHOD=disk # options are s3,disk , default disk
AWS_ACCESS_KEY_ID= your id
AWS_SECRET_ACCESS_KEY= yourkey
BUCKET_NAME= your bucket name
```

Sentry Config :

```
[SENTRY]
SENTRY_DSN=
SENTRY_RATE=
```

### You can export config variables without block as system env variables too
