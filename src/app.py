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
"""Page contains Main core logic of app"""
# Standard library imports
import concurrent.futures
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import uuid
from collections import namedtuple
from datetime import datetime, timedelta, timezone
from json import dumps
from json import loads as json_loads

# Third party imports
import boto3
import humanize
import orjson
import psycopg2.extras
import requests
from area import area
from fastapi import HTTPException
from geojson import FeatureCollection
from psycopg2 import OperationalError, connect, sql
from psycopg2.extras import DictCursor
from slugify import slugify
from tqdm import tqdm

# Reader imports
from src.config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    BUCKET_NAME,
    DEFAULT_README_TEXT,
    ENABLE_CUSTOM_EXPORTS,
    ENABLE_HDX_EXPORTS,
    ENABLE_POLYGON_STATISTICS_ENDPOINTS,
    ENABLE_SOZIP,
    ENABLE_TILES,
    EXPORT_MAX_AREA_SQKM,
)
from src.config import EXPORT_PATH as export_path
from src.config import INDEX_THRESHOLD as index_threshold
from src.config import (
    PARALLEL_PROCESSING_CATEGORIES,
    POLYGON_STATISTICS_API_URL,
    PROCESS_SINGLE_CATEGORY_IN_POSTGRES,
)
from src.config import USE_CONNECTION_POOLING as use_connection_pooling
from src.config import (
    USE_DUCK_DB_FOR_CUSTOM_EXPORTS,
    USE_S3_TO_UPLOAD,
    get_db_connection_params,
    level,
)
from src.config import logger as logging
from src.query_builder.builder import (
    HDX_FILTER_CRITERIA,
    HDX_MARKDOWN,
    check_exisiting_country,
    check_last_updated_rawdata,
    extract_features_custom_exports,
    extract_geometry_type_query,
    generate_polygon_stats_graphql_query,
    get_countries_query,
    get_country_from_iso,
    get_country_geom_from_iso,
    get_osm_feature_query,
    postgres2duckdb_query,
    raw_currentdata_extraction_query,
)
from src.validation.models import EXPORT_TYPE_MAPPING, RawDataOutputType

if ENABLE_SOZIP:
    # Third party imports
    import sozipfile.sozipfile as zipfile
else:
    # Standard library imports
    import zipfile

# import instance for pooling
if use_connection_pooling:
    # Reader imports
    from src.db_session import database_instance
else:
    database_instance = None
# Standard library imports
import logging as log

if ENABLE_CUSTOM_EXPORTS:
    if USE_DUCK_DB_FOR_CUSTOM_EXPORTS is True:
        # Third party imports
        import duckdb

        # Reader imports
        from src.config import DUCK_DB_MEMORY_LIMIT, DUCK_DB_THREAD_LIMIT

if ENABLE_HDX_EXPORTS:
    # Third party imports
    from hdx.data.dataset import Dataset
    from hdx.data.resource import Resource

    # Reader imports
    from src.config import HDX_MAINTAINER, HDX_OWNER_ORG, HDX_URL_PREFIX


global LOCAL_CON_POOL

# getting the pool instance which was fireup when API is started
LOCAL_CON_POOL = database_instance


def print_psycopg2_exception(err):
    """
    Function that handles and parses Psycopg2 exceptions
    """
    """details_exception"""
    err_type, err_obj, traceback = sys.exc_info()
    line_num = traceback.tb_lineno
    # the connect() error
    print("\npsycopg2 ERROR:", err, "on line number:", line_num)
    print("psycopg2 traceback:", traceback, "-- type:", err_type)
    # psycopg2 extensions.Diagnostics object attribute
    print("\nextensions.Diagnostics:", err.diag)
    # pgcode and pgerror exceptions
    print("pgerror:", err.pgerror)
    print("pgcode:", err.pgcode, "\n")
    raise err


def convert_dict_to_conn_str(db_dict):
    conn_str = " ".join([f"{key}={value}" for key, value in db_dict.items()])
    return conn_str


def check_for_json(result_str):
    """Check if the Payload is a JSON document

    Return: bool:
        True in case of success, False otherwise
    """
    try:
        r_json = json_loads(result_str)
        return True, r_json
    except Exception as ex:
        logging.error(ex)
        return False, None


def dict_none_clean(to_clean):
    """Clean DictWriter"""
    result = {}
    for key, value in to_clean.items():
        if value is None:
            value = 0
        result[key] = value
    return result


def generate_ogr2ogr_cmd_from_psql(
    export_file_path,
    export_file_format_driver,
    postgres_query,
    layer_creation_options,
    query_dump_path,
):
    """
    Generates ogr2ogr command for postgresql queries
    """
    db_items = get_db_connection_params()
    os.makedirs(query_dump_path, exist_ok=True)
    query_path = os.path.join(query_dump_path, "query.sql")
    with open(query_path, "w", encoding="UTF-8") as file:
        file.write(postgres_query)
    ogr2ogr_cmd = """ogr2ogr -overwrite -f "{export_format}" {export_path} PG:"host={host} port={port} user={username} dbname={db} password={password}" -sql @"{pg_sql_select}" {layer_creation_options_str} -progress""".format(
        export_format=export_file_format_driver,
        export_path=export_file_path,
        host=db_items.get("host"),
        port=db_items.get("port"),
        username=db_items.get("user"),
        db=db_items.get("dbname"),
        password=db_items.get("password"),
        pg_sql_select=query_path,
        layer_creation_options_str=(
            f"-lco {layer_creation_options}" if layer_creation_options else ""
        ),
    )
    return ogr2ogr_cmd


def run_ogr2ogr_cmd(cmd):
    """Runs command and monitors the file size until the process runs

    Args:
        cmd (_type_): Command to run for subprocess
        binding_file_dir (_type_): _description_

    Raises:
        Exception: If process gets failed
    """
    try:
        subprocess.check_output(
            cmd, env=os.environ, shell=True, preexec_fn=os.setsid, timeout=60 * 60 * 6
        )
    except subprocess.CalledProcessError as ex:
        logging.error(ex.output)
        raise ex


class Database:
    """Database class is used to connect with your database , run query  and get result from it . It has all tests and validation inside class"""

    def __init__(self, db_params):
        """Database class constructor"""

        self.db_params = db_params

    def connect(self):
        """Database class instance method used to connect to database parameters with error printing"""

        try:
            self.conn = connect(**self.db_params)
            self.cur = self.conn.cursor(cursor_factory=DictCursor)
            # logging.debug("Database connection has been Successful...")
            return self.conn, self.cur
        except OperationalError as err:
            """pass exception to function"""

            print_psycopg2_exception(err)
            # set the connection to 'None' in case of error
            self.conn = None

    def executequery(self, query):
        """Function to execute query after connection"""
        # Check if the connection was successful
        try:
            if self.conn is not None:
                self.cursor = self.cur
                if query is not None:
                    # catch exception for invalid SQL statement

                    try:
                        logging.debug("Query sent to Database")
                        self.cursor.execute(query)
                        try:
                            result = self.cursor.fetchall()
                            logging.debug("Result fetched from Database")
                            return result
                        except Exception as ex:
                            logging.error(ex)
                            return self.cursor.statusmessage
                    except Exception as err:
                        print_psycopg2_exception(err)
                else:
                    raise ValueError("Query is Null")

                    # rollback the previous transaction before starting another
                    self.conn.rollback()
                # closing  cursor object to avoid memory leaks
                # cursor.close()
                # self.conn.close()
            else:
                print("Database is not connected")
        except Exception as err:
            print("Oops ! You forget to have connection first")
            raise err

    def close_conn(self):
        """function for clossing connection to avoid memory leaks"""

        # Check if the connection was successful
        try:
            if self.conn is not None:
                if self.cur is not None:
                    self.cur.close()
                    self.conn.close()
        except Exception as err:
            raise err


