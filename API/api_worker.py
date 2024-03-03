import json
import os
import pathlib
import re
import shutil
import time
from datetime import datetime as dt
from datetime import timedelta, timezone

import humanize
import requests
from celery import Celery

from src.app import CustomExport, PolygonStats, RawData, S3FileTransfer
from src.config import ALLOW_BIND_ZIP_FILTER
from src.config import CELERY_BROKER_URL as celery_broker_uri
from src.config import CELERY_RESULT_BACKEND as celery_backend
from src.config import (
    DEFAULT_HARD_TASK_LIMIT,
    DEFAULT_README_TEXT,
    DEFAULT_SOFT_TASK_LIMIT,
    ENABLE_SOZIP,
    ENABLE_TILES,
    HDX_HARD_TASK_LIMIT,
    HDX_SOFT_TASK_LIMIT,
)
from src.config import USE_S3_TO_UPLOAD as use_s3_to_upload
from src.config import WORKER_PREFETCH_MULTIPLIER
from src.config import logger as logging
from src.query_builder.builder import format_file_name_str
from src.validation.models import (
    DatasetConfig,
    DynamicCategoriesModel,
    RawDataCurrentParams,
    RawDataOutputType,
)

if ENABLE_SOZIP:
    import sozipfile.sozipfile as zipfile
else:
    from zipfile import zipfile

celery = Celery("Raw Data API")
celery.conf.broker_url = celery_broker_uri
celery.conf.result_backend = celery_backend
# celery.conf.task_serializer = "pickle"
# celery.conf.result_serializer = "json"
# celery.conf.accept_content = ["application/json", "application/x-python-serialize"]
celery.conf.task_track_started = True
celery.conf.update(result_extended=True)
celery.conf.task_reject_on_worker_lost = True
celery.conf.task_acks_late = True

if WORKER_PREFETCH_MULTIPLIER:
    celery.conf.update(worker_prefetch_multiplier=WORKER_PREFETCH_MULTIPLIER)


@celery.task(
    bind=True,
    name="process_raw_data",
    time_limit=DEFAULT_HARD_TASK_LIMIT,
    soft_time_limit=DEFAULT_SOFT_TASK_LIMIT,
)
def process_raw_data(self, params, user=None):
    if self.request.retries > 0:
        raise ValueError("Retry limit reached. Marking task as failed.")
    params = RawDataCurrentParams(**params)
    try:
        start_time = time.time()
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

        exportname = f"{params.file_name}_{params.output_type}{f'_uid_{str(self.request.id)}' if params.uuid else ''}"
        params.file_name = params.file_name.split("/")[
            -1
        ]  # get last item from list and consider it as a file rest is file path on s3
        exportname_parts = exportname.split("/")
        file_parts = os.path.join(*exportname_parts)
        logging.info(
            "Request %s received with following %s file_path",
            params.file_name,
            file_parts,
        )

        geom_area, geom_dump, working_dir = RawData(params).extract_current_data(
            file_parts
        )
        inside_file_size = 0
        polygon_stats = None
        if "include_stats" in params.dict():
            if params.include_stats:
                feature = {
                    "type": "Feature",
                    "geometry": json.loads(params.geometry.model_dump_json()),
                    "properties": {},
                }
                polygon_stats = PolygonStats(feature).get_summary_stats()
        if bind_zip:
            logging.debug("Zip Binding Started !")
            # saving file in temp directory instead of memory so that zipping file will not eat memory
            upload_file_path = os.path.join(
                working_dir, os.pardir, f"{exportname_parts[-1]}.zip"
            )

            zf = zipfile.ZipFile(
                upload_file_path,
                "w",
                compression=zipfile.ZIP_DEFLATED,
                allowZip64=True,
                chunk_size=zipfile.SOZIP_DEFAULT_CHUNK_SIZE,
            )
            for file_path in pathlib.Path(working_dir).iterdir():
                zf.write(file_path, arcname=file_path.name)
                inside_file_size += os.path.getsize(file_path)

            # Compressing geojson file
            zf.writestr("clipping_boundary.geojson", geom_dump)

            utc_now = dt.now(timezone.utc)
            utc_offset = utc_now.strftime("%z")
            # Adding metadata readme.txt
            readme_content = f"Exported Timestamp (UTC{utc_offset}): {utc_now.strftime('%Y-%m-%d %H:%M:%S')}\n"
            readme_content += DEFAULT_README_TEXT
            if polygon_stats:
                readme_content += f'{polygon_stats["summary"]["buildings"]}\n'
                readme_content += f'{polygon_stats["summary"]["roads"]}\n'
                readme_content += "Read about what this summary means: indicators: https://github.com/hotosm/raw-data-api/tree/develop/docs/src/stats/indicators.md,metrics: https://github.com/hotosm/raw-data-api/tree/develop/docs/src/stats/metrics.md"

            zf.writestr("Readme.txt", readme_content)

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
            upload_name = (
                f"default/{file_parts}" if params.uuid else f"recurring/{file_parts}"
            )
            logging.info(upload_name)

            if exportname.startswith("hotosm_project"):  # TM
                if not params.uuid:
                    pattern = r"(hotosm_project_)(\d+)"
                    match = re.match(pattern, exportname)
                    if match:
                        prefix = match.group(1)
                        project_number = match.group(2)
                        if project_number:
                            upload_name = f"TM/{project_number}/{exportname}"
            elif exportname.startswith("hotosm_"):  # HDX
                if not params.uuid:
                    pattern = r"hotosm_([A-Za-z]{3})_(\w+)"
                    match = re.match(pattern, exportname)

                    if match:
                        iso3countrycode = match.group(1)
                        if iso3countrycode:
                            upload_name = f"HDX/{iso3countrycode.upper()}/{exportname}"

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
        if use_s3_to_upload or bind_zip:
            # remove working dir from the machine , if its inside zip / uploaded we no longer need it
            remove_file(working_dir)
        response_time_str = humanize.naturaldelta(
            timedelta(seconds=(time.time() - start_time))
        )
        logging.info(
            f"Done Export : {exportname} of {round(inside_file_size/1000000)} MB / {geom_area} sqkm in {response_time_str}"
        )
        final_response = {
            "download_url": download_url,
            "file_name": params.file_name,
            "process_time": response_time_str,
            "query_area": f"{round(geom_area,2)} Sq Km",
            "binded_file_size": f"{round(inside_file_size/1000000,2)} MB",
            "zip_file_size_bytes": zip_file_size,
        }
        if polygon_stats:
            final_response["stats"] = polygon_stats
        return final_response

    except Exception as ex:
        raise ex


@celery.task(
    bind=True,
    name="process_custom_request",
    time_limit=HDX_HARD_TASK_LIMIT,
    soft_time_limit=HDX_SOFT_TASK_LIMIT,
)
def process_custom_request(self, params, user=None):
    if self.request.retries > 0:
        raise ValueError("Retry limit reached. Marking task as failed.")
    params = DynamicCategoriesModel(**params)

    if not params.dataset:
        params.dataset = DatasetConfig()
    custom_object = CustomExport(params)
    try:
        return custom_object.process_custom_categories()
    except Exception as ex:
        custom_object.clean_resources()
        raise ex


def remove_file(path: str) -> None:
    """Used for removing temp file dir and its all content after zip file is delivered to user"""
    try:
        shutil.rmtree(path)
    except OSError as ex:
        logging.error("Error: %s - %s.", ex.filename, ex.strerror)
