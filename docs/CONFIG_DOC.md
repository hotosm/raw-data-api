
Before getting started on config Make sure you have [Postgres](https://www.postgresql.org/) and [Postgis](https://postgis.net/) setup in your machine.

**Note** : If you are running API through Docker container , Your local postgres should be accessible from containers . In order to do that find your network ip address (for linux/mac you can use ```ifconfig -l | xargs -n1 ipconfig getifaddr``` ) and use your ip as a host instead of localhost in config file .
If connection still fails : You may need to edit your postgres config file ( ask postgres where it is by this query ```show config_file;``` ) and edit/enable ```listen_addresses = '*'``` inside ```postgresql.conf``` . Also add ```host    all             all             0.0.0.0/0               trust``` in ```pg_hba.conf```

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
Put your credentials in Underpass block
```
[UNDERPASS]
host=localhost
user=postgres
password=admin
database=underpass
port=5432
```

### 3. Setup Insights for Historical Data
Setup insights from [here](https://github.com/hotosm/insights) OR Create database "insights" in your local postgres and insert sample dump from
```
/tests/src/fixtures/insights.sql
```

```
psql -U postgres -h localhost insights < insights.sql
```
Add a sample data dump for mapathon summary to visualize statistics

```
psql -U postgres -h localhost insights < tests/src/fixtures/mapathon_summary.sql
```

Put your credentials in insights block
```
[INSIGHTS]
host=localhost
user=postgres
password=admin
database=insights
port=5432
```

### 4. Setup Raw Data for Current OSM Snapshot
Initialize rawdata from [here](https://github.com/hotosm/underpass/tree/master/raw) OR Create database "raw" in your local postgres and insert sample dump from
```
/tests/src/fixtures/raw_data.sql
```

```
psql -U postgres -h localhost raw < raw_data.sql
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

### 5. Setup Tasking Manager Database for TM related development

Setup Tasking manager from [here](https://github.com/hotosm/tasking-manager/blob/develop/docs/developers/development-setup.md#backend) OR Create database "tm" in your local postgres and insert sample dump from [TM test dump](https://github.com/hotosm/tasking-manager/blob/develop/tests/database/tasking-manager.sql).

```
wget https://raw.githubusercontent.com/hotosm/tasking-manager/develop/tests/database/tasking-manager.sql
```

```
psql -U postgres -h localhost tm < tasking-manager.sql
```
Put your credentials on TM block
```
[TM]
host=localhost
user=postgres
password=admin
database=tm
port=5432
```

### 6. Setup Oauth for Authentication
Login to [OSM](https://www.openstreetmap.org/) , Click on My Settings and register your local galaxy app to Oauth2applications

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

### 7. Configure celery and redis

Galaxy API uses [Celery 5](https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html) and [Redis 6](https://redis.io/download/#redis-stack-downloads) for task queue management , Currently implemented for Rawdata endpoint. 6379 is the default port . if you are running redis on same machine your broker could be ```redis://localhost:6379/```. You can change the port according to your configuration for the current docker compose use following

```
[CELERY]
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 7. Finalizing config.txt
Insert your config blocks with the database credentials where you have underpass ,insight and rawdata in your database along with oauth block

Summary of command :

Considering You have PSQL-POSTGIS setup  with user **postgres** host **localhost** on port **5432** as password **admin**

```
  export PGPASSWORD='admin';
  psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE underpass;"
  psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE tm;"
  psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE raw;"

  cd tests/src/fixtures/
  psql -U postgres -h localhost -p 5432 insights < insights.sql
  psql -U postgres -h localhost -p 5432 insights < mapathon_summary.sql
  psql -U postgres -h localhost -p 5432 raw  < raw_data.sql
  psql -U postgres -h localhost -p 5432 underpass < underpass.sql
  wget https://raw.githubusercontent.com/hotosm/tasking-manager/develop/tests/database/tasking-manager.sql
  psql -U postgres -h localhost -p 5432 tm < tasking-manager.sql
```

Your config.txt will look like this

```
[UNDERPASS]
host=localhost
user=postgres
password=admin
database=underpass
port=5432

[INSIGHTS]
host=localhost
user=postgres
password=admin
database=insights
port=5432

[RAW_DATA]
host=localhost
user=postgres
password=admin
database=raw
port=5432

[TM]
host=localhost
user=postgres
password=admin
database=tm
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