class Users:
    """
    Users class provides CRUD operations for interacting with the 'users' table in the database.

    Methods:
    - create_user(osm_id: int, role: int) -> Dict[str, Any]: Inserts a new user into the database.
    - read_user(osm_id: int) -> Dict[str, Any]: Retrieves user information based on the given osm_id.
    - update_user(osm_id: int, update_data: UserUpdate) -> Dict[str, Any]: Updates user information based on the given osm_id.
    - delete_user(osm_id: int) -> Dict[str, Any]: Deletes a user based on the given osm_id.
    - read_users(skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]: Retrieves a list of users with optional pagination.

    Usage:
    users = Users()
    """

    def __init__(self) -> None:
        """
        Initializes an instance of the Auth class, connecting to the database.
        """
        dbdict = get_db_connection_params()
        self.d_b = Database(dbdict)
        self.con, self.cur = self.d_b.connect()

    def create_user(self, osm_id, role):
        """
        Inserts a new user into the 'users' table and returns the created user's osm_id.

        Args:
        - osm_id (int): The OSM ID of the new user.
        - role (int): The role of the new user.

        Returns:
        - Dict[str, Any]: A dictionary containing the osm_id of the newly created user.

        Raises:
        - HTTPException: If the user creation fails.
        """
        query = "INSERT INTO users (osm_id, role) VALUES (%s, %s) RETURNING osm_id;"
        params = (osm_id, role)
        self.cur.execute(self.cur.mogrify(query, params).decode("utf-8"))
        new_osm_id = self.cur.fetchall()[0][0]
        self.con.commit()
        self.d_b.close_conn()
        return {"osm_id": new_osm_id}

    def read_user(self, osm_id):
        """
        Retrieves user information based on the given osm_id.

        Args:
        - osm_id (int): The OSM ID of the user to retrieve.

        Returns:
        - Dict[str, Any]: A dictionary containing user information if the user is found.
                        If the user is not found, returns a default user with 'role' set to 3.

        Raises:
        - HTTPException: If there's an issue with the database query.
        """
        query = "SELECT * FROM users WHERE osm_id = %s;"
        params = (osm_id,)
        self.cur.execute(self.cur.mogrify(query, params).decode("utf-8"))
        result = self.cur.fetchall()
        self.d_b.close_conn()
        if result:
            return dict(result[0])
        else:
            # Return a default user with 'role' set to 3 if the user is not found
            return {"osm_id": osm_id, "role": 3}

    def update_user(self, osm_id, update_data):
        """
        Updates user information based on the given osm_id.

        Args:
        - osm_id (int): The OSM ID of the user to update.
        - update_data (UserUpdate): The data to update for the user.

        Returns:
        - Dict[str, Any]: A dictionary containing the updated user information.

        Raises:
        - HTTPException: If the user with the given osm_id is not found.
        """
        query = "UPDATE users SET osm_id = %s, role = %s WHERE osm_id = %s RETURNING *;"
        params = (update_data.osm_id, update_data.role, osm_id)
        self.cur.execute(self.cur.mogrify(query, params).decode("utf-8"))
        updated_user = self.cur.fetchall()
        self.con.commit()
        self.d_b.close_conn()
        if updated_user:
            return dict(updated_user[0])
        raise HTTPException(status_code=404, detail="User not found")

    def delete_user(self, osm_id):
        """
        Deletes a user based on the given osm_id.

        Args:
        - osm_id (int): The OSM ID of the user to delete.

        Returns:
        - Dict[str, Any]: A dictionary containing the deleted user information.

        Raises:
        - HTTPException: If the user with the given osm_id is not found.
        """
        query = "DELETE FROM users WHERE osm_id = %s RETURNING *;"
        params = (osm_id,)
        self.cur.execute(self.cur.mogrify(query, params).decode("utf-8"))
        deleted_user = self.cur.fetchall()
        self.con.commit()
        self.d_b.close_conn()
        if deleted_user:
            return dict(deleted_user[0])
        raise HTTPException(status_code=404, detail="User not found")

    def read_users(self, skip=0, limit=10):
        """
        Retrieves a list of users with optional pagination.

        Args:
        - skip (int): The number of users to skip (for pagination).
        - limit (int): The maximum number of users to retrieve (for pagination).

        Returns:
        - List[Dict[str, Any]]: A list of dictionaries containing user information.
        """
        query = "SELECT * FROM users OFFSET %s LIMIT %s;"
        params = (skip, limit)
        self.cur.execute(self.cur.mogrify(query, params).decode("utf-8"))
        users_list = self.cur.fetchall()
        self.d_b.close_conn()
        return [dict(user) for user in users_list]


