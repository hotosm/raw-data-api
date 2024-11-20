import json
from .transliterator import Transliterator
from .geojson_stats import GeoJSONStats
import os
import pathlib


class PostProcessor:
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

    def custom(self, categories, export_format_path, export_filename):
        """
        Post-process custom exports
        """
        self.geoJSONStats.config.properties_prop = "properties"

        category_tag = ""
        if any("Roads" in element for element in categories):
            category_tag = "highway"
            self.geoJSONStats.config.length = True
        elif any("Buildings" in element for element in categories):
            category_tag = "building"
            self.geoJSONStats.config.area = True
        elif any("Waterways" in element for element in categories):
            category_tag = "Waterway"
            self.geoJSONStats.config.length = True

        if self.options["include_stats"]:
            if category_tag:
                self.geoJSONStats.config.keys.append(category_tag)
                self.geoJSONStats.config.value_keys.append(category_tag)

                path_input = os.path.join(
                    export_format_path, f"{export_filename}.geojson"
                )
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

                if self.options["include_translit"]:
                    os.remove(path_input)
                    os.rename(path_output, path_input)
                else:
                    os.remove(path_output)

                    geojson_stats_json = json.dumps(self.geoJSONStats.dict())
                    with open(
                        os.path.join(
                            export_format_path, f"{export_filename}-stats.json"
                        ),
                        "w",
                    ) as f:
                        f.write(geojson_stats_json)

                if self.options["include_stats_html"]:
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
                    geojson_stats_html = self.geoJSONStats.html(tpl_path).build()
                    upload_html_path = os.path.join(
                        export_format_path, f"{export_filename}-stats.html"
                    )
                    with open(upload_html_path, "w") as f:
                        f.write(geojson_stats_html)

    def init(self):
        """
        Initialize post-processor
        """

        if "include_stats" in self.options and self.options["include_stats"]:
            self.geoJSONStats = GeoJSONStats(self.filters)
            self.functions.append(self.geoJSONStats.raw_data_line_stats)

        if "include_translit" in self.options and self.options["include_translit"]:
            self.transliterator = Transliterator()
            self.functions.append(self.transliterator.translit)
