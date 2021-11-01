from .app import Mapathon, Database
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

__all__ = [
    'Mapathon',
    'Database'
]