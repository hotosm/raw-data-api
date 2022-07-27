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

"""[Router Responsible for downloading exports ]
"""
from fastapi import APIRouter
from fastapi_versioning import  version
from src.galaxy.config import export_path
from fastapi.responses import FileResponse
from os.path import exists



router = APIRouter(prefix="")

@router.get("/exports/{file_name}")
@version(1,0)
def download_export(file_name: str):
    """Used for Delivering our export to user.
    Returns zip file if it is present on our server if not returns error 
    """
    zip_temp_path = f"""{export_path}{file_name}"""
    if exists(zip_temp_path):
        response = FileResponse(zip_temp_path, media_type="application/zip")
        response.headers["Content-Disposition"] = f"attachment; filename={file_name}"
        return response
    else:
        raise ValueError("File Doesn't Exist or have been cleared up from system")
