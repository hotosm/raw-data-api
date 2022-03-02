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
from fastapi import APIRouter, Depends
from src.galaxy.validation.models import RawDataHistoricalParams , RawDataCurrentParams
from .auth import login_required
from src.galaxy.app import RawData
from fastapi.responses import FileResponse
from datetime import datetime
import time
import zipfile
router = APIRouter(prefix="/raw-data")
import logging
import orjson
import os 
from starlette.background import BackgroundTasks
from .auth import login_required

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

# @router.post("/historical-snapshot/")
# def get_historical_data(params:RawDataHistoricalParams):
#     start_time = time.time()
#     result= RawData(params).extract_historical_data()
#     return generate_rawdata_response(result,start_time)

def remove_file(path: str) -> None:
    """Used for removing temp file after zip file is delivered to user
    """
    os.unlink(path)

@router.post("/current-snapshot/")
def get_current_data(params:RawDataCurrentParams,background_tasks: BackgroundTasks, user_data=Depends(login_required)):
    start_time = time.time()
    logging.debug('Request Received from Raw Data API ')
    exportname =f"Raw_Export_{datetime.now().isoformat()}"
    dump_geojson_temp_file= RawData(params).extract_current_data(exportname)
    logging.debug('Zip Binding Started !')
    # in_memory = BytesIO()
    
    #saving file in temp directory instead of memory so that zipping file will not eat memory 
    zip_temp_path=f"""data/{exportname}.zip"""
    zf = zipfile.ZipFile(zip_temp_path, "w" , zipfile.ZIP_DEFLATED)
    # Compressing geojson file
    zf.writestr(f"""clipping_boundary.geojson""",orjson.dumps(dict(params.geometry)))
    zf.write(dump_geojson_temp_file)
    
    zf.close()
    logging.debug('Zip Binding Done !')
    response = FileResponse(zip_temp_path,media_type="application/zip")
    response.headers["Content-Disposition"] = f"attachment; filename={exportname}.zip"
    print("-----Raw Data Request Took-- %s seconds -----" % (time.time() - start_time))
    background_tasks.add_task(remove_file, zip_temp_path) #clearing the tmp zip file 
    background_tasks.add_task(remove_file, dump_geojson_temp_file) # clearing tmp geojson file 
    
    return response
    