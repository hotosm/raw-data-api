# Copyright (C) 2021 Humanitarian OpenStreetmap Team

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Humanitarian OpenStreetmap Team
# 1100 13th Street NW Suite 800 Washington, D.C. 20005
# <info@hotosm.org>

"""[Router Responsible for Raw data API ]
"""
import os
from uuid import uuid4
import json
from os.path import exists
from src.galaxy import config
from starlette.background import BackgroundTasks
import orjson
import logging
from http.client import REQUEST_ENTITY_TOO_LARGE
from fastapi import APIRouter, Depends, Request
from src.galaxy.query_builder.builder import remove_spaces
from src.galaxy.validation.models import RawDataHistoricalParams, RawDataCurrentParams
from .auth import login_required
from src.galaxy.app import RawData
from fastapi.responses import FileResponse, StreamingResponse
from datetime import datetime
import time
import zipfile
router = APIRouter(prefix="/raw-data")
import logging
import orjson
import os 
from starlette.background import BackgroundTasks
from .auth import login_required
from src.galaxy import config
from os.path import exists
import json
from uuid import uuid4
from .auth import login_required
import pathlib
import shutil

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

# @router.post("/historical-snapshot/")
# def get_historical_data(params:RawDataHistoricalParams):
#     start_time = time.time()
#     result= RawData(params).extract_historical_data()
#     return generate_rawdata_response(result,start_time)


def remove_file(path: str) -> None:
    """Used for removing temp file dir and its all content after zip file is delivered to user
    """
    # os.unlink(path)
    try:
        shutil.rmtree(path)
    except OSError as e:
        logging.error("Error: %s - %s." % (e.filename, e.strerror))

@router.post("/current-snapshot/")
def get_current_data(params:RawDataCurrentParams,background_tasks: BackgroundTasks,request: Request):  
# def get_current_data(params:RawDataCurrentParams,background_tasks: BackgroundTasks, user_data=Depends(login_required)):
    start_time = time.time()
    logging.debug('Request Received from Raw Data API ')
    # logging.debug(params)

    # unique id for zip file and geojson for each export
    if params.file_name :
        formatted_file_name=remove_spaces(params.file_name) # need to format string from space to _ because it is filename , may be we need to filter special character as well later on
        # exportname = f"{formatted_file_name}_{datetime.now().isoformat()}_{str(uuid4())}"
        exportname = f"{formatted_file_name}_{str(uuid4())}" #disabled date for now

    else:
        # exportname = f"Raw_Export_{datetime.now().isoformat()}_{str(uuid4())}"
        exportname = f"Raw_Export_{str(uuid4())}"

    dump_temp_file, geom_area=RawData(params).extract_current_data(exportname)

    logging.debug('Zip Binding Started !')
    try:
        path = config.get("EXPORT_CONFIG", "path")
    except : 
        path = 'exports/' # first tries to import from config, if not defined creates exports in home directory 
    # saving file in temp directory instead of memory so that zipping file will not eat memory
    zip_temp_path = f"""{path}{exportname}.zip"""
    zf = zipfile.ZipFile(zip_temp_path, "w", zipfile.ZIP_DEFLATED)


    path=f"""{path}{exportname}/"""
    directory = pathlib.Path(path)
    for file_path in directory.iterdir():
        zf.write(file_path, arcname=file_path.name)

    # Compressing geojson file
    zf.writestr(f"""clipping_boundary.geojson""",
                orjson.dumps(dict(params.geometry)))

    zf.close()
    logging.debug('Zip Binding Done !')
    inside_file_size = 0
    for temp_file in dump_temp_file:
        # clearing tmp geojson file since it is already dumped to zip file we don't need it anymore
        if os.path.exists(temp_file):      
            inside_file_size += os.path.getsize(temp_file)
    
    background_tasks.add_task(remove_file, path)
    try:
        client_host = config.get("EXPORT_CONFIG", "api_host")  # getting from config in case api and frontend is not hosted on same url
    except:
        client_host = f"""{request.url.scheme}://{request.client.host}"""  # getting client host
    
    try :
        client_port = config.get("EXPORT_CONFIG", "api_port")
    except:
        client_port = None
    if client_port :
        download_url = f"""{client_host}:{client_port}/exports/{exportname}.zip"""  # disconnected download portion from this endpoint because when there will be multiple hits at a same time we don't want function to get stuck waiting for user to download the file and deliver the response , we want to reduce waiting time and free function !
    else :
        download_url = f"""{client_host}/exports/{exportname}.zip"""  # disconnected download portion from this endpoint because when there will be multiple hits at a same time we don't want function to get stuck waiting for user to download the file and deliver the response , we want to reduce waiting time and free function !

    response_time = time.time() - start_time
    # getting file size of zip , units are in bytes converted to mb in response
    zip_file_size = os.path.getsize(zip_temp_path)
    response_time_str=""
    if int(response_time) < 60:
        response_time_str = f"""{int(response_time)} Seconds"""
    else:
        minute = int(response_time/60)
        if minute >= 60 :
            Hour = int(response_time/60)
            response_time_str= f"""{int(Hour)} Hour"""
            minute=minute-60*int(Hour)
        response_time_str += f"""{minute} Minute"""
    logging.debug("-------Raw : %s MB, %s :-: %s, %s Sqkm, format-%s-------" %
                  (round(inside_file_size/1000000), response_time_str,params.file_name,geom_area,params.output_type))
    return {"download_url": download_url, "file_name": exportname, "response_time": response_time_str, "query_area": f"""{geom_area} Sq Km """, "binded_file_size": f"""{round(inside_file_size/1000000)} MB""", "zip_file_size_bytes": {zip_file_size}}

@router.get("/status/")
def check_current_db_status():
    """Gives status about DB update, Substracts with current time and last db update time"""
    result = RawData().check_status()
    response = f"""{result} ago"""
    return {"last_updated": response}




