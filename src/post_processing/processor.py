
import json
from .transliterator import Transliterator
from .geojson_stats import GeoJSONStats

class PostProcessor():
    """Used for posst-process data while processing GeoJSON files line by line"""

    options = {}
    filters = {}
    functions = []

    def __init__(self, options, *args, **kwargs):
        self.options = options

    def post_process_line(self, line: str):
        """
        Parses line, run functions over it and returns it
        """

        line_object = json.loads(line)

        for fn in self.functions:
           fn(line_object)

        return json.dumps(line_object)
    
    def init(self):
        """
        Initialize post-processor
        """

        if self.options["include_stats"]:
            self.geoJSONStats = GeoJSONStats(self.filters)
            self.functions.append(self.geoJSONStats.raw_data_line_stats)

        if self.options["include_translit"]:
            self.transliterator = Transliterator()
            self.functions.append(self.transliterator.translit)