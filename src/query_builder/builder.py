# Copyright (C) 2021 Humanitarian OpenStreetmap Team

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Humanitarian OpenStreetmap Team
# 1100 13th Street NW Suite 800 Washington, D.C. 20005
# <info@hotosm.org>
"""Page Contains Query logic required for application"""

from json import dumps, loads

# Third party imports
from geomet import wkt
from src.config import USE_DUCK_DB_FOR_CUSTOM_EXPORTS

from osm2pgsql_query_builder import (
    build_column_select,
    build_geom_filter,
    build_geometry_type_query,
    build_snapshot_query,
    convert_tags_to_postgres,
    sanitize_filename,
)

# Legacy aliases used by the rest of the codebase.
# TODO Eventually swap callers to the new names.
raw_currentdata_extraction_query = build_snapshot_query
extract_geometry_type_query = build_geometry_type_query
format_file_name_str = sanitize_filename

HDX_FILTER_CRITERIA = """
This theme includes all OpenStreetMap features in this area matching ( Learn what tags means [here](https://wiki.openstreetmap.org/wiki/Tags) ) :

{criteria}
"""
HDX_MARKDOWN = """
{filter_str}
Features may have these attributes:

{columns}

This dataset is one of many [OpenStreetMap exports on
HDX](https://data.humdata.org/organization/hot).
See the [Humanitarian OpenStreetMap Team](http://hotosm.org/) website for more
information.
"""


def get_grid_id_query(geometry_dump):
    base_query = f"""select
                        b.poly_id
                    from
                        grid b
                    where
                        ST_Intersects(ST_GEOMFROMGEOJSON('{geometry_dump}') ,
                        b.geom)"""
    return base_query


def get_country_id_query(geom_dump):
    base_query = f"""select
                        b.cid::int as fid
                    from
                        countries b
                    where
                        ST_Intersects(ST_GEOMFROMGEOJSON('{geom_dump}') ,
                        b.geometry)
                    order by ST_Area(ST_Intersection(b.geometry,ST_MakeValid(ST_GEOMFROMGEOJSON('{geom_dump}')))) desc

                    """
    return base_query


def check_exisiting_country(geom):
    query = f"""select
                        b.cid::int as fid
                    from
                        countries b
                    where
                        ST_Equals(ST_SnapToGrid(ST_GEOMFROMGEOJSON('{geom}'),0.00001) ,
                        ST_SnapToGrid(b.geometry,0.00001))
                    """
    return query


def check_last_updated_rawdata():
    query = """select importdate as last_updated from planet_osm_replication_status"""
    return query


def get_countries_query(q):
    query = "Select ST_AsGeoJSON(cf.*) FROM countries cf"
    if q:
        query += f" WHERE name ILIKE '%{q}%'"
    return query


def get_country_cid(cid):
    query = f"Select ST_AsGeoJSON(cf.*) FROM countries cf where cid = {cid}"
    return query


def get_osm_feature_query(osm_id):
    select_condition = (
        "osm_id, tableoid::regclass AS osm_type, tags,changeset,timestamp,geom"
    )
    query = f"""SELECT ST_AsGeoJSON(n.*)
        FROM (select {select_condition} from nodes) n
        WHERE osm_id = {osm_id}
        UNION
        SELECT ST_AsGeoJSON(wl.*)
        FROM (select {select_condition} from ways_line) wl
        WHERE osm_id = {osm_id}
        UNION
        SELECT ST_AsGeoJSON(wp.*)
        FROM (select {select_condition} from ways_poly) wp
        WHERE osm_id = {osm_id}
        UNION
        SELECT ST_AsGeoJSON(r.*)
        FROM (select {select_condition} from relations) r
        WHERE osm_id = {osm_id}"""
    return query


