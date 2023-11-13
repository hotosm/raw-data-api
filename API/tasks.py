from celery.result import AsyncResult
from celery.task.control import revoke
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi_versioning import version

from src.validation.models import SnapshotTaskResponse

from .api_worker import celery

router = APIRouter(prefix="/tasks")


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


@router.get("revoke/{task_id}/")
@version(1)
def revoke_task(task_id):
    revoked_task = revoke(task_id, terminate=True)
    print(revoked_task)
    return JSONResponse({"id": task_id, "status": revoked_task})
