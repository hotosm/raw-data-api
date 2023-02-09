Module API.tasks
================

Variables
---------

```python3
router
```

Functions
---------

    
#### get_task_status

```python3
def get_task_status(
    task_id
)
```
Tracks the request from the task id provided by Raw Data API  for the request

Args:

    task_id ([type]): [Unique id provided on response from /snapshot/]

Returns:

    id: Id of the task
    status : SUCCESS / PENDING
    result : Result of task

Successful task will have additional nested json inside