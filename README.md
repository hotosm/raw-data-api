# GALAXY API
![example workflow](https://github.com/hotosm/galaxy-api/actions/workflows/Unit-Test.yml/badge.svg)
![example workflow](https://github.com/hotosm/galaxy-api/actions/workflows/locust.yml/badge.svg)

## Getting Started

API Can be installed through docker or manually to local machine .
To get started with docker follow [GETTING_STARTED_WITH_DOCKER](https://github.com/hotosm/galaxy-api/blob/develop/docs/GETTING_STARTED_WITH_DOCKER.md)

### 1. Install requirements.

- Install [gdal](https://gdal.org/index.html) on your machine , for example on Ubuntu

```
sudo apt-get update && sudo apt-get -y upgrade && sudo apt-get -y install gdal-bin python3-gdal && sudo apt-get -y autoremove && sudo apt-get clean

```
- Install [redis](https://redis.io/docs/getting-started/installation/) on your system

```
sudo apt-get install redis
```

- Check Redis server

Check redis is running on your machine

Login to redis cli

```
redis-cli
```

Hit ```ping``` it should return pong

If REDIS is not running check out its [documentation](https://redis.io/docs/getting-started/)

- Clone the Repo to your machine

```
git clone https://github.com/hotosm/galaxy-api.git
```

Navigate to repo

```
cd galaxy-api
```

- Install python dependencies

```
pip install -r requirements.txt
```

Install gdal python ( Include your gdal version , if you are using different version )

```
pip install gdal==3.0.2
```

### 2. Setup required config for API

Make sure you have https://www.postgresql.org/ setup in your machine.

Setup necessary config for API from [docs/CONFIG.DOC](https://github.com/hotosm/galaxy-api/blob/develop/docs/CONFIG_DOC.md)

### 3. Run server

```
uvicorn API.main:app --reload
```

### 4. Start Celery Worker
You should be able to start [celery](https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html#running-the-celery-worker-server) worker  by running following command on different shell

```
celery --app API.api_worker worker --loglevel=INFO
```

### 5 . [OPTIONAL] Start flower for monitoring queue

API uses flower for monitoring the Celery distributed queue. Run this command on different shell

```
celery --app API.api_worker flower --port=5550 --broker=redis://redis:6379/
```

### 6. Navigate to Fast API Docs to get details about API Endpoint

After sucessfully running server , hit [this](http://127.0.0.1:8000/latest/docs) URL on your browser

```
http://127.0.0.1:8000/latest/docs
```

Flower dashboard should be available on 5550 localhost port.

```
http://127.0.0.1:5550/
```

## Check API Installation
### Check Authetication

1. Hit /auth/login/
2. Hit Url returned on response
3. You will get access_token
4. You can use that access_token in all endpoints that requires authentication , To check token pass token in /auth/me/ It should return your osm profile

If you get a 401 response with the detail "User is not staff member", get your OSM id using https://galaxy-api.hotosm.org/v1/docs#/default/get_user_id_osm_users_ids__post, then run the following SQL on underpass database replacing ID:

```sql
INSERT INTO users_roles VALUES (ID, 1);
```

Repeat the steps to get a new access_token.

You can test  with the `/mapathon/detail/` endpoint  with the following input to check both authentication and database connection

```
{"fromTimestamp":"2019-04-08 10:00:00.000000","toTimestamp":"2019-04-08 11:00:00.000000","projectIds":[1],"hashtags":[]}
```


#### API has been setup successfully !


## Run tests

Galaxy-API uses pytest for tests ,Navigate to root Dir, Install package in editable mode


```
pip install -e .
```


Make sure you have postgresql installed locally with postgis extension enabled , Now Run Pytest


```
py.test -v -s
```


Run Individual tests

```
py.test -k test function name
```


# Galaxy Package

## Local Install


```
python setup.py install
```

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
