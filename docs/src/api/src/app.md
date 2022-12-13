# Module src.app

Page contains Main core logic of app

None

## Variables

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
LOCAL_CON_POOL
```

```python3
database_instance
```

```python3
export_path
```

```python3
grid_index_threshold
```

```python3
level
```

```python3
use_connection_pooling
```

## Functions

    
### check_for_json

```python3
def check_for_json(
    result_str
)
```

    
Check if the Payload is a JSON document

Return: bool:
    True in case of success, False otherwise

    
### dict_none_clean

```python3
def dict_none_clean(
    to_clean
)
```

    
Clean DictWriter

    
### print_psycopg2_exception

```python3
def print_psycopg2_exception(
    err
)
```

    
Function that handles and parses Psycopg2 exceptions

    
### run_ogr2ogr_cmd

```python3
def run_ogr2ogr_cmd(
    cmd
)
```

    
Runs command and monitors the file size until the process runs

**Parameters:**

| Name | Type | Description | Default |
|---|---|---|---|
| cmd | _type_ | Command to run for subprocess | None |
| binding_file_dir | _type_ | _description_ | None |

**Raises:**

| Type | Description |
|---|---|
| Exception | If process gets failed |

## Classes

### Database

```python3
class Database(
    db_params
)
```

#### Methods

    
#### close_conn

```python3
def close_conn(
    self
)
```

    
function for clossing connection to avoid memory leaks

    
#### connect

```python3
def connect(
    self
)
```

    
Database class instance method used to connect to database parameters with error printing

    
#### executequery

```python3
def executequery(
    self,
    query
)
```

    
Function to execute query after connection

### ProgressPercentage

```python3
class ProgressPercentage(
    filename
)
```

#### Attributes

| Name | Type | Description | Default |
|---|---|---|---|
| object | _type_ | _description_ | None |

### RawData

```python3
class RawData(
    parameters=None,
    dbdict=None
)
```

#### Static methods

    
#### close_con

```python3
def close_con(
    con
)
```

    
Closes connection if exists

    
#### get_grid_id

```python3
def get_grid_id(
    geom,
    cur,
    country_export=False
)
```

    
Gets the intersecting related grid id for the geometry that is passed

**Parameters:**

| Name | Type | Description | Default |
|---|---|---|---|
| geom | _type_ | _description_ | None |
| cur | _type_ | _description_ | None |

**Returns:**

| Type | Description |
|---|---|
| _type_ | grid id , geometry dump and the area of geometry |

    
#### ogr_export

```python3
def ogr_export(
    query,
    outputtype,
    working_dir,
    dump_temp_path,
    params
)
```

    
Function written to support ogr type extractions as well , In this way we will be able to support all file formats supported by Ogr , Currently it is slow when dataset gets bigger as compared to our own conversion method but rich in feature and data types even though it is slow

    
#### ogr_export_shp

```python3
def ogr_export_shp(
    point_query,
    line_query,
    poly_query,
    working_dir,
    file_name
)
```

    
Function written to support ogr type extractions as well , In this way we will be able to support all file formats supported by Ogr , Currently it is slow when dataset gets bigger as compared to our own conversion method but rich in feature and data types even though it is slow

    
#### query2geojson

```python3
def query2geojson(
    con,
    extraction_query,
    dump_temp_file_path
)
```

    
Function written from scratch without being dependent on any library, Provides better performance for geojson binding

    
#### to_geojson_raw

```python3
def to_geojson_raw(
    results
)
```

    
Responsible for geojson writing

#### Methods

    
#### check_status

```python3
def check_status(
    self
)
```

    
Gives status about DB update, Substracts with current time and last db update time

    
#### extract_current_data

```python3
def extract_current_data(
    self,
    exportname
)
```

    
Responsible for Extracting rawdata current snapshot, Initially it creates a geojson file , Generates query , run it with 1000 chunk size and writes it directly to the geojson file and closes the file after dump

**Parameters:**

| Name | Type | Description | Default |
|---|---|---|---|
| exportname | None | takes filename as argument to create geojson file passed from routers | None |

**Returns:**

| Type | Description |
|---|---|
| geom_area | area of polygon supplied
working_dir: dir where results are saved |

    
#### extract_plain_geojson

```python3
def extract_plain_geojson(
    self
)
```

    
Gets geojson for small area : Performs direct query with/without geometry

### S3FileTransfer

```python3
class S3FileTransfer(
    
)
```

#### Methods

    
#### get_bucket_location

```python3
def get_bucket_location(
    self,
    bucket_name
)
```

    
Provides the bucket location on aws, takes bucket_name as string -- name of repo on s3

    
#### list_buckets

```python3
def list_buckets(
    self
)
```

    
used to list all the buckets available on s3

    
#### upload

```python3
def upload(
    self,
    file_path,
    file_name,
    file_suffix='zip'
)
```

    
Used for transferring file to s3 after reading path from the user , It will wait for the upload to complete

Parameters :file_path --- your local file path to upload ,
    file_prefix -- prefix for the filename which is stored
sample function call :
    S3FileTransfer.transfer(file_path="exports",file_prefix="upload_test")