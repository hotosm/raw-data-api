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
##### You can see sample for mapathon in tests/src/terminal.py