class RawData:
    """Class responsible for the Rawdata Extraction from available sources ,
        Currently Works for Underpass source Current Snapshot
    Returns:
    Geojson Zip file
    Supports:
    -Any Key value pair of osm tags
    -A Polygon
    -Osm element type (Optional)
    """

    def __init__(self, parameters=None, dbdict=None):
        if parameters:
            # validation for the parameters if it is already validated with
            # pydantic model or not , people coming from package they
            # will not have api valdiation so to make sure they will be validated
            # before accessing the class
            # if isinstance(parameters, RawDataCurrentParams) is False:
            #     self.params = RawDataCurrentParams(**parameters)
            # else:
            self.params = parameters
        # only use connection pooling if it is configured in config file
        if use_connection_pooling:
            # if database credentials directly from class is not passed grab from pool
            pool_conn = LOCAL_CON_POOL.get_conn_from_pool()
            self.con, self.cur = pool_conn, pool_conn.cursor(cursor_factory=DictCursor)
        else:
            # else use our default db class
            if not dbdict:
                dbdict = get_db_connection_params()
            self.d_b = Database(dict(dbdict))
            self.con, self.cur = self.d_b.connect()

    @staticmethod
    def close_con(con):
        """Closes connection if exists"""
        if con:
            if use_connection_pooling:
                # release connection from pool
                database_instance.release_conn_from_pool(con)
            else:
                con.close()

    @staticmethod
    def ogr_export_shp(point_query, line_query, poly_query, working_dir, file_name):
        """Function written to support ogr type extractions as well , In this way we will be able to support all file formats supported by Ogr , Currently it is slow when dataset gets bigger as compared to our own conversion method but rich in feature and data types even though it is slow"""
        db_items = get_db_connection_params()
        if point_query:
            query_path = os.path.join(working_dir, "point.sql")
            # writing to .sql to pass in ogr2ogr because we don't want to pass too much argument on command with sql
            with open(query_path, "w", encoding="UTF-8") as file:
                file.write(point_query)
            # standard file path for the generation
            point_file_path = os.path.join(working_dir, f"{file_name}_point.shp")
            # command for ogr2ogr to generate file

            cmd = """ogr2ogr -overwrite -f "ESRI Shapefile" {export_path} PG:"host={host} port={port} user={username} dbname={db} password={password}" -sql @"{pg_sql_select}" -lco ENCODING=UTF-8 -progress""".format(
                export_path=point_file_path,
                host=db_items.get("host"),
                port=db_items.get("port"),
                username=db_items.get("user"),
                db=db_items.get("dbname"),
                password=db_items.get("password"),
                pg_sql_select=query_path,
            )
            logging.debug("Calling ogr2ogr-Point Shapefile")
            run_ogr2ogr_cmd(cmd)
            # clear query file we don't need it anymore
            os.remove(query_path)

        if line_query:
            query_path = os.path.join(working_dir, "line.sql")
            # writing to .sql to pass in ogr2ogr because we don't want to pass too much argument on command with sql
            with open(query_path, "w", encoding="UTF-8") as file:
                file.write(line_query)
            line_file_path = os.path.join(working_dir, f"{file_name}_line.shp")
            cmd = """ogr2ogr -overwrite -f "ESRI Shapefile" {export_path} PG:"host={host} port={port} user={username} dbname={db} password={password}" -sql @"{pg_sql_select}" -lco ENCODING=UTF-8 -progress""".format(
                export_path=line_file_path,
                host=db_items.get("host"),
                port=db_items.get("port"),
                username=db_items.get("user"),
                db=db_items.get("dbname"),
                password=db_items.get("password"),
                pg_sql_select=query_path,
            )
            logging.debug("Calling ogr2ogr-Line Shapefile")
            run_ogr2ogr_cmd(cmd)
            # clear query file we don't need it anymore
            os.remove(query_path)

        if poly_query:
            query_path = os.path.join(working_dir, "poly.sql")
            poly_file_path = os.path.join(working_dir, f"{file_name}_poly.shp")
            # writing to .sql to pass in ogr2ogr because we don't want to pass too much argument on command with sql
            with open(query_path, "w", encoding="UTF-8") as file:
                file.write(poly_query)
            cmd = """ogr2ogr -overwrite -f "ESRI Shapefile" {export_path} PG:"host={host} port={port} user={username} dbname={db} password={password}" -sql @"{pg_sql_select}" -lco ENCODING=UTF-8 -progress""".format(
                export_path=poly_file_path,
                host=db_items.get("host"),
                port=db_items.get("port"),
                username=db_items.get("user"),
                db=db_items.get("dbname"),
                password=db_items.get("password"),
                pg_sql_select=query_path,
            )
            logging.debug("Calling ogr2ogr-Poly Shapefile")
            run_ogr2ogr_cmd(cmd)
            # clear query file we don't need it anymore
            os.remove(query_path)

    @staticmethod
    def ogr_export(query, outputtype, working_dir, dump_temp_path, params):
        """Generates ogr2ogr command based on outputtype and parameters

        Args:
            query (_type_): Postgresql query to extract
            outputtype (_type_): _description_
            working_dir (_type_): _description_
            dump_temp_path (_type_): temp file path for metadata gen
            params (_type_): _description_
        """
        db_items = get_db_connection_params()
        query_path = os.path.join(working_dir, "export_query.sql")
        with open(query_path, "w", encoding="UTF-8") as file:
            file.write(query)

        format_options = {
            RawDataOutputType.FLATGEOBUF.value: {
                "format": "FLATGEOBUF",
                "extra": "-lco SPATIAL_INDEX=YES VERIFY_BUFFERS=NO",
            },
            RawDataOutputType.GEOPARQUET.value: {
                "format": "Parquet",
                "extra": "",
            },
            RawDataOutputType.PGDUMP.value: {
                "format": "PGDump",
                "extra": "--config PG_USE_COPY YES -lco SRID=4326",
            },
            RawDataOutputType.KML.value: {
                "format": "KML",
                "extra": "",
            },
            RawDataOutputType.CSV.value: {
                "format": "CSV",
                "extra": "",
            },
            RawDataOutputType.GEOPACKAGE.value: {
                "format": "GPKG",
                "extra": "",
            },
        }

        if ENABLE_TILES:
            format_options[RawDataOutputType.MBTILES.value] = {
                "format": "MBTILES",
                "extra": (
                    "-dsco MINZOOM={} -dsco MAXZOOM={} ".format(
                        params.min_zoom, params.max_zoom
                    )
                    if params.min_zoom and params.max_zoom
                    else "-dsco ZOOM_LEVEL_AUTO=YES"
                ),
            }

        file_name_option = (
            f"-nln {params.file_name if params.file_name else 'raw_export'}"
        )

        if outputtype == RawDataOutputType.FLATGEOBUF.value and params.fgb_wrap_geoms:
            format_options[outputtype]["extra"] += " -nlt GEOMETRYCOLLECTION"

        format_option = format_options.get(outputtype, {"format": "", "extra": ""})

        cmd = f"ogr2ogr -overwrite -f {format_option['format']} {dump_temp_path} PG:\"host={db_items.get('host')} port={db_items.get('port')} user={db_items.get('user')} dbname={db_items.get('dbname')} password={db_items.get('password')}\" -sql @{query_path} -lco ENCODING=UTF-8 -progress {format_option['extra']} {file_name_option}"
        run_ogr2ogr_cmd(cmd)

        os.remove(query_path)

    @staticmethod
    def query2geojson(con, extraction_query, dump_temp_file_path):
        """Function written from scratch without being dependent on any library, Provides better performance for geojson binding"""
        # creating geojson file
        pre_geojson = """{"type": "FeatureCollection","features": ["""
        post_geojson = """]}"""
        logging.debug("Query : %s", extraction_query)
        # writing to the file
        # directly writing query result to the file one by one without holding them in object so that it will not eat up our memory
        with open(dump_temp_file_path, "a", encoding="utf-8") as f:
            f.write(pre_geojson)
            logging.debug("Server side Cursor Query Sent with 1000 Chunk Size")
            with con.cursor(name="fetch_raw") as cursor:  # using server side cursor
                cursor.itersize = (
                    1000  # chunk size to get 1000 row at a time in client side
                )
                cursor.execute(extraction_query)
                first = True
                for row in cursor:
                    if first:
                        first = False
                        f.write(row[0])
                    else:
                        f.write(",")
                        f.write(row[0])
                cursor.close()  # closing connection to avoid memory issues
                # close the writing geojson with last part
            f.write(post_geojson)
        logging.debug("Server side Query Result  Post Processing Done")

    @staticmethod
    def get_grid_id(geom, cur):
        """Gets the intersecting related grid id for the geometry that is passed

        Args:
            geom (_type_): _description_
            cur (_type_): _description_

        Returns:
            _type_: grid id , geometry dump and the area of geometry
        """
        geometry_dump = dumps(dict(geom))
        # generating geometry area in sqkm
        geom_area = area(json_loads(geom.json())) * 1e-6
        country_export = False
        g_id = None
        countries = []
        cur.execute(check_exisiting_country(geometry_dump))
        backend_match = cur.fetchall()
        if backend_match:
            countries = backend_match[0]
            country_export = True
            logging.info(f"Using Country Export Mode with id : {countries[0]}")
        # else:
        #     if int(geom_area) > int(index_threshold):
        #         # this will be applied only when polygon gets bigger we will be slicing index size to search
        #         country_query = get_country_id_query(geometry_dump)
        #         cur.execute(country_query)
        #         result_country = cur.fetchall()
        #         countries = [int(f[0]) for f in result_country]
        #         logging.debug(f"Intersected Countries : {countries}")
        #         cur.close()
        return (
            g_id,
            geometry_dump,
            geom_area,
            (
                countries if len(countries) > 0 and len(countries) <= 3 else None
            ),  # don't go through countires if they are more than 3
            country_export,
        )

    @staticmethod
    def geojson2tiles(geojson_path, tile_path, tile_layer_name):
        """Responsible for geojson to tiles"""
        cmd = """tippecanoe -zg --projection=EPSG:4326 -o {tile_output_path} -l {tile_layer_name} --force {geojson_input_path}""".format(
            tile_output_path=tile_path,
            tile_layer_name=tile_layer_name,
            geojson_input_path=geojson_path,
        )
        run_ogr2ogr_cmd(cmd)

    def extract_current_data(self, exportname):
        """Responsible for Extracting rawdata current snapshot, Initially it creates a geojson file , Generates query , run it with 1000 chunk size and writes it directly to the geojson file and closes the file after dump
        Args:
            exportname: takes filename as argument to create geojson file passed from routers

        Returns:
            geom_area: area of polygon supplied
            working_dir: dir where results are saved
        """
        # first check either geometry needs grid or not for querying
        (
            grid_id,
            geometry_dump,
            geom_area,
            country,
            country_export,
        ) = RawData.get_grid_id(self.params.geometry, self.cur)
        output_type = self.params.output_type
        # Check whether the export path exists or not
        working_dir = os.path.join(export_path, exportname)
        if not os.path.exists(working_dir):
            # Create a exports directory because it does not exist
            os.makedirs(working_dir)
        # create file path with respect to of output type

        dump_temp_file_path = os.path.join(
            working_dir,
            f"{self.params.file_name if self.params.file_name else 'Export'}.{output_type.lower()}",
        )
        try:
            # currently we have only geojson binding function written other than that we have depend on ogr
            if ENABLE_TILES:
                if output_type == RawDataOutputType.PMTILES.value:
                    geojson_path = os.path.join(
                        working_dir,
                        f"{self.params.file_name if self.params.file_name else 'Export'}.geojson",
                    )
                    RawData.query2geojson(
                        self.con,
                        raw_currentdata_extraction_query(
                            self.params,
                            g_id=grid_id,
                            c_id=country,
                            country_export=country_export,
                        ),
                        geojson_path,
                    )
                    RawData.geojson2tiles(
                        geojson_path, dump_temp_file_path, self.params.file_name
                    )
                if output_type == RawDataOutputType.MBTILES.value:
                    RawData.ogr_export(
                        query=raw_currentdata_extraction_query(
                            self.params,
                            grid_id,
                            country,
                            ogr_export=True,
                            country_export=country_export,
                        ),
                        outputtype=output_type,
                        dump_temp_path=dump_temp_file_path,
                        working_dir=working_dir,
                        params=self.params,
                    )  # uses ogr export to export

            if output_type == RawDataOutputType.GEOJSON.value:
                RawData.query2geojson(
                    self.con,
                    raw_currentdata_extraction_query(
                        self.params,
                        g_id=grid_id,
                        c_id=country,
                        country_export=country_export,
                    ),
                    dump_temp_file_path,
                )  # uses own conversion class
            if output_type == RawDataOutputType.SHAPEFILE.value:
                (
                    point_query,
                    line_query,
                    poly_query,
                    point_schema,
                    line_schema,
                    poly_schema,
                ) = extract_geometry_type_query(
                    self.params,
                    ogr_export=True,
                    g_id=grid_id,
                    c_id=country,
                    country_export=country_export,
                )
                RawData.ogr_export_shp(
                    point_query=point_query,
                    line_query=line_query,
                    poly_query=poly_query,
                    working_dir=working_dir,
                    file_name=(
                        self.params.file_name if self.params.file_name else "Export"
                    ),
                )  # using ogr2ogr
            if output_type in ["fgb", "kml", "gpkg", "sql", "parquet", "csv"]:
                RawData.ogr_export(
                    query=raw_currentdata_extraction_query(
                        self.params,
                        grid_id,
                        country,
                        ogr_export=True,
                        country_export=country_export,
                    ),
                    outputtype=output_type,
                    dump_temp_path=dump_temp_file_path,
                    working_dir=working_dir,
                    params=self.params,
                )  # uses ogr export to export
            return geom_area, geometry_dump, working_dir
        except Exception as ex:
            logging.error(ex)
            raise ex
        finally:
            # closing connection before leaving class
            RawData.close_con(self.con)

    def check_status(self):
        """Gives status about DB update, Substracts with current time and last db update time"""
        status_query = check_last_updated_rawdata()
        self.cur.execute(status_query)
        behind_time = self.cur.fetchall()
        self.cur.close()
        # closing connection before leaving class
        RawData.close_con(self.con)
        return str(behind_time[0][0])

    def get_countries_list(self, q):
        """Gets Countries list from the database

        Args:
            q (_type_): list filter query string

        Returns:
            featurecollection: geojson of country
        """
        query = get_countries_query(q)
        self.cur.execute(query)
        get_fetched = self.cur.fetchall()
        features = []
        for row in get_fetched:
            features.append(orjson.loads(row[0]))
        self.cur.close()
        return FeatureCollection(features=features)

    def get_osm_feature(self, osm_id):
        """Returns geometry of osm_id in geojson

        Args:
            osm_id (_type_): osm_id of feature

        Returns:
            featurecollection: Geojson
        """
        query = get_osm_feature_query(osm_id)
        self.cur.execute(query)
        get_fetched = self.cur.fetchall()
        features = []
        for row in get_fetched:
            features.append(orjson.loads(row[0]))
        self.cur.close()
        return FeatureCollection(features=features)

    def extract_plain_geojson(self):
        """Gets geojson for small area Returns plain geojson without binding"""
        extraction_query = raw_currentdata_extraction_query(self.params)
        features = []

        with self.con.cursor(
            name="fetch_raw_quick"
        ) as cursor:  # using server side cursor
            cursor.itersize = 500
            cursor.execute(extraction_query)
            for row in cursor:
                features.append(orjson.loads(row[0]))
            cursor.close()
        return FeatureCollection(features=features)


