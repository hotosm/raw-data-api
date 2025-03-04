from geojson_stats.stats import Stats, Config
from geojson_stats.html import Html
import os
import pathlib

CATEGORIES_CONFIG = {
    "roads": {"tag": "highway", "length": True, "area": False},
    "buildings": {"tag": "building", "length": False, "area": True},
    "waterways": {"tag": "waterway", "length": True, "area": False},
    "railways": {"tag": "railway", "length": True, "area": False},
    "default": {"tag": None, "length": False, "area": False},
}


class PostProcessor:
    """Used for post-process GeoJSON files"""

    def __init__(self, options, *args, **kwargs):
        self.options = options

    def get_categories_config(self, category_name):
        """
        Get configuration for categories
        """
        config = CATEGORIES_CONFIG.get(category_name)
        return config if config else CATEGORIES_CONFIG["default"]

    def stats(
        self, category_name, export_format_path, export_filename, file_export_path
    ):
        """
        Post-process custom exports
        """

        # Get stats config
        category_config = self.get_categories_config(category_name)
        config = Config(
            clean=True,
            length=category_config["length"],
            area=category_config["area"],
            keys=category_config["tag"],
            value_keys=category_config["tag"],
        )

        if self.options["include_stats"]:
            # Generate stats
            path_input = os.path.join(export_format_path, f"{export_filename}.geojson")
            stats = Stats(config)
            stats.process_file_stream(path_input)
            del stats.results.key["osm_id"]
            stats_json = stats.json()

            # Save raw stats
            with open(
                os.path.join(file_export_path, "stats.json"),
                "w",
            ) as f:
                f.write(stats_json)

            # Save HTML stats
            if self.options.get("include_stats_html"):
                # Get template
                category_tag = category_config["tag"]
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

                # Generate HTML
                geojson_stats_html = Html(
                    tpl_path, stats, {"title": f"{export_filename}.geojson"}
                ).build()

                # Save HTML file
                upload_html_path = os.path.join(file_export_path, "stats-summary.html")
                with open(upload_html_path, "w") as f:
                    f.write(geojson_stats_html)
