from fastapi import APIRouter
from src.galaxy.validation.models import DataQualityRequestParams
from src.galaxy.app import DataQuality
from src.galaxy import config

router = APIRouter(prefix="/data-quality")


@router.post("/report")
def data_quality_reports(params: DataQualityRequestParams):
    data_quality = DataQuality(dict(config.items("local")), params)
    return data_quality.get_report()
