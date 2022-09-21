import os
import pathlib
import orjson
import shutil
from datetime import datetime as dt
import zipfile
from celery import Celery
from src.galaxy.config import config
from fastapi.responses import JSONResponse
from src.galaxy.query_builder.builder import format_file_name_str
from src.galaxy.validation.models import RawDataOutputType
from src.galaxy.app import RawData, S3FileTransfer
from src.galaxy.config import use_s3_to_upload, logger as logging, config

celery = Celery(__name__)
celery.conf.broker_url = config.get(
    "CELERY", "CELERY_BROKER_URL", fallback="redis://localhost:6379"
)
celery.conf.result_backend = config.get(
    "CELERY", "CELERY_RESULT_BACKEND", fallback="redis://localhost:6379"
)  # using redis as backend , make sure you have redis server started on your system on port 6379

celery.conf.task_serializer = 'pickle'
celery.conf.result_serializer = 'json'
celery.conf.accept_content = ['application/json', 'application/x-python-serialize']


@celery.task(bind=True,name="process_raw_data")
def process_raw_data(self, incoming_scheme, incoming_host, params):
    start_time = dt.now()
    if (
        params.output_type is None
    ):  # if no ouput type is supplied default is geojson output
        params.output_type = RawDataOutputType.GEOJSON.value

    # unique id for zip file and geojson for each export
    if params.file_name:
        # need to format string from space to _ because it is filename , may be we need to filter special character as well later on
        formatted_file_name = format_file_name_str(params.file_name)
        # exportname = f"{formatted_file_name}_{datetime.now().isoformat()}_{str(self.request.id)}"
        exportname = f"""{formatted_file_name}_{str(self.request.id)}_{params.output_type}"""  # disabled date for now

    else:
        # exportname = f"Raw_Export_{datetime.now().isoformat()}_{str(self.request.id)}"
        exportname = f"Raw_Export_{str(self.request.id)}_{params.output_type}"

    logging.info("Request %s received", exportname)

    dump_temp_file, geom_area, root_dir_file = RawData(params).extract_current_data(
        exportname
    )
    path = f"""{root_dir_file}{exportname}/"""

    if os.path.exists(path) is False:
        return JSONResponse(status_code=400, content={"Error": "Request went too big"})

    logging.debug("Zip Binding Started !")
    # saving file in temp directory instead of memory so that zipping file will not eat memory
    zip_temp_path = f"""{root_dir_file}{exportname}.zip"""
    zf = zipfile.ZipFile(zip_temp_path, "w", zipfile.ZIP_DEFLATED)

    directory = pathlib.Path(path)
    for file_path in directory.iterdir():
        zf.write(file_path, arcname=file_path.name)

    # Compressing geojson file
    zf.writestr("clipping_boundary.geojson",
                orjson.dumps(dict(params.geometry)))

    zf.close()
    logging.debug("Zip Binding Done !")
    inside_file_size = 0
    for temp_file in dump_temp_file:
        # clearing tmp geojson file since it is already dumped to zip file we don't need it anymore
        if os.path.exists(temp_file):
            inside_file_size += os.path.getsize(temp_file)

    # remove the file that are just binded to zip file , we no longer need to store it
    remove_file(path)

    # check if download url will be generated from s3 or not from config
    if use_s3_to_upload:
        file_transfer_obj = S3FileTransfer()
        download_url = file_transfer_obj.upload(zip_temp_path, exportname)
    else:

        # getting from config in case api and frontend is not hosted on same url
        client_host = config.get(
            "API_CONFIG",
            "api_host",
            fallback=f"""{incoming_scheme}://{incoming_host}""",
        )
        client_port = config.get("API_CONFIG", "api_port", fallback=8000)

        if client_port:
            download_url = f"""{client_host}:{client_port}/v1/exports/{exportname}.zip"""  # disconnected download portion from this endpoint because when there will be multiple hits at a same time we don't want function to get stuck waiting for user to download the file and deliver the response , we want to reduce waiting time and free function !
        else:
            download_url = f"""{client_host}/v1/exports/{exportname}.zip"""  # disconnected download portion from this endpoint because when there will be multiple hits at a same time we don't want function to get stuck waiting for user to download the file and deliver the response , we want to reduce waiting time and free function !

    # getting file size of zip , units are in bytes converted to mb in response
    zip_file_size = os.path.getsize(zip_temp_path)
    response_time = dt.now() - start_time
    response_time_str = str(response_time)
    logging.info(
        f"Done Export : {exportname} of {round(inside_file_size/1000000)} MB / {geom_area} sqkm in {response_time_str}"
    )

    return {
        "download_url": download_url,
        "file_name": exportname,
        "response_time": response_time_str,
        "query_area": f"{geom_area} Sq Km ",
        "binded_file_size": f"{round(inside_file_size/1000000)} MB",
        "zip_file_size_bytes": zip_file_size,
    }


def remove_file(path: str) -> None:
    """Used for removing temp file dir and its all content after zip file is delivered to user"""
    try:
        shutil.rmtree(path)
    except OSError as ex:
        logging.error("Error: %s - %s.", ex.filename, ex.strerror)
