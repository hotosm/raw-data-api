# Module src.db_connection

None

None

## Classes

### Database

```python3
class Database(
    
)
```

#### Methods

    
#### close_all_connection_pool

```python3
def close_all_connection_pool(
    self
)
```

    
Closes the connection thread created by thread pooling all at once

    
#### connect

```python3
def connect(
    self
)
```

    
Connection to the database

    
#### get_conn_from_pool

```python3
def get_conn_from_pool(
    self
)
```

    
Function to get connection from the pool instead of new connection

**Returns:**

| Type | Description |
|---|---|
| None | connection |

    
#### release_conn_from_pool

```python3
def release_conn_from_pool(
    self,
    pool_con
)
```

    
Can be used to release specific connection after its use from the pool , so that it can be used by another process

**Parameters:**

| Name | Type | Description | Default |
|---|---|---|---|
| pool_con | _type_ | define which connection to remove from pool | None |

**Raises:**

| Type | Description |
|---|---|
| ex | error if connection doesnot exists or misbehave of function |