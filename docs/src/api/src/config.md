Module src.config
=================

Variables
---------

```python3
AWS_ACCESS_KEY_ID
```

```python3
AWS_SECRET_ACCESS_KEY
```

```python3
BUCKET_NAME
```

```python3
CONFIG_FILE_PATH
```

```python3
allow_bind_zip_filter
```

```python3
config
```

```python3
export_path
```

```python3
export_rate_limit
```

```python3
file_upload_method
```

```python3
grid_index_threshold
```

```python3
level
```

```python3
limiter
```

```python3
limiter_storage_uri
```

```python3
log_level
```

```python3
logger
```

```python3
use_connection_pooling
```

```python3
use_s3_to_upload
```

Functions
---------

    
#### get_db_connection_params

```python3
def get_db_connection_params(
    dbIdentifier: str
) -> dict
```
Return a python dict that can be passed to psycopg2 connections
to authenticate to Postgres Databases

Params: dbIdentifier: Section name of the INI config file containing
        database connection parameters

Returns: connection_params (dict): PostgreSQL connection parameters
         corresponding to the configuration section.