class S3FileTransfer:
    """Responsible for the file transfer to s3 from API maachine"""

    def __init__(self):
        # responsible for the connection
        try:
            if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
                self.aws_session = boto3.Session(
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                )
            else:  # if it is not passed on config then api will assume it is configured within machine using credentials file
                self.aws_session = boto3.Session()
            self.s_3 = self.aws_session.client("s3")
            logging.debug("Connection has been successful to s3")
        except Exception as ex:
            logging.error(ex)
            raise ex

    def list_buckets(self):
        """used to list all the buckets available on s3"""
        buckets = self.s_3.list_buckets()
        return buckets

    def get_bucket_location(self, bucket_name):
        """Provides the bucket location on aws, takes bucket_name as string -- name of repo on s3"""
        try:
            bucket_location = self.s_3.get_bucket_location(Bucket=bucket_name)[
                "LocationConstraint"
            ]
        except Exception as ex:
            logging.error("Can't access bucket location")
            raise ex
        return bucket_location or "us-east-1"

    def upload(self, file_path, file_name, file_suffix=None):
        """Used for transferring file to s3 after reading path from the user , It will wait for the upload to complete
        Parameters :file_path --- your local file path to upload ,
            file_prefix -- prefix for the filename which is stored
        sample function call :
            S3FileTransfer.transfer(file_path="exports",file_prefix="upload_test")"""
        if file_suffix:
            file_name = f"{file_name}.{file_suffix}"
        logging.debug("Started Uploading %s from %s", file_name, file_path)
        # instantiate upload
        start_time = time.time()

        try:
            self.s_3.upload_file(str(file_path), BUCKET_NAME, str(file_name))
        except Exception as ex:
            logging.error(ex)
            raise ex
        logging.debug("Uploaded %s in %s sec", file_name, time.time() - start_time)
        # generate the download url
        bucket_location = self.get_bucket_location(bucket_name=BUCKET_NAME)
        object_url = (
            f"""https://s3.{bucket_location}.amazonaws.com/{BUCKET_NAME}/{file_name}"""
        )
        return object_url


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
            dbdict = get_db_connection_params()
            d_b = Database(dbdict)
            con, cur = d_b.connect()
            cur.execute(get_country_geom_from_iso(iso3))
            result = cur.fetchone()
            if result is None:
                raise HTTPException(status_code=404, detail="Invalid iso3 code")
            self.INPUT_GEOM = result[0]
        else:
            self.INPUT_GEOM = dumps(geojson)

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

    def get_osm_analytics_meta_stats(self):
        """
        Gets the raw stats translated into a JSON body using the OSM Analytics API.

        Returns:
            dict: Raw statistics translated into JSON.
        """
        try:
            query = generate_polygon_stats_graphql_query(self.INPUT_GEOM)
            payload = {"query": query}
            response = requests.post(self.API_URL, json=payload, timeout=60)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            return response.json()
        except Exception as e:
            print(f"Request failed: {e}")
            return None

    def get_summary_stats(self):
        """
        Generates summary statistics for buildings and roads.

        Returns:
            dict: Summary statistics including building and road statements.
        """
        combined_data = {}
        analytics_data = self.get_osm_analytics_meta_stats()
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


