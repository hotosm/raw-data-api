import json
from datetime import datetime

import redis
from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi_versioning import version

from src.config import CELERY_BROKER_URL, DAEMON_QUEUE_NAME, DEFAULT_QUEUE_NAME
from src.validation.models import SnapshotTaskResponse

from .api_worker import celery
from .auth import AuthUser, admin_required, login_required, staff_required

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/status/{task_id}/", response_model=SnapshotTaskResponse)
@version(1)
def get_task_status(
    task_id,
    only_args: bool = Query(
        default=False,
        description="Indicates whether to fetch only the arguments of the task.",
    ),
):
    """
    Retrieve the current status and result of a task identified by its unique task ID.

    Args:
        task_id (uuid.UUID): The unique identifier of the task. It must be a valid UUID.
        only_args (bool, optional): Specifies whether to fetch only the arguments of the task.
            Defaults to False.

    Returns:
        dict: A dictionary containing the status and result of the task.

    The possible status values are:
        - PENDING: The task is waiting for execution.
        - STARTED: The task has been started.
        - RETRY: The task is scheduled for retry, possibly due to failure.
        - FAILURE: The task failed or exceeded the retry limit.
        - SUCCESS: The task executed successfully.

    If the task is successful, the result attribute contains the task's return value.

    If only_args is True, only the arguments of the task are returned.

    Successful tasks may include additional nested JSON data representing the result.

    Raises:
        HTTPException(422): If the provided task_id is not a valid UUID.

    Examples:
        To fetch the status and result of a task:
            GET /tasks/status/{task_id}/

        Example Response (Success):
        {
            "id": "2f0d9d8e-07a9-4364-b604-64e8d665b0ad",
            "status": "SUCCESS",
            "result": {
                "data": { ... },
                "message": "Task completed successfully."
            }
        }

        Example Response (Pending):
        {
            "id": "2f0d9d8e-07a9-4364-b604-64e8d665b0ad",
            "status": "PENDING",
            "result": null
        }
    """
    task_result = AsyncResult(task_id, app=celery)
    if only_args:
        return JSONResponse(task_result.args)
    task_response_result = None
    if task_result.status == "SUCCESS":
        task_response_result = task_result.result
    if task_result.state != "SUCCESS":
        task_response_result = str(task_result.info)

    result = {
        "id": task_id,
        "status": task_result.state,
        "result": task_response_result,
    }
    return JSONResponse(result)


@router.get("/revoke/{task_id}/")
@version(1)
def revoke_task(task_id, user: AuthUser = Depends(staff_required)):
    """Revokes task , Terminates if it is executing

    Args:
        task_id (_type_): task id of raw data task

    Returns:
        id: id of revoked task
    """
    celery.control.revoke(task_id=task_id, terminate=True)
    return JSONResponse({"id": task_id})


@router.get("/inspect/")
@version(1)
def inspect_workers(
    request: Request,
    summary: bool = Query(
        default=True,
        description="Displays summary of tasks",
    ),
):
    """Inspects tasks assigned to workers

    Returns:
        active: Current Active tasks ongoing on workers
    """
    inspected = celery.control.inspect()
    active_tasks = inspected.active()
    active_tasks_summary = []

    if summary:
        if active_tasks:
            for worker, tasks in active_tasks.items():
                worker_tasks = {worker: {}}

                for task in tasks:
                    worker_tasks[worker]["id"] = task["id"]
                    worker_tasks[worker]["task"] = task["name"]
                    worker_tasks[worker]["time_start"] = (
                        datetime.fromtimestamp(task["time_start"]).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        if task["time_start"]
                        else None
                    )
                active_tasks_summary.append(worker_tasks)

    response_data = {
        "active": active_tasks_summary if summary else active_tasks,
    }
    return JSONResponse(content=response_data)


@router.get("/ping/")
@version(1)
def ping_workers():
    """Pings available workers

    Returns: {worker_name : return_result}
    """
    inspected_ping = celery.control.inspect().ping()
    return JSONResponse(inspected_ping)


@router.get("/purge/")
@version(1)
def discard_all_waiting_tasks(user: AuthUser = Depends(admin_required)):
    """
    Discards all waiting tasks from the queue
    Returns : Number of tasks discarded
    """
    purged = celery.control.purge()
    return JSONResponse({"tasks_discarded": purged})


queues = [DEFAULT_QUEUE_NAME, DAEMON_QUEUE_NAME]


@router.get("/queue/")
@version(1)
def get_queue_info():
    queue_info = {}
    redis_client = redis.StrictRedis.from_url(CELERY_BROKER_URL)

    for queue_name in queues:
        # Get queue length
        queue_length = redis_client.llen(queue_name)

        queue_info[queue_name] = {
            "length": queue_length,
        }

    return JSONResponse(content=queue_info)


@router.get("/queue/details/{queue_name}/")
@version(1)
def get_list_details(
    queue_name: str,
    args: bool = Query(
        default=False,
        description="Includes arguments of task",
    ),
):
    if queue_name not in queues:
        raise HTTPException(status_code=404, detail=f"Queue '{queue_name}' not found")
    redis_client = redis.StrictRedis.from_url(CELERY_BROKER_URL)

    list_items = redis_client.lrange(queue_name, 0, -1)

    # Convert bytes to strings
    list_items = [item.decode("utf-8") for item in list_items]

    items_details = [
        {
            "index": index,
            "id": json.loads(item)["headers"]["id"],
            **({"args": json.loads(item)["headers"]["argsrepr"]} if args else {}),
        }
        for index, item in enumerate(list_items)
    ]

    return JSONResponse(content=items_details)
