# Module API.tasks

None

None

## Variables

```python3
router
```

## Functions

    
### get_task_status

```python3
def get_task_status(
    task_id
)
```

    
Tracks the request from the task id provided by export tool api for the request

**Parameters:**

| Name | Type | Description | Default |
|---|---|---|---|
| task_id | [type] | [Unique id provided on response from /snapshot/] | None |

**Returns:**

| Type | Description |
|---|---|
| id | Id of the task
status : SUCCESS / PENDING
    result : Result of task

Successful task will have additional nested json inside |