class DuckDB:
    """
    Constructor for the DuckDB class.

    Parameters:
    - db_path (str): The path to the DuckDB database file.
    """

    def __init__(self, db_path, temp_dir=None):
        dbdict = get_db_connection_params()
        self.db_con_str = convert_dict_to_conn_str(db_dict=dbdict)
        self.db_path = db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        con = duckdb.connect(self.db_path)
        con.sql(f"""ATTACH '{self.db_con_str}' AS postgres_db (TYPE POSTGRES)""")
        con.install_extension("spatial")
        con.load_extension("spatial")
        duck_db_temp = temp_dir
        if temp_dir is None:
            duck_db_temp = os.path.join(export_path, "duckdb_temp")
            os.makedirs(duck_db_temp, exist_ok=True)
        con.sql(f"""SET temp_directory = '{os.path.join(duck_db_temp,'temp.tmp')}'""")

        if DUCK_DB_MEMORY_LIMIT:
            con.sql(f"""SET memory_limit = '{DUCK_DB_MEMORY_LIMIT}'""")
        if DUCK_DB_THREAD_LIMIT:
            con.sql(f"""SET threads to {DUCK_DB_THREAD_LIMIT}""")

        con.sql("""SET enable_progress_bar = true""")

    def run_query(self, query, attach_pgsql=False, load_spatial=False):
        """
        Executes a query on the DuckDB database.

        Parameters:
        - query (str): The SQL query to execute.
        - attach_pgsql (bool): Flag to indicate whether to attach a PostgreSQL database.
        - load_spatial (bool): Flag to indicate whether to load the spatial extension.
        """
        with duckdb.connect(self.db_path) as con:
            if attach_pgsql:
                con.execute(
                    f"""ATTACH '{self.db_con_str}' AS postgres_db (TYPE POSTGRES)"""
                )
                load_spatial = True
            if load_spatial:
                con.load_extension("spatial")
            # con.load_extension("json")
            con.execute(query)