def generate_polygon_stats_graphql_query(geojson_feature):
    """
    Gernerates the graphql query for the statistics
    """
    query = """
    {
        polygonStatistic (
        polygonStatisticRequest: {
            polygon: %s
        }
        )
        {
        analytics {
            functions(args:[
            {name:"sumX", id:"population", x:"population"},
            {name:"sumX", id:"populatedAreaKm2", x:"populated_area_km2"},
            {name:"percentageXWhereNoY", id:"osmBuildingGapsPercentage", x:"populated_area_km2", y:"building_count"},
            {name:"percentageXWhereNoY", id:"osmRoadGapsPercentage", x:"populated_area_km2", y:"highway_length"},
            {name:"percentageXWhereNoY", id:"antiqueOsmBuildingsPercentage", x:"populated_area_km2", y:"building_count_6_months"},
            {name:"percentageXWhereNoY", id:"antiqueOsmRoadsPercentage", x:"populated_area_km2", y:"highway_length_6_months"},
            {name:"avgX", id:"averageEditTime", x:"avgmax_ts"},
            {name:"maxX", id:"lastEditTime", x:"avgmax_ts"},
            {name:"sumX", id:"osmBuildingsCount", x:"building_count"},
            {name:"sumX", id:"highway_length", x:"highway_length"},
            {name:"sumX", id:"osmUsersCount", x:"osm_users"},
            {name:"sumX", id:"building_count_6_months" , x:"building_count_6_months"},
            {name:"sumX", id:"highway_length_6_months", x:"highway_length_6_months"},
            {name:"sumX", id:"aiBuildingsCountEstimation", x:"total_building_count"}
            {name:"sumX", id:"aiRoadCountEstimation", x:"total_road_length"}

            ]) {
            id,
            result
            }
        }
        }
    }
  """
    query = query % dumps(geojson_feature)

    return query


def get_country_from_iso(iso3):
    """
    Generate a SQL query to retrieve country information based on ISO3 code.

    Args:
    - iso3 (str): ISO3 Country Code.

    Returns:
    str: SQL query to fetch country information.
    """
    query = f"""SELECT
                    b.cid::int as fid, b.dataset->>'dataset_title' as dataset_title, b.dataset->>'dataset_prefix' as dataset_prefix,  b.dataset->>'dataset_locations' as locations
                FROM
                    cron b
                WHERE
                    LOWER(iso3) = '{iso3}'
                """
    return query


def postgres2duckdb_query(
    base_table_name,
    table,
    cid=None,
    geometry=None,
    single_category_where=None,
    enable_users_detail=False,
):
    """
    Generate a DuckDB query to create a table from a PostgreSQL query.

    Args:
    - base_table_name (str): Base table name.
    - table (str): PostgreSQL table name.
    - cid (int, optional): Country ID for filtering. Defaults to None.
    - geometry (Polygon, optional): Custom polygon geometry. Defaults to None.
    - single_category_where (str, optional): Where clause for single category to fetch it from postgres
    - enable_users_detail (bool, optional): Enable user details. Defaults to False.

    Returns:
    str: DuckDB query for creating a table.
    """
    select_query = """osm_id, osm_type, version, changeset, timestamp, tags,  ST_AsBinary(geom) as geom"""
    create_select_duck_db = """osm_id, osm_type , version, changeset, timestamp, cast(tags::json AS map(varchar, varchar)) AS tags, cast(ST_GeomFromWKB(geom) as GEOMETRY) AS geom"""

    if enable_users_detail:
        select_query = """osm_id, osm_type, uid, "user", version, changeset, timestamp, tags, ST_AsBinary(geom) as geom"""
        create_select_duck_db = """osm_id, osm_type, uid, "user", version, changeset, timestamp, cast(tags::json AS map(varchar, varchar)) AS tags, cast(ST_GeomFromWKB(geom) as GEOMETRY) AS geom"""

    row_filter_condition = (
        f"""(country @> ARRAY [{cid}])"""
        if cid
        else f"""ST_Intersects(geom,(select ST_SetSRID(ST_Extent(ST_makeValid(ST_GeomFromText('{wkt.dumps(loads(geometry.json()),decimals=6)}',4326))),4326)))"""
    )

    postgres_query = f"""select {select_query} from (select * , tableoid::regclass as osm_type from {table} where {row_filter_condition}) as sub_query"""
    if single_category_where:
        postgres_query += (
            f" where {convert_tags_to_postgres(single_category_where)}"
        )

    duck_db_create = f"""CREATE TABLE {base_table_name}_{table} AS SELECT {create_select_duck_db} FROM postgres_query("postgres_db", "{postgres_query}") """

    return duck_db_create


