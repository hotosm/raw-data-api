from geojson_stats.stats import Stats
from geojson_stats.html import Html

CONFIG_AREA = ["building"]
CONFIG_LENGTH = ["highway", "waterway"]


class GeoJSONStats(Stats):
    """Used for collecting stats while processing GeoJSON files line by line"""

    def __init__(self, filters, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config.clean = True
        self.config.properties_prop = "properties.tags"

        if filters and filters.tags:
            for tag in CONFIG_AREA:
                if self.check_filter(filters.tags, tag):
                    self.config.keys.append(tag)
                    self.config.value_keys.append(tag)
                    self.config.area = True

            for tag in CONFIG_LENGTH:
                if self.check_filter(filters.tags, tag):
                    self.config.keys.append(tag)
                    self.config.value_keys.append(tag)
                    self.config.length = True

    def check_filter(self, tags, tag):
        """
        Check if a tag is present in tag filters
        """

        if tags.all_geometry:
            if tags.all_geometry.join_or and tag in tags.all_geometry.join_or:
                return True
            if tags.all_geometry.join_and and tag in tags.all_geometry.join_and:
                return True
        if tags.polygon:
            if tags.polygon.join_or and tag in tags.polygon.join_or:
                return True
            if tags.polygon.join_and and tag in tags.polygon.join_and:
                return True
        if tags.line:
            if tags.line.join_or and tag in tags.line.join_or:
                return True
            if tags.line.join_and and tag in tags.line.join_and:
                return True

    def raw_data_line_stats(self, json_object: dict):
        """
        Process a GeoJSON line (for getting stats) and return that line
        """
        self.get_object_stats(json_object)

    def html(self, tpl):
        """
        Returns stats Html object, generated from stats data using a template
        """
        return Html(tpl, self)
