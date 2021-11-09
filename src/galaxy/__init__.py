from .app import Mapathon, Database,Output,DataQuality
import logging
from configparser import ConfigParser

config = ConfigParser()
config.read("src/config.txt")


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

__all__ = [
    'Mapathon',
    'Database',
    'Output',
    'DataQuality'
]