def extract_custom_features_from_postgres(
    select_q, from_q, where_q, geom=None, cid=None
):
    """
    Generates Postgresql query for custom feature extraction
    """
    geom_filter = f"""(country @> ARRAY [{cid}])""" if cid else build_geom_filter(geom)

    postgres_query = f"""select {select_q} from (select * , tableoid::regclass as osm_type from {from_q} where {geom_filter}) as sub_query"""
    if where_q:
        postgres_query += f" where {convert_tags_to_postgres(where_q)}"
    return postgres_query


def extract_features_custom_exports(
    base_table_name, select, feature_type, where, geometry=None, cid=None
):
    """
    Generate a Extraction query to extract features based on given parameters.

    Args:
    - base_table_name (str): Base table name.
    - select (List[str]): List of selected fields.
    - feature_type (str): Type of feature (points, lines, polygons).
    - where (str): SQL-like condition to filter features.

    Returns:
    str: Extraction query to extract features.
    """
    map_tables = {
        "points": {"table": ["nodes"], "where": {"nodes": f"({where})"}},
        "lines": {
            "table": ["ways_line", "relations"],
            "where": {
                "ways_line": where,
                "relations": f"({where}) and (ST_GeometryType(geom)='MULTILINESTRING')",
            },
        },
        "polygons": {
            "table": ["ways_poly", "relations"],
            "where": {
                "ways_poly": where,
                "relations": f"({where}) and (ST_GeometryType(geom)='MULTIPOLYGON' or ST_GeometryType(geom)='POLYGON')",
            },
        },
    }
    if USE_DUCK_DB_FOR_CUSTOM_EXPORTS is True:
        if "*" in select:
            select = [f"""tags::json as tags """]
        else:
            select = [f"""tags['{item}'][1] as "{item}" """ for item in select]
        select += ["osm_id", "osm_type", "geom"]
        select_query = ", ".join(select)
    else:
        select_query = build_column_select(select, include_osm_type=False)

    from_query = map_tables[feature_type]["table"]

    base_query = []
    for table in from_query:
        where_query = map_tables[feature_type]["where"][table]
        if USE_DUCK_DB_FOR_CUSTOM_EXPORTS is True:
            if geometry:
                where_query += f" and (ST_Intersects(geom,ST_GeomFromGeoJSON('{geometry.json()}')))"
            query = f"""select {select_query} from {f"{base_table_name}_{table}"} where {where_query}"""
        else:
            query = extract_custom_features_from_postgres(
                select_q=select_query,
                from_q=table,
                where_q=where_query,
                geom=geometry,
                cid=cid,
            )
        base_query.append(query)
    return " UNION ALL ".join(base_query)


def get_country_geojson(c_id):
    query = f"SELECT ST_AsGeoJSON(geometry) as geom from countries where id={c_id}"
    return query


def get_country_geom_from_iso(iso3):
    """
    Generate a SQL query to retrieve country geometry based on ISO3 code.

    Args:
    - iso3 (str): ISO3 Country Code.

    Returns:
    str: SQL query to fetch country geometry.
    """
    query = f"""SELECT
                    ST_AsGeoJSON(geometry) as geom
                FROM
                    countries b
                WHERE
                    LOWER(iso3) = '{iso3}'
                """
    return query
