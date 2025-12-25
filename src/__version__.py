"""Version information for Raw Data API"""

try:
    from importlib.metadata import version

    __version__ = version("raw-data-api")
except Exception:
    __version__ = "unknown"
