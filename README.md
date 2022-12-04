# Export Tool API
![Unit test](https://github.com/hotosm/export-tool-api/actions/workflows/Unit-Test.yml/badge.svg)
![Build](https://github.com/hotosm/export-tool-api/actions/workflows/build.yml/badge.svg)

## Getting Started

API Can be installed through docker or manually to local machine .
To get started with docker follow [GETTING_STARTED_WITH_DOCKER](/docs/GETTING_STARTED_WITH_DOCKER.md)
### 1. Install requirements.

- Install [gdal](https://gdal.org/index.html) on your machine , for example on Ubuntu

```
sudo apt-get update && sudo apt-get -y install gdal-bin python3-gdal && sudo apt-get -y autoremove && sudo apt-get clean

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
git clone https://github.com/hotosm/export-tool-api.git
```

Navigate to repo

```
cd export-tool-api
```

- Install python dependencies

```
pip install -r requirements.txt
```

### 2. Setup required config for API

Make sure you have https://www.postgresql.org/ setup in your machine or you can use docker

Setup necessary config for API from [docs/CONFIG.DOC](/docs/CONFIG_DOC.md)

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

API uses flower for monitoring the Celery distributed queue. Run this command on different shell , if you are running redis on same machine your broker could be ```redis://localhost:6379//```

```
celery --broker=redis://redis:6379// --app API.api_worker flower --port=5000
```

### 6. Navigate to Fast API Docs to get details about API Endpoint

After sucessfully running server , hit [this](http://127.0.0.1:8000/latest/docs) URL on your browser

```
http://127.0.0.1:8000/latest/docs
```

Flower dashboard should be available on 5000 localhost port.

```
http://127.0.0.1:5000/
```

## Check API Installation

- Check Authetication :

  1. Hit /auth/login/
  2. Hit Url returned on response
  3. You will get access_token
  4. You can use that access_token in all endpoints that requires authentication , To check token pass token in /auth/me/ It should return your osm profile

- Check Extraction :

  You can test  with the `/raw-data/current-snapshot/` endpoint  with the following input to check both authentication , database connection and download the export

  ```
  curl -d '{"geometry":{"type":"Polygon","coordinates":[[[83.96919250488281,28.194446860487773],[83.99751663208006,28.194446860487773],   [83.99751663208006,28.214869548073377],[83.96919250488281,28.214869548073377],[83.96919250488281,28.194446860487773]]]}}' -H 'Content-Type: application/json'   http://127.0.0.1:8000/v2/raw-data/current-snapshot/
  ```

Clean Setup of API can be found in github action workflow , You can follow the steps for more [clarity](/.github/workflows/build.yml).  ```/workflows/build.yml```

#### API has been setup successfully !


## Run tests

Export tool-API uses pytest for tests ,Navigate to root Dir, Install package in editable mode


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


# Dev Setup



## New Relic
When using New Relic, save the newrelic.ini to the root of the project and run the following to start the server:

```NEW_RELIC_CONFIG_FILE=newrelic.ini $PATH_TO_BIN/newrelic-admin run-program $PATH_TO_BIN/uvicorn API.main:app```

## Setup Documentation

Repo Sphinx for it's technical documentation.

To Setup  :

Navigate to docs Folder and Build .rst files first

``` cd docs ```
#### If you want to generate documentation for src
``` sphinx-apidoc -o source ../src ```
#### If you want to generate documentation for API
``` sphinx-apidoc -o source ../API ```

#### You can create HTML files with following
Or you can export it in other supported formats by Sphinx

``` make html ```

All exported html files are inside build/html
