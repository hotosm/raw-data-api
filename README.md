# OSM Stats API

## Install

Install requirements.

```pip install -r requirements.txt```

Run server

```uvicorn API.main:app --reload```

# OSM Stats Package

## Local Install


```python setup.py install```

Now import as : 

```import osm_stats```

For database : 

```from osm_stats import Database```

For Mapathon : 

```from osm_stats import Mapathon```
##### You can see sample for mapathon in tests/terminal.py