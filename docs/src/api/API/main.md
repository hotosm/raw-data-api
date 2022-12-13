Module API.main
===============

Variables
---------

```python3
app
```

```python3
export_path
```

```python3
origins
```

```python3
run_env
```

```python3
use_connection_pooling
```

```python3
use_s3_to_upload
```

Functions
---------

    
#### add_process_time_header

```python3
def add_process_time_header(
    request,
    call_next
)
```
Times request and knows response time and pass it to header in every request

Args:
    request (_type_): _description_
    call_next (_type_): _description_

Returns:
    header with process time

    
#### on_shutdown

```python3
def on_shutdown(
    
)
```
Closing all the threads connection from pooling before shuting down the api

    
#### on_startup

```python3
def on_startup(
    
)
```
Fires up 3 idle conenction with threaded connection pooling before starting the API

Raises:
    e: if connection is rejected to database