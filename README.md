# GALAXY API
![example workflow](https://github.com/hotosm/galaxy-api/actions/workflows/Unit-Test.yml/badge.svg)
![example workflow](https://github.com/hotosm/galaxy-api/actions/workflows/locust.yml/badge.svg)

## Getting Started

### 1. Install requirements.

Install gdal on your machine , for example on Ubuntu

```
sudo apt-add-repository ppa:ubuntugis/ubuntugis-unstable
sudo apt-get update
sudo apt-get install gdal-bin libgdal-dev
```

Clone the Repo to your machine

``` git clone https://github.com/hotosm/galaxy-api.git ```

Navigate to repo

``` cd galaxy-api ```

Install python dependencies

```pip install -r requirements.txt```

Install gdal python ( Include your gdal version , if you are using different version )

```pip install gdal==3.0.2```



### 2. Create ```config.txt``` inside src directory.
![image](https://user-images.githubusercontent.com/36752999/188402566-80dc9633-5d4e-479c-97dc-9e8a4999b385.png)


### 3. Setup Underpass
  Run underpass from [here](https://github.com/hotosm/underpass/blob/master/doc/getting-started.md)  OR Create database "underpass" in your local postgres and insert sample dump from  ```/tests/src/fixtures/underpass.sql ```

```psql -U postgres -h localhost underpass < underpass.sql```
### 4. Setup Insights
Setup insights from [here](https://github.com/hotosm/insights) OR Create database "insights" in your local postgres and insert sample dump from  ```/tests/src/fixtures/insights.sql ```

```psql -U postgres -h localhost insights < insights.sql```

### 5. Setup Raw Data
Initialize rawdata from [here](https://github.com/hotosm/underpass/tree/master/raw) OR Create database "raw" in your local postgres and insert sample dump from  ```/tests/src/fixtures/raw_data.sql ```

```psql -U postgres -h localhost raw < raw_data.sql```


### 6. Setup Oauth
Login to [OSM](https://www.openstreetmap.org/) , Click on My Settings and register your local galaxy app to Oauth2applications

![image](https://user-images.githubusercontent.com/36752999/188452619-aababf28-b685-4141-b381-9c25d0367b57.png)


Check on read user preferences and Enter redirect URI as following
```http://127.0.0.1:8000/latest/auth/callback/```

Grab Client ID and Client Secret and put it inside config.txt as OAUTH Block , you can generate secret key for your application by yourself


### 7. Put your credentials inside config.txt
Insert your config blocks with the database credentials where you have underpass ,insight and tm in your database

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

#### Optional Configuration

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
(```wget https://raw.githubusercontent.com/hotosm/tasking-manager/develop/tests/database/tasking-manager.sql```)

```psql -U postgres -h localhost tm < tasking-manager.sql```

Add those block to config.txt with the value you use in the tasking manager configuration.
```
[TM]
host=localhost
user=postgres
password=admin
database=tm
port=5432
```

You can test it with the `/mapathon/detail/` endpoint and with the following input:
`{"fromTimestamp":"2019-04-08 10:00:00.000000","toTimestamp":"2019-04-08 11:00:00.000000","projectIds":[1],"hashtags":[]}`

### 8. Run server

```uvicorn API.main:app --reload```

### 9. Navigate to Fast API Docs to get details about API Endpoint

After sucessfully running server , hit [this](http://127.0.0.1:8000/latest/docs) URL on your browser

```http://127.0.0.1:8000/latest/docs```

### Check Authetication

1. Hit /auth/login/
2. Hit Url returned on response
3. You will get access_token
4. You can use that access_token in all endpoints that requires authentication , To check token pass token in /auth/me/ It should return your osm profile

If you get a 401 response with the detail "User is not staff member", get your OSM id using https://osm-stats.hotosm.org/v1/docs#/default/get_user_id_osm_users_ids__post, then run the following SQL on underpass database replacing ID:

```sql
INSERT INTO users_roles VALUES (ID, 1);
```

Repeat the steps to get a new access_token.

#### API has been setup successfully ! 


## Run tests

Galaxy-API uses pytest for tests ,Navigate to root Dir, Install package in editable mode


```pip install -e .```


Make sure you have postgresql installed locally with postgis extension enabled , Now Run Pytest


```py.test -v -s```


Run Individual tests

```py.test -k test function name```


# Galaxy Package

## Local Install


```python setup.py install```

Now import as :

```import galaxy```

For database :

```from galaxy import Database```

For Mapathon :

```from galaxy import Mapathon```

## New Relic
When using New Relic, save the newrelic.ini to the root of the project and run the following to start the server:

```NEW_RELIC_CONFIG_FILE=newrelic.ini $PATH_TO_BIN/newrelic-admin run-program $PATH_TO_BIN/uvicorn API.main:app```

## Setup Documentation

Galaxy API Uses Sphinx for it's technical documentation.

To Setup  :

Navigate to docs Folder and Build .rst files first

``` cd docs ```
#### If you want to generate documentation for src
``` sphinx-apidoc -o source ../src/galaxy ```
#### If you want to generate documentation for API
``` sphinx-apidoc -o source ../API ```

#### You can create HTML files with following
Or you can export it in other supported formats by Sphinx

``` make html ```

All exported html files are inside build/html