class CustomExport:
    """
    Constructor for the custom export class.

    Parameters:
    - params (DynamicCategoriesModel): An instance of DynamicCategoriesModel containing configuration settings.
    """

    def __init__(self, params):
        self.params = params
        self.iso3 = self.params.iso3
        self.HDX_SUPPORTED_FORMATS = ["geojson", "gpkg", "kml", "shp"]
        if self.iso3:
            self.iso3 = self.iso3.lower()
        self.cid = None
        if self.iso3:
            dbdict = get_db_connection_params()
            d_b = Database(dbdict)
            con, cur = d_b.connect()
            query = get_country_from_iso(self.iso3)
            cur.execute(query)
            result = cur.fetchall()
            if not result:
                raise HTTPException(status_code=404, detail="Invalid iso3 code")
            result = result[0]
            (
                self.cid,
                dataset_title,
                dataset_prefix,
                dataset_locations,
            ) = result

            if not self.params.dataset.dataset_title:
                self.params.dataset.dataset_title = dataset_title
            if not self.params.dataset.dataset_prefix:
                self.params.dataset.dataset_prefix = dataset_prefix
            if not self.params.dataset.dataset_locations:
                self.params.dataset.dataset_locations = json.loads(dataset_locations)

        self.uuid = str(uuid.uuid4().hex)
        self.parallel_process_state = False
        self.default_export_base_name = (
            self.iso3.upper() if self.iso3 else self.params.dataset.dataset_prefix
        )
        self.default_export_path = os.path.join(
            export_path,
            self.uuid,
            self.params.dataset.dataset_folder,
            self.default_export_base_name,
        )
        if os.path.exists(self.default_export_path):
            shutil.rmtree(self.default_export_path, ignore_errors=True)
        os.makedirs(self.default_export_path)

        if USE_DUCK_DB_FOR_CUSTOM_EXPORTS is True:
            self.duck_db_db_path = os.path.join(
                self.default_export_path,
                f"{self.default_export_base_name}.db",
            )
            self.duck_db_instance = DuckDB(self.duck_db_db_path)

    def types_to_tables(self, type_list: list):
        """
        Maps feature types to corresponding database tables.

        Parameters:
        - type_list (List[str]): List of feature types.

        Returns:
        - List of database tables associated with the given feature types.
        """
        mapping = {
            "points": ["nodes"],
            "lines": ["ways_line", "relations"],
            "polygons": ["ways_poly", "relations"],
        }

        table_set = set()

        for t in type_list:
            if t in mapping:
                table_set.update(mapping[t])

        return list(table_set)

    def format_where_clause_duckdb(self, where_clause):
        """
        Formats the where_clause by replacing the first occurrence of the pattern.

        Parameters:
        - where_clause (str): SQL-like condition to filter features.

        Returns:
        - Formatted where_clause.
        """
        pattern = r"tags\['([^']+)'\]"
        for match in re.finditer(pattern, where_clause):
            key = match.group(1)
            string_in_pattern = f"tags['{key}']"
            replacement = f"{string_in_pattern}[1]"
            where_clause = where_clause.replace(string_in_pattern, replacement)

        return where_clause

    def upload_resources(self, resource_path):
        """
        Uploads a resource file to Amazon S3.

        Parameters:
        - resource_path (str): Path to the resource file on the local filesystem.

        Returns:
        - Download URL for the uploaded resource.
        """
        if USE_S3_TO_UPLOAD:
            s3_upload_name = os.path.relpath(
                resource_path, os.path.join(export_path, self.uuid)
            )
            file_transfer_obj = S3FileTransfer()
            download_url = file_transfer_obj.upload(
                resource_path,
                str(s3_upload_name),
            )
            return download_url
        return resource_path

    def zip_to_s3(self, resources):
        """
        Zips and uploads a list of resources to Amazon S3.

        Parameters:
        - resources (List[Dict[str, Any]]): List of resource dictionaries.

        Returns:
        - List of resource dictionaries with added download URLs.
        """
        for resource in resources:
            temp_zip_path = resource["url"]
            resource["url"] = self.upload_resources(resource_path=temp_zip_path)
            os.remove(temp_zip_path)
        return resources

    def file_to_zip(self, working_dir, zip_path):
        """
        Creates a ZIP file from files in a directory.

        Parameters:
        - working_dir (str): Path to the directory containing files to be zipped.
        - zip_path (str): Path to the resulting ZIP file.

        Returns:
        - Path to the created ZIP file.
        """
        zf = zipfile.ZipFile(
            zip_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            allowZip64=True,
        )

        for file_path in pathlib.Path(working_dir).iterdir():
            zf.write(file_path, arcname=file_path.name)
        utc_now = datetime.now(timezone.utc)
        utc_offset = utc_now.strftime("%z")
        # Adding metadata readme.txt
        readme_content = f"Exported Timestamp (UTC{utc_offset}): {utc_now.strftime('%Y-%m-%d %H:%M:%S')}\n"
        readme_content += DEFAULT_README_TEXT
        zf.writestr("Readme.txt", readme_content)
        if self.params.geometry:
            zf.writestr("clipping_boundary.geojson", self.params.geometry.json())
        zf.close()
        shutil.rmtree(working_dir)
        return zip_path

    def query_to_file(self, query, category_name, feature_type, export_formats):
        """
        Executes a query and exports the result to file(s).

        Parameters:
        - query (str): SQL query to execute.
        - category_name (str): Name of the category.
        - feature_type (str): Feature type.
        - export_formats (List[ExportTypeInfo]): List of export formats.

        Returns:
        - List of resource dictionaries containing export information.
        """
        category_name = slugify(category_name.lower()).replace("-", "_")
        file_export_path = os.path.join(
            self.default_export_path, category_name, feature_type
        )
        resources = []

        def process_export_format(export_format):
            export_format = EXPORT_TYPE_MAPPING.get(export_format)
            export_format_path = os.path.join(file_export_path, export_format.suffix)
            os.makedirs(export_format_path, exist_ok=True)
            start = time.time()
            logging.info(
                "Processing %s:%s", category_name.lower(), export_format.suffix
            )

            export_filename = f"""{self.params.dataset.dataset_prefix}_{category_name}_{feature_type}_{export_format.suffix}"""
            export_file_path = os.path.join(
                export_format_path, f"{export_filename}.{export_format.suffix}"
            )

            if os.path.exists(export_file_path):
                os.remove(export_file_path)

            layer_creation_options_str = (
                " ".join(
                    [f"'{option}'" for option in export_format.layer_creation_options]
                )
                if export_format.layer_creation_options
                else ""
            )
            if USE_DUCK_DB_FOR_CUSTOM_EXPORTS is True:
                executable_query = f"""COPY ({query.strip()}) TO '{export_file_path}' WITH (FORMAT {export_format.format_option}{f", DRIVER '{export_format.driver_name}'{f', LAYER_CREATION_OPTIONS {layer_creation_options_str}' if layer_creation_options_str else ''}" if export_format.format_option == 'GDAL' else ''})"""
                self.duck_db_instance.run_query(
                    executable_query.strip(), load_spatial=True
                )
            else:
                ogr2ogr_cmd = generate_ogr2ogr_cmd_from_psql(
                    export_file_path=export_file_path,
                    export_file_format_driver=export_format.driver_name,
                    postgres_query=query.strip(),
                    layer_creation_options=layer_creation_options_str,
                    query_dump_path=export_format_path,
                )
                run_ogr2ogr_cmd(ogr2ogr_cmd)

            zip_file_path = os.path.join(file_export_path, f"{export_filename}.zip")
            zip_path = self.file_to_zip(export_format_path, zip_file_path)

            resource = {}
            resource["name"] = f"{export_filename}.zip"
            resource["url"] = zip_path
            resource["format"] = export_format.suffix
            resource["description"] = export_format.driver_name
            resource["size"] = os.path.getsize(zip_path)
            resource["last_modifed"] = datetime.now().isoformat()
            logging.info(
                "Done %s:%s in %s",
                category_name.lower(),
                export_format.suffix,
                humanize.naturaldelta(timedelta(seconds=(time.time() - start))),
            )
            return resource

        if (
            self.parallel_process_state is False
            and len(export_formats) > 1
            and PARALLEL_PROCESSING_CATEGORIES is True
        ):
            logging.info(
                "Using Parallel Processing for %s Export formats with total %s workers",
                category_name.lower(),
                os.cpu_count(),
            )
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=os.cpu_count()
            ) as executor:
                futures = [
                    executor.submit(process_export_format, export_format)
                    for export_format in export_formats
                ]
                resources = [
                    future.result()
                    for future in concurrent.futures.as_completed(futures)
                ]
                resources = [
                    future.result()
                    for future in tqdm(
                        concurrent.futures.as_completed(futures),
                        total=len(futures),
                        desc=f"{category_name.lower()}: Processing Export Formats",
                    )
                ]
        else:
            for exf in export_formats:
                resource = process_export_format(exf)
                resources.append(resource)
        return resources

    def process_category_result(self, category_result):
        """
        Processes the result of a category and prepares the response.

        Parameters:
        - category_result (CategoryResult): Instance of CategoryResult.

        Returns:
        - Dictionary containing processed category result.
        """
        if self.params.hdx_upload and ENABLE_HDX_EXPORTS:
            return self.resource_to_hdx(
                uploaded_resources=category_result.uploaded_resources,
                dataset_config=self.params.dataset,
                category=category_result.category,
            )

        return self.resource_to_response(
            category_result.uploaded_resources, category_result.category
        )

    def process_category(self, category):
        """
        Processes a category by executing queries and handling exports.

        Parameters:
        - category (Dict[str, CategoryModel]): Dictionary representing a category.

        Returns:
        - List of resource dictionaries containing export information.
        """
        category_name, category_data = list(category.items())[0]
        category_start_time = time.time()
        logging.info("Started Processing %s", category_name)
        all_uploaded_resources = []
        for feature_type in category_data.types:
            extract_query = extract_features_custom_exports(
                self.iso3 if self.iso3 else self.params.dataset.dataset_prefix,
                category_data.select,
                feature_type,
                (
                    self.format_where_clause_duckdb(category_data.where)
                    if USE_DUCK_DB_FOR_CUSTOM_EXPORTS is True
                    else category_data.where
                ),
                geometry=self.params.geometry if self.params.geometry else None,
                cid=self.cid,
            )
            resources = self.query_to_file(
                extract_query,
                category_name,
                feature_type,
                list(set(category_data.formats)),
            )

            uploaded_resources = self.zip_to_s3(resources)
            all_uploaded_resources.extend(uploaded_resources)
        logging.info(
            "Done Processing %s in %s ",
            category_name,
            humanize.naturaldelta(
                timedelta(seconds=(time.time() - category_start_time))
            ),
        )
        return all_uploaded_resources

    def resource_to_response(self, uploaded_resources, category):
        """
        Converts uploaded resources to a response format.

        Parameters:
        - uploaded_resources (List[Dict[str, Any]]): List of resource dictionaries.
        - category (Dict[str, CategoryModel]): Dictionary representing a category.

        Returns:
        - Dictionary containing the response information.
        """
        category_name, category_data = list(category.items())[0]
        return {category_name: {"resources": uploaded_resources}}

    def resource_to_hdx(self, uploaded_resources, dataset_config, category):
        """
        Converts uploaded resources to an HDX dataset and uploads to HDX.

        Parameters:
        - uploaded_resources (List[Dict[str, Any]]): List of resource dictionaries.
        - dataset_config (DatasetConfig): Instance of DatasetConfig.
        - category (Dict[str, CategoryModel]): Dictionary representing a category.

        Returns:
        - Dictionary containing the HDX upload information.
        """
        if any(
            item["format"] in self.HDX_SUPPORTED_FORMATS for item in uploaded_resources
        ):
            uploader = HDXUploader(
                hdx=dataset_config,
                category=category,
                default_category_path=self.default_export_path,
                uuid=self.uuid,
                completeness_metadata={
                    "iso3": self.iso3,
                    "geometry": (
                        {
                            "type": "Feature",
                            "geometry": json.loads(
                                self.params.geometry.model_dump_json()
                            ),
                            "properties": {},
                        }
                        if self.params.geometry
                        else None
                    ),
                },
            )
            logging.info("Initiating HDX Upload")
            uploader.init_dataset()
            non_hdx_resources = []
            for resource in uploaded_resources:
                if resource["format"] in self.HDX_SUPPORTED_FORMATS:
                    uploader.add_resource(resource)
                    resource["uploaded_to_hdx"] = True
                else:
                    non_hdx_resources.append(resource)
            category_name, hdx_dataset_info = uploader.upload_dataset(
                self.params.meta and USE_S3_TO_UPLOAD
            )
            hdx_dataset_info["resources"].extend(non_hdx_resources)
            return {category_name: hdx_dataset_info}

    def clean_resources(self):
        """
        Cleans up temporary resources.
        """
        temp_dir = os.path.join(export_path, self.uuid)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            return True
        return False

    def process_custom_categories(self):
        """
        Processes HDX tags and executes category processing in parallel.

        Returns:
        - Dictionary containing the processed dataset information.
        """
        started_at = datetime.now().isoformat()
        processing_time_start = time.time()
        # clean cateories remove {}
        self.params.categories = [
            category for category in self.params.categories if category
        ]
        if USE_DUCK_DB_FOR_CUSTOM_EXPORTS is True:
            table_type = [
                cat_type
                for category in self.params.categories
                if category
                for cat_type in list(category.values())[0].types
            ]
            where_0_category = None

            if (
                len(self.params.categories) == 1
                and PROCESS_SINGLE_CATEGORY_IN_POSTGRES is True
            ):
                where_0_category = list(self.params.categories[0].values())[0].where

            table_names = self.types_to_tables(list(set(table_type)))
            base_table_name = (
                self.iso3 if self.iso3 else self.params.dataset.dataset_prefix
            )
            for table in table_names:
                create_table = postgres2duckdb_query(
                    base_table_name=base_table_name,
                    table=table,
                    cid=self.cid,
                    geometry=self.params.geometry,
                    single_category_where=where_0_category,
                )
                logging.debug(create_table)
                start = time.time()
                logging.info("Transfer-> Postgres Data to DuckDB Started : %s", table)
                self.duck_db_instance.run_query(create_table.strip(), attach_pgsql=True)
                logging.info(
                    "Transfer-> Postgres Data to DuckDB : %s Done in %s",
                    table,
                    humanize.naturaldelta(timedelta(seconds=(time.time() - start))),
                )

        CategoryResult = namedtuple(
            "CategoryResult", ["category", "uploaded_resources"]
        )

        tag_process_results = []
        dataset_results = []
        if len(self.params.categories) > 1 and PARALLEL_PROCESSING_CATEGORIES is True:
            self.parallel_process_state = True
            logging.info("Starting to Use Parallel Processes")
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=os.cpu_count()
            ) as executor:
                futures = {
                    executor.submit(self.process_category, category): category
                    for category in self.params.categories
                }
                for future in tqdm(
                    concurrent.futures.as_completed(futures),
                    total=len(futures),
                    desc=f"{self.default_export_base_name} : Processing Categories",
                ):
                    category = futures[future]
                    uploaded_resources = future.result()
                    category_result = CategoryResult(
                        category=category, uploaded_resources=uploaded_resources
                    )
                    tag_process_results.append(category_result)
        else:
            resources = self.process_category(self.params.categories[0])
            category_result = CategoryResult(
                category=self.params.categories[0], uploaded_resources=resources
            )
            tag_process_results.append(category_result)
        logging.info("Export generation is done, Moving forward to process result")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(self.process_category_result, result): result
                for result in tag_process_results
            }

            for future in concurrent.futures.as_completed(futures):
                result = futures[future]
                result_data = future.result()
                dataset_results.append(result_data)

        result = {"datasets": dataset_results}
        if self.params.meta:
            if USE_DUCK_DB_FOR_CUSTOM_EXPORTS is True:
                logging.info("Dumping Duck DB to Parquet")
                db_dump_path = os.path.join(
                    self.default_export_path,
                    "DB_DUMP",
                )
                os.makedirs(db_dump_path, exist_ok=True)
                export_db = f"""EXPORT DATABASE '{db_dump_path}' (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000);"""
                self.duck_db_instance.run_query(export_db, load_spatial=True)
                db_zip_download_url = self.upload_resources(
                    self.file_to_zip(
                        working_dir=db_dump_path,
                        zip_path=os.path.join(self.default_export_path, "dbdump.zip"),
                    )
                )
                result["db_dump"] = db_zip_download_url
        processing_time_close = time.time()
        result["elapsed_time"] = humanize.naturaldelta(
            timedelta(seconds=(processing_time_close - processing_time_start))
        )
        result["started_at"] = started_at

        meta_last_run_dump_path = os.path.join(self.default_export_path, "meta.json")
        with open(meta_last_run_dump_path, "w", encoding="UTF-8") as json_file:
            json.dump(result, json_file, indent=4)
        self.upload_resources(resource_path=meta_last_run_dump_path)
        self.clean_resources()
        return result


