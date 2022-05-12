from ..validation.models import BaseModel
from typing import Optional


class ValidatorStatsRequest(BaseModel):
    year: int = 2012
    country: Optional[str] = None
    organisation: Optional[str] = None
