import re
from typing import List

from celery.result import AsyncResult
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi_versioning import version

from src.validation.models import SnapshotTaskResponse

from .api_worker import celery
from .auth import AuthUser, admin_required, login_required, staff_required

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/status/{task_id}/", response_model=SnapshotTaskResponse)
@version(1)
def get_task_status(task_id):
    """Tracks the request from the task id provided by Raw Data API  for the request

    Args:

        task_id ([type]): [Unique id provided on response from /snapshot/]

    Returns:

        id: Id of the task
        status : SUCCESS / PENDING
        result : Result of task

    Successful task will have additional nested json inside

    """
    task_result = AsyncResult(task_id, app=celery)
    result = {
        "id": task_id,
        "status": task_result.state,
        "result": task_result.result if task_result.status == "SUCCESS" else None,
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
def inspect_workers():
    """Inspects tasks assigned to workers

    Returns:
        scheduled: All scheduled tasks to be picked up by workers
        active: Current Active tasks ongoing on workers
    """
    inspected = celery.control.inspect()

    def extract_file_name(args: str) -> str:
        """Extract file_name using a pattern match."""
        match = re.search(r"file_name\s*=\s*['\"]([^'\"]+)['\"]", args)
        return match.group(1) if match else None

    def filter_task_details(tasks: List[dict]) -> List[dict]:
        """Filter task details to include only id and file_name."""
        filtered_tasks = {}
        if tasks:
            for worker in tasks:
                filtered_tasks[worker] = {"total": 0, "detail": []}
                if tasks[worker]:
                    # key is worker name here
                    for value_task in tasks[worker]:
                        if value_task:
                            if "id" in value_task:
                                task_id = value_task.get("id")
                                args = value_task.get("args")
                                file_name = extract_file_name(str(args))
                                if task_id:
                                    filtered_tasks[worker]["total"] += 1
                                    filtered_tasks[worker]["detail"].append(
                                        {"id": task_id, "file_name": file_name}
                                    )
        return filtered_tasks

    scheduled_tasks = inspected.scheduled()
    # print(scheduled_tasks)
    active_tasks = inspected.active()
    # print(active_tasks)
    response_data = {
        "scheduled": filter_task_details(scheduled_tasks),
        "active": filter_task_details(active_tasks),
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
