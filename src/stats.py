# Standard library imports
import asyncio
import logging
from datetime import datetime

# Third party imports
import humanize
import requests
from geojson import dumps
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Reader imports
from postgres import AsyncPostgres


class PolygonStats:
    """Generates stats for polygon"""

    def __init__(self, geojson=None, iso3=None):
        """
        Initialize PolygonStats with the provided GeoJSON.

        Args:
            geojson (dict): GeoJSON representation of the polygon.
        """
        self.API_URL = POLYGON_STATISTICS_API_URL
        if geojson is None and iso3 is None:
            raise HTTPException(
                status_code=404, detail="Either geojson or iso3 should be passed"
            )

        if iso3:
            # Use AsyncPostgres to fetch data from the database
            self.db = AsyncPostgres("your_database_url")
            asyncio.run(self.db.establish_pool())
            iso3_query = get_country_geom_from_iso(iso3)
            result = asyncio.run(self.db.fetchrow(iso3_query))
            if result is None:
                raise HTTPException(status_code=404, detail="Invalid iso3 code")
            self.INPUT_GEOM = result[0]
        else:
            self.INPUT_GEOM = dumps(geojson)

        # Configure requests session with retries
        self.session = requests.Session()
        retry_strategy = Retry(total=3, backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    @staticmethod
    def get_building_pattern_statement(
        osm_building_count,
        ai_building_count,
        avg_timestamp,
        last_edit_timestamp,
        osm_building_count_6_months,
    ):
        """
        Translates building stats to a human-readable statement.

        Args:
            osm_building_count (int): Count of buildings from OpenStreetMap.
            ai_building_count (int): Count of buildings from AI estimates.
            avg_timestamp (timestamp): Average timestamp of data.
            last_edit_timestamp(timestamp): Last edit timestamp of an area
            osm_building_count_6_months (int): Count of buildings updated in the last 6 months.

        Returns:
            str: Human-readable building statement.
        """
        building_statement = f"OpenStreetMap contains roughly {humanize.intword(osm_building_count)} buildings in this region. "
        if ai_building_count > 0:
            building_statement += f"Based on AI-mapped estimates, this is approximately {round((osm_building_count/ai_building_count)*100)}% of the total buildings."
        building_statement += f"The average age of data for this region is {humanize.naturaltime(avg_timestamp).replace('ago', '')}( Last edited {humanize.naturaltime(last_edit_timestamp)} ) "
        if osm_building_count > 0:
            building_statement += f"and {round((osm_building_count_6_months/osm_building_count)*100)}% buildings were added or updated in the last 6 months."
        return building_statement

    @staticmethod
    def get_road_pattern_statement(
        osm_highway_length,
        ai_highway_length,
        avg_timestamp,
        last_edit_timestamp,
        osm_highway_length_6_months,
    ):
        """
        Translates road stats to a human-readable statement.

        Args:
            osm_highway_length (float): Length of roads from OpenStreetMap.
            ai_highway_length (float): Length of roads from AI estimates.
            avg_timestamp (str): Average timestamp of data.
            osm_highway_length_6_months (float): Length of roads updated in the last 6 months.

        Returns:
            str: Human-readable road statement.
        """
        road_statement = f"OpenStreetMap contains roughly {humanize.intword(osm_highway_length)} km of roads in this region. "
        if ai_highway_length > 1:
            road_statement += f"Based on AI-mapped estimates, this is approximately {round(osm_highway_length/ai_highway_length*100)} % of the total road length in the dataset region. "
        road_statement += f"The average age of data for the region is {humanize.naturaltime(avg_timestamp).replace('ago', '')} ( Last edited {humanize.naturaltime(last_edit_timestamp)} ) "
        if osm_highway_length > 1:
            road_statement += f"and {round((osm_highway_length_6_months/osm_highway_length)*100)}% of roads were added or updated in the last 6 months."
        return road_statement

    async def get_osm_analytics_meta_stats(self):
        """
        Gets the raw stats translated into a JSON body using the OSM Analytics API.

        Returns:
            dict: Raw statistics translated into JSON.
        """
        try:
            query = generate_polygon_stats_graphql_query(self.INPUT_GEOM)
            payload = {"query": query}
            response = await self.session.post(self.API_URL, json=payload, timeout=60)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            return response.json()
        except Exception as e:
            print(f"Request failed: {e}")
            return None

    async def get_summary_stats(self):
        """
        Generates summary statistics for buildings and roads.

        Returns:
            dict: Summary statistics including building and road statements.
        """
        combined_data = {}
        analytics_data = await self.get_osm_analytics_meta_stats()
        if (
            analytics_data is None
            or "data" not in analytics_data
            or "polygonStatistic" not in analytics_data["data"]
            or "analytics" not in analytics_data["data"]["polygonStatistic"]
            or "functions"
            not in analytics_data["data"]["polygonStatistic"]["analytics"]
            or analytics_data["data"]["polygonStatistic"]["analytics"]["functions"]
            is None
        ):
            logging.error(analytics_data)
            return None
        for function in analytics_data["data"]["polygonStatistic"]["analytics"][
            "functions"
        ]:
            function_id = function.get("id")
            result = function.get("result")
            combined_data[function_id] = result if result is not None else 0
        combined_data["osm_buildings_freshness_percentage"] = (
            100 - combined_data["antiqueOsmBuildingsPercentage"]
        )
        combined_data["osm_building_completeness_percentage"] = (
            100
            if combined_data["osmBuildingsCount"] == 0
            and combined_data["aiBuildingsCountEstimation"] == 0
            else (
                combined_data["osmBuildingsCount"]
                / combined_data["aiBuildingsCountEstimation"]
            )
            * 100
        )

        combined_data["osm_roads_freshness_percentage"] = (
            100 - combined_data["antiqueOsmRoadsPercentage"]
        )

        combined_data["osm_roads_completeness_percentage"] = (
            100
            if combined_data["highway_length"] == 0
            and combined_data["aiRoadCountEstimation"] == 0
            else (
                combined_data["highway_length"] / combined_data["aiRoadCountEstimation"]
            )
            * 100
        )

        combined_data["averageEditTime"] = datetime.fromtimestamp(
            combined_data["averageEditTime"]
        )
        combined_data["lastEditTime"] = datetime.fromtimestamp(
            combined_data["lastEditTime"]
        )

        building_summary = self.get_building_pattern_statement(
            combined_data["osmBuildingsCount"],
            combined_data["aiBuildingsCountEstimation"],
            combined_data["averageEditTime"],
            combined_data["lastEditTime"],
            combined_data["building_count_6_months"],
        )

        road_summary = self.get_road_pattern_statement(
            combined_data["highway_length"],
            combined_data["aiRoadCountEstimation"],
            combined_data["averageEditTime"],
            combined_data["lastEditTime"],
            combined_data["highway_length_6_months"],
        )

        return_stats = {
            "summary": {"buildings": building_summary, "roads": road_summary},
            "raw": {
                "population": combined_data["population"],
                "populatedAreaKm2": combined_data["populatedAreaKm2"],
                "averageEditTime": combined_data["averageEditTime"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "lastEditTime": combined_data["lastEditTime"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "osmUsersCount": combined_data["osmUsersCount"],
                "osmBuildingCompletenessPercentage": combined_data[
                    "osm_building_completeness_percentage"
                ],
                "osmRoadsCompletenessPercentage": combined_data[
                    "osm_roads_completeness_percentage"
                ],
                "osmBuildingsCount": combined_data["osmBuildingsCount"],
                "osmHighwayLengthKm": combined_data["highway_length"],
                "aiBuildingsCountEstimation": combined_data[
                    "aiBuildingsCountEstimation"
                ],
                "aiRoadCountEstimationKm": combined_data["aiRoadCountEstimation"],
                "buildingCount6Months": combined_data["building_count_6_months"],
                "highwayLength6MonthsKm": combined_data["highway_length_6_months"],
            },
            "meta": {
                "indicators": "https://github.com/hotosm/raw-data-api/tree/develop/docs/src/stats/indicators.md",
                "metrics": "https://github.com/hotosm/raw-data-api/tree/develop/docs/src/stats/metrics.md",
            },
        }

        return return_stats

    async def close_db_connection(self):
        """
        Close the database connection pool.
        """
        await self.db.close_pool()
