from celery.result import AsyncResult
from .api_worker import celery
from fastapi import APIRouter
from fastapi_versioning import version
from fastapi.responses import JSONResponse


router = APIRouter(prefix="/tasks")


@router.get("/status/{task_id}/")
@version(2)
def get_task_status(task_id):
    """Tracks the request from the task id provided by galaxy api for the request

    Args:

        task_id ([type]): [Unique id provided on response from /current-snapshot/]

    Returns:

        id: Id of the task
        status : SUCCESS / PENDING
        result : Result of task

    Successful task will have additional nested json inside row as following :
    Example response of rawdata current snapshot response :


        {
            "id": "3fded368-456f-4ef4-a1b8-c099a7f77ca4",
            "status": "SUCCESS",
            "result": {
                "download_url": "https://s3.us-east-1.amazonaws.com/exports-stage.hotosm.org/Raw_Export_3fded368-456f-4ef4-a1b8-c099a7f77ca4_GeoJSON.zip",
                "file_name": "Raw_Export_3fded368-456f-4ef4-a1b8-c099a7f77ca4_GeoJSON",
                "response_time": "0:00:12.175976",
                "query_area": "6 Sq Km ",
                "binded_file_size": "7 MB",
                "zip_file_size_bytes": 1331601

        }

    """
    task_result = AsyncResult(task_id, app=celery)
    result = { "id": task_id, "status": task_result.state, "result": task_result.result if task_result.status == 'SUCCESS' else None }
    return JSONResponse(result)