class HDXUploader:
    """
    Constructor for the HDXUploader class.

    Parameters:
    - category (Dict[str, CategoryModel]): Dictionary representing a category.
    - hdx (HDX): Instance of the HDX class.
    - uuid (str): Universally unique identifier.
    - default_category_path (str): Default path for the category.
    - completeness_metadata (Optional[Dict[str, Any]]): Metadata for completeness.
    """

    def __init__(
        self, category, hdx, uuid, default_category_path, completeness_metadata=None
    ):
        self.hdx = hdx
        self.category_name, self.category_data = list(category.items())[0]
        self.category_path = os.path.join(
            default_category_path, slugify(self.category_name.lower()).replace("-", "_")
        )
        self.dataset = None
        self.uuid = uuid
        self.completeness_metadata = completeness_metadata
        self.data_completeness_stats = None
        self.resources = []

    def slugify(self, name):
        """
        Converts a string to a valid slug format.

        Parameters:
        - name (str): Input string.

        Returns:
        - Slugified string.
        """
        return slugify(name).replace("-", "_")

    def add_notes(self):
        """
        Adds notes based on category data.

        Returns:
        - Notes string.
        """
        columns = []
        for key in self.category_data.select:
            columns.append(
                "- [{0}](http://wiki.openstreetmap.org/wiki/Key:{0})".format(key)
            )
        columns = "\n".join(columns)
        filter_str = HDX_FILTER_CRITERIA.format(criteria=self.category_data.where)
        if self.category_name.lower() in ["roads", "buildings"]:
            if self.data_completeness_stats is None:
                if self.completeness_metadata:
                    self.data_completeness_stats = PolygonStats(
                        iso3=self.completeness_metadata["iso3"],
                        geojson=(
                            self.completeness_metadata["geometry"]
                            if self.completeness_metadata["geometry"]
                            else None
                        ),
                    ).get_summary_stats()
            if self.data_completeness_stats:
                self.category_data.hdx.notes += f'{self.data_completeness_stats["summary"][self.category_name.lower()]}\n'
                self.category_data.hdx.notes += "Read about what this summary means : [indicators](https://github.com/hotosm/raw-data-api/tree/develop/docs/src/stats/indicators.md) , [metrics](https://github.com/hotosm/raw-data-api/tree/develop/docs/src/stats/metrics.md)\n"

        return self.category_data.hdx.notes + HDX_MARKDOWN.format(
            columns=columns, filter_str=filter_str
        )

    def add_resource(self, resource_meta):
        """
        Adds a resource to the list of resources.

        Parameters:
        - resource_meta (Dict[str, Any]): Metadata for the resource.
        """
        if self.dataset:
            self.resources.append(resource_meta)
            resource_obj = Resource(resource_meta)
            resource_obj.mark_data_updated()
            self.dataset.add_update_resource(resource_obj)

    def upload_dataset(self, dump_config_to_s3=False):
        """
        Uploads the dataset to HDX.

        Parameters:
        - dump_config_to_s3 (bool): Flag to indicate whether to dump configuration to S3.

        Returns:
        - Tuple containing category name and dataset information.
        """
        if self.dataset:
            dataset_info = {}
            dt_config_path = os.path.join(
                self.category_path, f"{self.dataset['name']}_config.json"
            )
            self.dataset.save_to_json(dt_config_path)
            if dump_config_to_s3:
                s3_upload_name = os.path.relpath(
                    dt_config_path, os.path.join(export_path, self.uuid)
                )
                file_transfer_obj = S3FileTransfer()
                dataset_info["config"] = file_transfer_obj.upload(
                    dt_config_path,
                    str(s3_upload_name),
                )

            self.dataset.set_time_period(datetime.now())
            try:
                self.dataset.create_in_hdx(
                    allow_no_resources=True,
                    hxl_update=False,
                )
                dataset_info["hdx_upload"] = "SUCCESS"
            except Exception as ex:
                logging.error(ex)
                dataset_info["hdx_upload"] = "FAILED"

            dataset_info["name"] = self.dataset["name"]
            dataset_info["hdx_url"] = f"{HDX_URL_PREFIX}/dataset/{self.dataset['name']}"
            dataset_info["resources"] = self.resources
            return self.category_name, dataset_info

    def init_dataset(self):
        """
        Initializes the HDX dataset.
        """
        dataset_prefix = self.hdx.dataset_prefix
        dataset_title = self.hdx.dataset_title
        dataset_locations = self.hdx.dataset_locations
        self.dataset = Dataset(
            {
                "name": "{0}_{1}".format(
                    dataset_prefix, self.slugify(self.category_name)
                ),
                "title": "{0} {1} (OpenStreetMap Export)".format(
                    dataset_title, self.category_name
                ),
                "owner_org": HDX_OWNER_ORG,
                "maintainer": HDX_MAINTAINER,
                "dataset_source": "OpenStreetMap contributors",
                "methodology": "Other",
                "methodology_other": "Volunteered geographic information",
                "license_id": "hdx-odc-odbl",
                "updated_by_script": f'Hotosm OSM Exports ({datetime.now().strftime("%Y-%m-%dT%H:%M:%S")})',
                "caveats": self.category_data.hdx.caveats,
                "private": self.hdx.private,
                "notes": self.add_notes(),
                "subnational": 1 if self.hdx.subnational else 0,
            }
        )
        self.dataset.set_expected_update_frequency(self.hdx.update_frequency)
        for location in dataset_locations:
            self.dataset.add_other_location(location)
        for tag in self.category_data.hdx.tags:
            self.dataset.add_tag(tag)


