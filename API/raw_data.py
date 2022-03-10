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
from fastapi import APIRouter, Depends,Request
from src.galaxy.validation.models import RawDataHistoricalParams , RawDataCurrentParams
from .auth import login_required
from src.galaxy.app import RawData
from fastapi.responses import FileResponse , StreamingResponse
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
from area import area
import json

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

# @router.post("/historical-snapshot/")
# def get_historical_data(params:RawDataHistoricalParams):
#     start_time = time.time()
#     result= RawData(params).extract_historical_data()
#     return generate_rawdata_response(result,start_time)

@router.get("/exports/{file_name}")
async def download_export(file_name: str,background_tasks: BackgroundTasks):
    """Used for Delivering our export to user , It will hold the zip file until user downloads or hits the url once it is delivered it gets cleared up, Designed as  a separate function to avoid the condition ( waiting for the api response without knowing what is happening on the background )
    Returns zip file if it is present on our server if not returns null 
    """
    zip_temp_path=f"""exports/{file_name}.zip"""
    if exists(zip_temp_path):
        response = FileResponse(zip_temp_path,media_type="application/zip")
        response.headers["Content-Disposition"] = f"attachment; filename={file_name}.zip"
        background_tasks.add_task(remove_file, zip_temp_path) #clearing the tmp zip file
        return response

def remove_file(path: str) -> None:
    """Used for removing temp file after zip file is delivered to user
    """
    os.unlink(path)

@router.post("/current-snapshot/")
async def get_current_data(params:RawDataCurrentParams,background_tasks: BackgroundTasks):  #using async function so that multiple request at a time won't get stuck
# def get_current_data(params:RawDataCurrentParams,background_tasks: BackgroundTasks, user_data=Depends(login_required)):
    start_time = time.time()
    logging.debug('Request Received from Raw Data API ')
    exportname =f"Raw_Export_{datetime.now().isoformat()}"
    dump_geojson_temp_file=RawData(params).extract_current_data(exportname)
    logging.debug('Zip Binding Started !')
    # in_memory = BytesIO()
    
    #saving file in temp directory instead of memory so that zipping file will not eat memory 
    zip_temp_path=f"""exports/{exportname}.zip"""
    zf = zipfile.ZipFile(zip_temp_path, "w" , zipfile.ZIP_DEFLATED)
    # Compressing geojson file
    zf.writestr(f"""clipping_boundary.geojson""",orjson.dumps(dict(params.geometry)))
    zf.write(dump_geojson_temp_file)
    
    zf.close()
    logging.debug('Zip Binding Done !')
    logging.debug("-----Raw Data Request Took-- %s seconds -----" % (time.time() - start_time))
    background_tasks.add_task(remove_file, dump_geojson_temp_file) # # clearing tmp geojson file since it is already dumped to zip file we don't need it anymore  

    client_host = dict(config.items("HOST"))['host'] #getting hosting url 
    client_port = dict(config.items("HOST"))['port'] #getting hosting port

    download_url=f"""{client_host}:{client_port}/raw-data/exports/{exportname}""" # disconnected download portion from this endpoint because when there will be multiple hits at a same time we don't want function to get stuck waiting for user to download the file and deliver the response , we want to reduce waiting time and free function ! 
    response_time=time.time() - start_time
    return {"download_url": download_url, "response_time": f"""{int(response_time)} Seconds""", "query_area" : f"""{int(area(json.loads(params.geometry.json()))* 1E-6)} Sq Km"""}
    