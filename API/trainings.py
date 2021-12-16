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

"""[Router Responsible for training data API ]
"""
from fastapi import APIRouter, Depends
from src.galaxy.app import Training
from src.galaxy.validation.models import TrainingOrganisations, TrainingParams , Trainings
from .auth import login_required
from typing import List
router = APIRouter(prefix="/training")


@router.get("/organisations", response_model=List[TrainingOrganisations])
# def get_organisations_list(user_data=Depends(login_required)):
def get_organisations_list():
    training = Training("underpass")
    return training.get_all_organisations()

@router.post("",response_model=List[Trainings])
# def get_organisations_list(user_data=Depends(login_required)):
def get_trainings_list(params:TrainingParams):
    training= Training("underpass")
    return training.get_trainingslist(params)
