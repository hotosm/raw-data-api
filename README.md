# GALAXY API

## Install

Install requirements.

```pip install -r requirements.txt```

Run server

```uvicorn API.main:app --reload```

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