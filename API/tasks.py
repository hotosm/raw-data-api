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
        status: status of revoked task
    """
    revoked_task = celery.control.revoke(task_id=task_id, terminate=True)
    return JSONResponse({"id": task_id, "status": revoked_task})


@router.get("/inspect/")
@version(1)
def inspect_workers():
    """Inspects tasks assigned to workers

    Returns:
        scheduled: All scheduled tasks to be picked up by workers
        active: Current Active tasks ongoing on workers
    """
    inspected = celery.control.inspect()
    return JSONResponse(
        {"scheduled": str(inspected.scheduled()), "active": str(inspected.active())}
    )


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
