from geojson_stats.stats import Stats
from geojson_stats.html import Html


class GeoJSONStats(Stats):
    """Used for collecting stats while processing GeoJSON files"""

    def __init__(self, filters, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config.clean = True
        self.config.properties_prop = "properties.tags"

    def raw_data_line_stats(self, json_object: dict):
        """
        Process a GeoJSON line (for getting stats) and return that line
        """
        self.get_object_stats(json_object)

    def html(self, tpl, tpl_params):
        """
        Returns stats Html object, generated from stats data using a template
        """
        return Html(tpl, self, tpl_params)
