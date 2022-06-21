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

from csv import DictWriter
from fastapi import APIRouter
from src.galaxy.validation.models import DataQuality_TM_RequestParams,DataQuality_username_RequestParams,DataQualityHashtagParams,OutputType
from src.galaxy.app import DataQuality, DataQualityHashtags
from fastapi.responses import StreamingResponse
import io
from datetime import datetime

router = APIRouter(prefix="/data-quality")


@router.post("/hashtag-reports/")
def data_quality_hashtag_reports(params: DataQualityHashtagParams):
    data_quality = DataQualityHashtags(params)

    results = data_quality.get_report()

    if params.output_type == OutputType.GEOJSON.value:
        return results

    # Set Response as streaming for CSV files.
    csv_stream = DataQualityHashtags.to_csv_stream(results)

    response = StreamingResponse(csv_stream)
    exportname =f"DataQuality_Hashtags_{datetime.now().isoformat()}"
    response.headers["Content-Disposition"] = f"attachment; filename={exportname}.csv"

    return response


@router.post("/project-reports/")
def data_quality_reports(params: DataQuality_TM_RequestParams):
    data_quality = DataQuality(params,"TM")

    if params.output_type == OutputType.GEOJSON.value:
        return data_quality.get_report()

    stream = io.StringIO()
    exportname =f"TM_DataQuality_{datetime.now().isoformat()}"
    data_quality.get_report_as_csv(stream)
    response = StreamingResponse(iter([stream.getvalue()]),
                            media_type="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename="+exportname+".csv"
    return response


@router.post("/user-reports/")
def data_quality_reports(params: DataQuality_username_RequestParams):
    data_quality = DataQuality(params,"username")
    
    if params.output_type == OutputType.GEOJSON.value:
        return data_quality.get_report()
    stream = io.StringIO()
    exportname =f"Username_DataQuality_{datetime.now().isoformat()}"
    data_quality.get_report_as_csv(stream)
    response = StreamingResponse(iter([stream.getvalue()]),
                            media_type="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename="+exportname+".csv"
    return response

