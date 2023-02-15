Before getting started on config Make sure you have [Postgres](https://www.postgresql.org/) and [Postgis](https://postgis.net/) setup in your machine.

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
http://127.0.0.1:8000/latest/auth/callback/
```

Grab Client ID and Client Secret and put it inside config.txt as OAUTH Block , you can generate secret key for your application by yourself

```
[OAUTH]
OSM_CLIENT_ID= your client id
OSM_CLIENT_SECRET= your client secret
OSM_URL=https://www.openstreetmap.org
OSM_PERMISSION_SCOPE=read_prefs
LOGIN_REDIRECT_URI=http://127.0.0.1:8000/latest/auth/callback/
APP_SECRET_KEY=your generated secret key
```

### Configure celery and redis

API uses [Celery 5](https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html) and [Redis 6](https://redis.io/download/#redis-stack-downloads) for task queue management , Currently implemented for Rawdata endpoint. 6379 is the default port . if you are running redis on same machine your broker could be `redis://localhost:6379/`. You can change the port according to your configuration for the current docker compose use following

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
LOGIN_REDIRECT_URI=http://127.0.0.1:8000/latest/auth/callback/
APP_SECRET_KEY=jnfdsjkfndsjkfnsdkjfnskfn

[API_CONFIG]
LOG_LEVEL=debug
RATE_LIMITER_STORAGE_URI=redis://redis:6379

[API_CONFIG]
LOG_LEVEL=debug
RATE_LIMITER_STORAGE_URI=redis://redis:6379

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
GRID_INDEX_THRESHOLD=5000 # value in sqkm to apply grid index filter
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
