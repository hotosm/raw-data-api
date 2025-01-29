import json
from .transliterator import Transliterator
from .geojson_stats import GeoJSONStats
import os
import pathlib

CATEGORIES_CONFIG = {
    "roads": {
        "tag": "highway", "length": True, "area": False
    },
    "buildings": {
        "tag": "building", "length": False, "area": True
    },
    "waterways": {
        "tag": "waterway", "length": True, "area": False
    },
    "railways": {
        "tag": "railway", "length": True, "area": False
    },
    "default": {
        "tag": None, "length": False, "area": False
    },
}

class PostProcessor:
    """Used for post-process GeoJSON files"""

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

    def get_categories_config(self, category_name):
        config = CATEGORIES_CONFIG.get(category_name)
        return config if config else CATEGORIES_CONFIG["default"]

    def custom(
        self, category_name, export_format_path, export_filename, file_export_path
    ):
        """
        Post-process custom exports
        """
        self.geoJSONStats.config.properties_prop = "properties"

        category_config = self.get_categories_config(category_name)
        category_tag = category_config["tag"]
        self.geoJSONStats.config.length = category_config["length"]
        self.geoJSONStats.config.area = category_config["area"]

        if self.options["include_stats"]:

            path_input = os.path.join(export_format_path, f"{export_filename}.geojson")
            path_output = os.path.join(
                export_format_path, f"{export_filename}-post.geojson"
            )

            with open(path_input, "r") as input_file, open(
                path_output, "w"
            ) as output_file:
                for line in input_file:
                    comma = False
                    if line.startswith('{ "type": "Feature"'):
                        json_string = ""
                        if line[-2:-1] == ",":
                            json_string = line[:-2]
                            comma = True
                        else:
                            json_string = line
                        line = self.post_process_line(json_string)
                    if self.options["include_translit"]:
                        if comma:
                            output_file.write(line + ",")
                        else:
                            output_file.write(line)

            if self.options.get("include_translit"):
                os.remove(path_input)
                os.rename(path_output, path_input)
            else:
                os.remove(path_output)

            geojson_stats_json = json.dumps(self.geoJSONStats.dict())
            with open(
                os.path.join(file_export_path, "stats.json"),
                "w",
            ) as f:
                f.write(geojson_stats_json)

            if self.options.get("include_stats_html"):
                tpl = (
                    "stats_{category_tag}".format(category_tag=category_tag)
                    if category_tag
                    else "stats"
                )
                project_root = pathlib.Path(__file__).resolve().parent
                tpl_path = os.path.join(
                    project_root,
                    "{tpl}_tpl.html".format(tpl=tpl),
                )
                geojson_stats_html = self.geoJSONStats.html(tpl_path, {"title": f"{export_filename}.geojson"}).build()
                upload_html_path = os.path.join(file_export_path, "stats-summary.html")
                with open(upload_html_path, "w") as f:
                    f.write(geojson_stats_html)

    def init(self):
        """
        Initialize post-processor
        """

        if self.options.get("include_stats"):
            self.geoJSONStats = GeoJSONStats(self.filters)
            self.functions.append(self.geoJSONStats.raw_data_line_stats)

        if self.options.get("include_translit"):
            self.transliterator = Transliterator()
            self.functions.append(self.transliterator.translit)
