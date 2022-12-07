
Before getting started on config Make sure you have [Postgres](https://www.postgresql.org/) and [Postgis](https://postgis.net/) setup in your machine.


## Compulsary Configuration

### 1. Create ```config.txt``` inside src directory.
![image](https://user-images.githubusercontent.com/36752999/188402566-80dc9633-5d4e-479c-97dc-9e8a4999b385.png)


### 2. Prepare your OSM Snapshot Data
Initialize rawdata from [here](https://github.com/hotosm/underpass/tree/master/raw) OR Create database "raw" in your local postgres and insert sample dump of Pokhara city from
```
/tests/fixtures/pokhara.sql
```

```
psql -U postgres -h localhost raw < pokhara.sql
```
Put your credentials on Rawdata block

```
[RAW_DATA]
host=localhost
user=postgres
password=admin
database=raw
port=5432
```

### 3. Setup Oauth for Authentication
Login to [OSM](https://www.openstreetmap.org/) , Click on My Settings and register your local export_tool_api app to Oauth2applications

![image](https://user-images.githubusercontent.com/36752999/188452619-aababf28-b685-4141-b381-9c25d0367b57.png)


Check on read user preferences and Enter redirect URI as following
```
http://127.0.0.1:8000/latest/auth/callback/
```

Grab Client ID and Client Secret and put it inside config.txt as OAUTH Block , you can generate secret key for your application by yourself

```
[OAUTH]
client_id= your client id
client_secret= your client secret
url=https://www.openstreetmap.org
scope=read_prefs
login_redirect_uri=http://127.0.0.1:8000/latest/auth/callback/
secret_key=jnfdsjkfndsjkfnsdkjfnskfn
```

### 4. Configure celery and redis

API uses [Celery 5](https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html) and [Redis 6](https://redis.io/download/#redis-stack-downloads) for task queue management , Currently implemented for Rawdata endpoint. 6379 is the default port . if you are running redis on same machine your broker could be ```redis://localhost:6379/```. You can change the port according to your configuration for the current docker compose use following

```
[CELERY]
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 5. Finalizing config.txt
Insert your config blocks with the database credentials where you have underpass ,insight and rawdata in your database along with oauth block

Summary of command :

Considering You have PSQL-POSTGIS setup  with user **postgres** host **localhost** on port **5432** as password **admin**

```
  export PGPASSWORD='admin';
  psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE raw;"

  cd tests/fixtures/
  psql -U postgres -h localhost -p 5432 raw  < pokhara.sql
```

Your config.txt will look like this

```
[RAW_DATA]
host=localhost
user=postgres
password=admin
database=raw
port=5432

[OAUTH]
client_id= your client id
client_secret= your client secret
url=https://www.openstreetmap.org
scope=read_prefs
login_redirect_uri=http://127.0.0.1:8000/latest/auth/callback/
secret_key=jnfdsjkfndsjkfnsdkjfnskfn

[API_CONFIG]
env=dev
log_level=debug
limiter_storage_uri=redis://redis:6379

[CELERY]
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

```

**Tips** : Follow .github/workflows/[unit-test](https://github.com/hotosm/export-tool-api/blob/feature/celery/.github/workflows/unit-test.yml) If you have any confusion on implementation of config file .

## Optional Configuration [ You can skip this part for basic installation ]

You can further customize API if you wish with API_CONFIG Block

```
[API_CONFIG]
export_path=exports # used to store export path
api_host=http://127.0.0.1 # you can define this if you have different host
api_port=8000
max_area=100000 # max area to support for rawdata input
use_connection_pooling=True # default it will not use connection pooling but you can configure api to use to for psycopg2 connections
log_level=info #options are info,debug,warning,error
env=dev # default is dev , supported values are dev and prod
allow_bind_zip_filter=true # option to configure export output zipped/unzipped Default all output will be zipped
limiter_storage_uri=redis://localhost:6379 # API uses redis as backend for rate limiting
grid_index_threshold=5000 # value in sqkm to apply grid index filter
export_rate_limit=5 # no of requests per minute - default is 5 requests per minute
```
Based on your requirement you can also customize rawdata exports parameter using EXPORT_UPLOAD block

```
[EXPORT_UPLOAD]
FILE_UPLOAD_METHOD=disk # options are s3,disk , default disk
AWS_ACCESS_KEY_ID= your id
AWS_SECRET_ACCESS_KEY= yourkey
BUCKET_NAME= your bucket name
```

