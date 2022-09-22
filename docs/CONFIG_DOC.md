
Before getting started on config Make sure you have https://www.postgresql.org/ setup in your machine.

## Compulsary Configuration 

### 1. Create ```config.txt``` inside src directory.
![image](https://user-images.githubusercontent.com/36752999/188402566-80dc9633-5d4e-479c-97dc-9e8a4999b385.png)


### 2. Setup Underpass
  Run underpass from [here](https://github.com/hotosm/underpass/blob/master/doc/getting-started.md)  OR Create database "underpass" in your local postgres and insert sample dump from
```
/tests/src/fixtures/underpass.sql
```

```
psql -U postgres -h localhost underpass < underpass.sql
```
### 3. Setup Insights
Setup insights from [here](https://github.com/hotosm/insights) OR Create database "insights" in your local postgres and insert sample dump from
```
/tests/src/fixtures/insights.sql
```

```
psql -U postgres -h localhost insights < insights.sql
```

### 4. Setup Raw Data
Initialize rawdata from [here](https://github.com/hotosm/underpass/tree/master/raw) OR Create database "raw" in your local postgres and insert sample dump from
```
/tests/src/fixtures/raw_data.sql
```

```
psql -U postgres -h localhost raw < raw_data.sql
```


### 5. Setup Oauth
Login to [OSM](https://www.openstreetmap.org/) , Click on My Settings and register your local galaxy app to Oauth2applications

![image](https://user-images.githubusercontent.com/36752999/188452619-aababf28-b685-4141-b381-9c25d0367b57.png)


Check on read user preferences and Enter redirect URI as following
```
http://127.0.0.1:8000/latest/auth/callback/
```

Grab Client ID and Client Secret and put it inside config.txt as OAUTH Block , you can generate secret key for your application by yourself


### 6. Put your credentials inside config.txt
Insert your config blocks with the database credentials where you have underpass ,insight and rawdata in your database along with oauth block

```
[INSIGHTS]
host=localhost
user=postgres
password=admin
database=insights
port=5432

[UNDERPASS]
host=localhost
user=postgres
password=admin
database=underpass
port=5432

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

```

**Celery Configuration options:**

Galaxy API uses [Celery 5](https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html) and [Redis 6](https://redis.io/download/#redis-stack-downloads) for task queue management , Currently implemented for Rawdata endpoint. 6379 is the default port , You can change the port according to your configuration , for the local setup Broker URL could be redis://localhost:6379/0 , for the current docker compose use following

**For local installation :**
```
[CELERY]
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```


**For Docker :**
```
[CELERY]
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

**Tips** : Follow .github/workflows/[unit-test](https://github.com/hotosm/galaxy-api/blob/feature/celery/.github/workflows/unit-test.yml) If you have any confusion on implementation of config file .

## Optional Configuration [ You can skip this part for basic installation ] 

You can further customize API if you wish with API_CONFIG Block

```
[API_CONFIG]
export_path=exports/ # used to store export path
api_host=http://127.0.0.1 # you can define this if you have different host
api_port=8000
max_area=100000 # max area to support for rawdata input
use_connection_pooling=True # default it will not use connection pooling but you can configure api to use to for psycopg2 connections
log_level=info #options are info,debug,warning,error
env=dev # default is dev , supported values are dev and prod
shp_limit=6000 # in mb default is 4096
```
Based on your requirement you can also customize rawdata exports parameter using EXPORT_UPLOAD block

```
[EXPORT_UPLOAD]
FILE_UPLOAD_METHOD=disk # options are s3,disk , default disk
AWS_ACCESS_KEY_ID= your id
AWS_SECRET_ACCESS_KEY= yourkey
BUCKET_NAME= your bucket name
```


##### Setup Tasking Manager Database for TM related development

Setup Tasking manager from [here](https://github.com/hotosm/tasking-manager/blob/develop/docs/developers/development-setup.md#backend) OR Create database "tm" in your local postgres and insert sample dump from [TM test dump](https://github.com/hotosm/tasking-manager/blob/develop/tests/database/tasking-manager.sql).

```
wget https://raw.githubusercontent.com/hotosm/tasking-manager/develop/tests/database/tasking-manager.sql
```


```
psql -U postgres -h localhost tm < tasking-manager.sql
```

Add those block to config.txt with the value you use in the tasking manager configuration.
```
[TM]
host=localhost
user=postgres
password=admin
database=tm
port=5432
```

You can test it later after running server with the `/mapathon/detail/` endpoint and with the following input:
`
{"fromTimestamp":"2019-04-08 10:00:00.000000","toTimestamp":"2019-04-08 11:00:00.000000","projectIds":[1],"hashtags":[]}
`

