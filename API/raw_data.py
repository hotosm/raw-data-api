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
from fastapi.responses import StreamingResponse
from datetime import datetime
import geojson
import io
import time
import zipfile
from io import BytesIO
router = APIRouter(prefix="/raw-data")
import logging

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

@router.post("/historical-snapshot/")
def get_historical_data(params:RawDataHistoricalParams):
    start_time = time.time()
    result= RawData(params).extract_historical_data()
    return generate_rawdata_response(result,start_time)

@router.post("/current-snapshot/")
def get_current_data(params:RawDataCurrentParams):
    start_time = time.time()
    result= RawData(params).extract_current_data()
    rpnse=generate_rawdata_response(result,start_time)
    return rpnse

def generate_rawdata_response(result,start_time):
    stream = io.StringIO()
    
    logging.debug('Geojson Dumping Started !')
    geojson.dump(result[0][0],stream)
    logging.debug('Zip Binding Started !')

    in_memory = BytesIO()
    zf = zipfile.ZipFile(in_memory, "w" , zipfile.ZIP_DEFLATED)
    exportname =f"Raw_Data_{datetime.now().isoformat()}"
    # Compressing geojson file in memory 
    zf.writestr(f"""{exportname}.geojson""",stream.getvalue())
    zf.close()
    # print(in_memory)
    logging.debug('Zip Binding Done !')

    response = StreamingResponse(iter([in_memory.getvalue()]),media_type="application/zip")
    response.headers["Content-Disposition"] = f"attachment; filename={exportname}.zip"
    print("-----Raw Data Request Took-- %s seconds -----" % (time.time() - start_time))
    return response
    