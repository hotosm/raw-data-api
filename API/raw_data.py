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

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

# @router.post("/historical-snapshot/")
# def get_historical_data(params:RawDataHistoricalParams):
#     start_time = time.time()
#     result= RawData(params).extract_historical_data()
#     return generate_rawdata_response(result,start_time)

def remove_file(path: str) -> None:
    os.unlink(path)

@router.post("/current-snapshot/")
def get_current_data(params:RawDataCurrentParams,background_tasks: BackgroundTasks):
    start_time = time.time()
    logging.debug('Request Received from Raw Data API ')
    result= RawData(params).extract_current_data()
    logging.debug('Zip Binding Started !')
    # in_memory = BytesIO()
    exportname =f"Raw_Export_{datetime.now().isoformat()}"
    #saving file in temp directory instead of memory so that zipping file will not eat memory 
    temp_path=f"""tmp/{exportname}.zip"""
    zf = zipfile.ZipFile(temp_path, "w" , zipfile.ZIP_DEFLATED)
    # Compressing geojson file
    zf.writestr(f"""{exportname}.geojson""",orjson.dumps(result))
    zf.close()
    logging.debug('Zip Binding Done !')
    response = FileResponse(temp_path,media_type="application/zip")
    response.headers["Content-Disposition"] = f"attachment; filename={exportname}.zip"
    print("-----Raw Data Request Took-- %s seconds -----" % (time.time() - start_time))
    background_tasks.add_task(remove_file, temp_path)
    return response
    