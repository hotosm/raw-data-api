import os
import pathlib
import re
import shutil
import time
import zipfile
from datetime import datetime as dt

import requests
from celery import Celery

from src.app import RawData, S3FileTransfer
from src.config import ALLOW_BIND_ZIP_FILTER
from src.config import CELERY_BROKER_URL as celery_broker_uri
from src.config import CELERY_RESULT_BACKEND as celery_backend
from src.config import ENABLE_TILES
from src.config import USE_S3_TO_UPLOAD as use_s3_to_upload
from src.config import logger as logging
from src.query_builder.builder import format_file_name_str
from src.validation.models import RawDataOutputType

celery = Celery(__name__)
celery.conf.broker_url = celery_broker_uri
celery.conf.result_backend = celery_backend
celery.conf.task_serializer = "pickle"
celery.conf.result_serializer = "pickle"
celery.conf.accept_content = ["application/json", "application/x-python-serialize"]


@celery.task(bind=True, name="process_raw_data")
def process_raw_data(self, params):
    try:
        start_time = dt.now()
        bind_zip = params.bind_zip if ALLOW_BIND_ZIP_FILTER else True
        # unique id for zip file and geojson for each export
        params.output_type = (
            params.output_type
            if params.output_type
            else RawDataOutputType.GEOJSON.value
        )
        if ENABLE_TILES:
            if (
                params.output_type == RawDataOutputType.PMTILES.value
                or params.output_type == RawDataOutputType.MBTILES.value
            ):
                logging.debug("Using STwithin Logic")
                params.use_st_within = True
        params.file_name = (
            format_file_name_str(params.file_name) if params.file_name else "Export"
        )
        logging.info("Is Default Export ? : %s", params.uuid)
        exportname = f"{params.file_name}_{params.output_type}{f'_uid_{str(self.request.id)}' if params.uuid else ''}"

        logging.info("Request %s received", exportname)

        geom_area, geom_dump, working_dir = RawData(params).extract_current_data(
            exportname
        )
        inside_file_size = 0
        if bind_zip:
            logging.debug("Zip Binding Started !")
            # saving file in temp directory instead of memory so that zipping file will not eat memory
            upload_file_path = os.path.join(working_dir, os.pardir, f"{exportname}.zip")

            zf = zipfile.ZipFile(upload_file_path, "w", zipfile.ZIP_DEFLATED)
            for file_path in pathlib.Path(working_dir).iterdir():
                zf.write(file_path, arcname=file_path.name)
                inside_file_size += os.path.getsize(file_path)

            # Compressing geojson file
            zf.writestr("clipping_boundary.geojson", geom_dump)

            zf.close()
            logging.debug("Zip Binding Done !")
        else:
            for file_path in pathlib.Path(working_dir).iterdir():
                if file_path.is_file() and file_path.name.endswith(
                    params.output_type.lower()
                ):
                    upload_file_path = file_path
                    inside_file_size += os.path.getsize(file_path)
                    break  # only take one file inside dir , if contains many it should be inside zip
        # check if download url will be generated from s3 or not from config
        if use_s3_to_upload:
            file_transfer_obj = S3FileTransfer()
            upload_name = exportname if params.uuid else f"Recurring/{exportname}"
            if exportname.startswith("hotosm_project"):
                if not params.uuid:
                    pattern = r"(hotosm_project_)(\d+)"
                    match = re.match(pattern, exportname)
                    if match:
                        prefix = match.group(1)
                        project_number = match.group(2)
                        if project_number:
                            upload_name = f"TM/{project_number}/{exportname}"
            download_url = file_transfer_obj.upload(
                upload_file_path,
                upload_name,
                file_suffix="zip" if bind_zip else params.output_type.lower(),
            )
        else:
            # give the static file download url back to user served from fastapi static export path
            download_url = str(upload_file_path)

        # getting file size of zip , units are in bytes converted to mb in response
        zip_file_size = os.path.getsize(upload_file_path)
        # watches the status code of the link provided and deletes the file if it is 200
        if use_s3_to_upload:
            watch_s3_upload(download_url, upload_file_path)
        if use_s3_to_upload or bind_zip:
            # remove working dir from the machine , if its inside zip / uploaded we no longer need it
            remove_file(working_dir)
        response_time = dt.now() - start_time
        response_time_str = str(response_time)
        logging.info(
            f"Done Export : {exportname} of {round(inside_file_size/1000000)} MB / {geom_area} sqkm in {response_time_str}"
        )
        return {
            "download_url": download_url,
            "file_name": params.file_name,
            "process_time": response_time_str,
            "query_area": f"{round(geom_area,2)} Sq Km",
            "binded_file_size": f"{round(inside_file_size/1000000,2)} MB",
            "zip_file_size_bytes": zip_file_size,
        }

    except Exception as ex:
        raise ex


def remove_file(path: str) -> None:
    """Used for removing temp file dir and its all content after zip file is delivered to user"""
    try:
        shutil.rmtree(path)
    except OSError as ex:
        logging.error("Error: %s - %s.", ex.filename, ex.strerror)


def watch_s3_upload(url: str, path: str) -> None:
    """Watches upload of s3 either it is completed or not and removes the temp file after completion

    Args:
        url (_type_): url generated by the script where data will be available
        path (_type_): path where temp file is located at
    """
    start_time = time.time()
    remove_temp_file = True
    check_call = requests.head(url).status_code
    if check_call != 200:
        logging.debug("Upload is not done yet waiting ...")
        while check_call != 200:  # check until status is not green
            check_call = requests.head(url).status_code
            if time.time() - start_time > 300:
                logging.error(
                    "Upload time took more than 5 min , Killing watch : %s , URL : %s",
                    path,
                    url,
                )
                remove_temp_file = False  # don't remove the file if upload fails
                break
            time.sleep(3)  # check each 3 second
    # once it is verfied file is uploaded finally remove the file
    if remove_temp_file:
        logging.debug("File is uploaded at %s , flushing out from %s", url, path)
        os.unlink(path)