class HDX:
    def __init__(self) -> None:
        """
        Initializes an instance of the HDX class, connecting to the database.
        """
        dbdict = get_db_connection_params()
        self.d_b = Database(dbdict)
        self.con, self.cur = self.d_b.connect()

    def create_hdx(self, hdx_data):
        """
        Create a new HDX entry in the database.

        Args:
            hdx_data (dict): Data for creating the HDX entry.

        Returns:
            dict: Result of the HDX creation process.
        """
        insert_query = sql.SQL(
            """
            INSERT INTO public.hdx (iso3, hdx_upload, dataset, queue, meta, categories, geometry)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        )
        self.cur.execute(
            insert_query,
            (
                hdx_data.get("iso3", None),
                hdx_data.get("hdx_upload", True),
                json.dumps(hdx_data.get("dataset")),
                hdx_data.get("queue", "raw_ondemand"),
                hdx_data.get("meta", False),
                json.dumps(hdx_data.get("categories", {})),
                json.dumps(hdx_data.get("geometry")),
            ),
        )
        self.con.commit()
        self.d_b.close_conn()
        result = self.cur.fetchone()
        if result:
            return {"create": True}
        raise HTTPException(status_code=500, detail="Insert failed")

    def get_hdx_list_with_filters(
        self, skip: int = 0, limit: int = 10, filters: dict = {}
    ):
        """
        Retrieve a list of HDX entries based on provided filters.

        Args:
            skip (int): Number of entries to skip.
            limit (int): Maximum number of entries to retrieve.
            filters (dict): Filtering criteria.

        Returns:
            List[dict]: List of HDX entries.
        """
        filter_conditions = []
        filter_values = []

        for key, value in filters.items():
            filter_conditions.append(key)
            filter_values.append(value)

        where_clause = " AND ".join(filter_conditions)

        select_query = sql.SQL(
            f"""
            SELECT ST_AsGeoJSON(c.*) FROM public.hdx c
            {"WHERE " + where_clause if where_clause else ""}
            OFFSET %s LIMIT %s
        """
        )

        self.cur.execute(select_query, tuple(filter_values) + (skip, limit))

        result = self.cur.fetchall()
        self.d_b.close_conn()
        return [orjson.loads(item[0]) for item in result]

    def search_hdx_by_dataset_title(
        self, dataset_title: str, skip: int = 0, limit: int = 10
    ):
        """
        Search for HDX entries by dataset title.

        Args:
            dataset_title (str): The title of the dataset to search for.
            skip (int): Number of entries to skip.
            limit (int): Maximum number of entries to retrieve.

        Returns:
            List[dict]: List of HDX entries matching the dataset title.
        """
        search_query = sql.SQL(
            """
            SELECT ST_AsGeoJSON(c.*) FROM public.hdx c
            WHERE c.dataset->>'dataset_title' ILIKE %s
            OFFSET %s LIMIT %s
            """
        )
        self.cur.execute(search_query, ("%" + dataset_title + "%", skip, limit))
        result = self.cur.fetchall()
        self.d_b.close_conn()
        return [orjson.loads(item[0]) for item in result]

    def get_hdx_by_id(self, hdx_id: int):
        """
        Retrieve a specific HDX entry by its ID.

        Args:
            hdx_id (int): ID of the HDX entry to retrieve.

        Returns:
            dict: Details of the requested HDX entry.

        Raises:
            HTTPException: If the HDX entry is not found.
        """
        select_query = sql.SQL(
            """
            SELECT ST_AsGeoJSON(c.*) FROM public.hdx c
            WHERE id = %s
        """
        )
        self.cur.execute(select_query, (hdx_id,))
        result = self.cur.fetchone()
        self.d_b.close_conn()
        if result:
            return orjson.loads(result[0])
        raise HTTPException(status_code=404, detail="Item not found")

    def update_hdx(self, hdx_id: int, hdx_data):
        """
        Update an existing HDX entry in the database.

        Args:
            hdx_id (int): ID of the HDX entry to update.
            hdx_data (dict): Data for updating the HDX entry.

        Returns:
            dict: Result of the HDX update process.

        Raises:
            HTTPException: If the HDX entry is not found.
        """
        update_query = sql.SQL(
            """
            UPDATE public.hdx
            SET iso3 = %s, hdx_upload = %s, dataset = %s, queue = %s, meta = %s, categories = %s, geometry = %s
            WHERE id = %s
            RETURNING *
        """
        )
        self.cur.execute(
            update_query,
            (
                hdx_data.get("iso3", None),
                hdx_data.get("hdx_upload", True),
                json.dumps(hdx_data.get("dataset")),
                hdx_data.get("queue", "raw_ondemand"),
                hdx_data.get("meta", False),
                json.dumps(hdx_data.get("categories", {})),
                json.dumps(hdx_data.get("geometry")),
                hdx_id,
            ),
        )
        self.con.commit()
        result = self.cur.fetchone()
        self.d_b.close_conn()
        if result:
            return {"update": True}
        raise HTTPException(status_code=404, detail="Item not found")

    def patch_hdx(self, hdx_id: int, hdx_data: dict):
        """
        Partially update an existing HDX entry in the database.

        Args:
            hdx_id (int): ID of the HDX entry to update.
            hdx_data (dict): Data for partially updating the HDX entry.

        Returns:
            dict: Result of the HDX update process.

        Raises:
            HTTPException: If the HDX entry is not found.
        """
        if not hdx_data:
            raise ValueError("No data provided for update")

        set_clauses = []
        params = []
        for field, value in hdx_data.items():
            set_clauses.append(sql.SQL("{} = %s").format(sql.Identifier(field)))
            if isinstance(value, dict):
                params.append(json.dumps(value))
            else:
                params.append(value)

        query = sql.SQL("UPDATE public.hdx SET {} WHERE id = %s RETURNING *").format(
            sql.SQL(", ").join(set_clauses)
        )
        params.append(hdx_id)

        self.cur.execute(query, tuple(params))
        self.con.commit()
        result = self.cur.fetchone()
        self.d_b.close_conn()

        if result:
            return {"update": True}
        raise HTTPException(status_code=404, detail="Item not found")

    def delete_hdx(self, hdx_id: int):
        """
        Delete an existing HDX entry from the database.

        Args:
            hdx_id (int): ID of the HDX entry to delete.

        Returns:
            dict: Result of the HDX deletion process.

        Raises:
            HTTPException: If the HDX entry is not found.
        """
        delete_query = sql.SQL(
            """
            DELETE FROM public.hdx
            WHERE id = %s
            RETURNING *
        """
        )
        self.cur.execute(delete_query, (hdx_id,))
        self.con.commit()
        result = self.cur.fetchone()
        self.d_b.close_conn()
        if result:
            return dict(result[0])
        raise HTTPException(status_code=404, detail="HDX item not found")
