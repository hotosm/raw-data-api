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
import random
import re
import shutil
import subprocess
import sys
import time
import uuid
from collections import Counter, namedtuple
from datetime import datetime, timedelta, timezone
from json import dumps
from json import loads as json_loads

# Third party imports
import boto3
import humanize
import orjson
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
    ENABLE_SOZIP,
    ENABLE_TILES,
    EXPORT_MAX_AREA_SQKM,
    LOG_LEVEL,
    MAX_WORKERS,
    PARALLEL_PROCESSING_CATEGORIES,
    PROCESS_SINGLE_CATEGORY_IN_POSTGRES,
    USE_DUCK_DB_FOR_CUSTOM_EXPORTS,
    USE_S3_TO_UPLOAD,
    get_db_connection_params,
    level,
)
from src.config import EXPORT_PATH as export_path
from src.config import INDEX_THRESHOLD as index_threshold
from src.config import logger as logging
from src.query_builder.builder import (
    HDX_FILTER_CRITERIA,
    HDX_MARKDOWN,
    check_last_updated_rawdata,
    extract_features_custom_exports,
    extract_geometry_type_query,
    get_osm_feature_query,
    postgres2duckdb_query,
    raw_currentdata_extraction_query,
)
from src.utils import create_working_dir
from src.validation.models import EXPORT_TYPE_MAPPING, RawDataOutputType

from .post_processing.processor import PostProcessor

if ENABLE_SOZIP:
    # Third party imports
    import sozipfile.sozipfile as zipfile
else:
    # Standard library imports
    import zipfile

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

    def __init__(self, parameters=None, request_uid="raw-data-api", dbdict=None):
        if parameters:
            self.params = parameters
        if not dbdict:
            dbdict = get_db_connection_params()
        self.d_b = Database(dict(dbdict))
        self.con, self.cur = self.d_b.connect()
        self.base_export_working_dir = os.path.join(export_path, request_uid)

    @staticmethod
    def close_con(con):
        """Close database connection."""
        if con:
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
                    else "-dsco MINZOOM=10 -dsco MAXZOOM=15"
                ),
            }
            format_options[RawDataOutputType.PMTILES.value] = {
                "format": "PMTiles",
                "extra": (
                    "-dsco MINZOOM={} -dsco MAXZOOM={} ".format(
                        params.min_zoom, params.max_zoom
                    )
                    if params.min_zoom and params.max_zoom
                    else "-dsco MINZOOM=10 -dsco MAXZOOM=15"
                ),
            }
            format_options[RawDataOutputType.MVT.value] = {
                "format": "MVT",
                "extra": (
                    "-t_srs EPSG:3857 -dsco MINZOOM={} -dsco MAXZOOM={} -dsco COMPRESS=NO".format(
                        params.min_zoom, params.max_zoom
                    )
                    if params.min_zoom and params.max_zoom
                    else "-t_srs EPSG:3857 -dsco MINZOOM=10 -dsco MAXZOOM=15 -dsco COMPRESS=NO"
                ),
            }

        file_name_option = (
            f"-nln {params.file_name if params.file_name else 'raw_export'}"
        )

        if outputtype == RawDataOutputType.FLATGEOBUF.value and params.fgb_wrap_geoms:
            format_options[outputtype]["extra"] += " -nlt GEOMETRYCOLLECTION"

        format_option = format_options.get(outputtype, {"format": "", "extra": ""})

        if format_option["format"] in [
            "Parquet"
        ]:  # those layers which doesn't support overwrite if layer is not present
            begin = "ogr2ogr -f"
        else:
            begin = "ogr2ogr -overwrite -f"

        cmd = f'{begin} {format_option["format"]} {dump_temp_path} PG:"host={db_items.get("host")} port={db_items.get("port")} user={db_items.get("user")} dbname={db_items.get("dbname")} password={db_items.get("password")}" -sql @{query_path} -lco ENCODING=UTF-8 -progress {format_option["extra"]} {file_name_option}'
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
    def get_geometry_info(geom):
        """Gets geometry information for the geometry that is passed

        Args:
            geom: Geometry object

        Returns:
            tuple: geometry dump and the area of geometry in sqkm
        """
        geometry_dump = dumps(dict(geom))
        geom_area = area(json_loads(geom.json())) * 1e-6
        return (geometry_dump, geom_area)

    def extract_current_data(self, exportname):
        """Responsible for Extracting rawdata current snapshot, Initially it creates a geojson file , Generates query , run it with 1000 chunk size and writes it directly to the geojson file and closes the file after dump
        Args:
            exportname: takes filename as argument to create geojson file passed from routers

        Returns:
            geom_area: area of polygon supplied
            working_dir: dir where results are saved
        """
        geometry_dump, geom_area = RawData.get_geometry_info(self.params.geometry)
        output_type = self.params.output_type
        # Check whether the export path exists or not
        working_dir = os.path.join(self.base_export_working_dir, exportname)
        if not os.path.exists(working_dir):
            # Create a exports directory because it does not exist
            create_working_dir(working_dir)
        # create file path with respect to of output type

        dump_temp_file_path = os.path.join(
            working_dir,
            f"{self.params.file_name if self.params.file_name else 'Export'}{f'.{output_type.lower()}'}",
        )

        try:
            # currently we have only geojson binding function written other than that we have depend on ogr
            if ENABLE_TILES:
                if output_type in [
                    RawDataOutputType.PMTILES.value,
                    RawDataOutputType.MBTILES.value,
                    RawDataOutputType.MVT.value,
                ]:
                    dump_temp_file_path = os.path.join(
                        working_dir,
                        f"{self.params.file_name if self.params.file_name else 'Export'}{'' if output_type == RawDataOutputType.MVT.value else f'.{output_type.lower()}'}",
                    )
                    RawData.ogr_export(
                        query=raw_currentdata_extraction_query(
                            self.params,
                            ogr_export=True,
                        ),
                        outputtype=output_type,
                        dump_temp_file_path=dump_temp_file_path,
                        working_dir=working_dir,
                        params=self.params,
                    )

            if output_type == RawDataOutputType.GEOJSON.value:
                RawData.query2geojson(
                    self.con,
                    raw_currentdata_extraction_query(self.params),
                    dump_temp_file_path,
                )
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
                        ogr_export=True,
                    ),
                    outputtype=output_type,
                    dump_temp_file_path=dump_temp_file_path,
                    working_dir=working_dir,
                    params=self.params,
                )
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

    def cleanup(self):
        """
        Cleans up temporary resources.
        """

        if os.path.exists(self.base_export_working_dir):
            shutil.rmtree(self.base_export_working_dir)
            return True
        return False


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
            if type(file_path) == str and file_path[-5:] == ".html":
                self.s_3.upload_file(
                    str(file_path),
                    BUCKET_NAME,
                    str(file_name),
                    ExtraArgs={"ContentType": "text/html"},
                )
            else:
                self.s_3.upload_file(str(file_path), BUCKET_NAME, str(file_name))
        except Exception as ex:
            logging.error(ex)
            raise ex
        logging.debug("Uploaded %s in %s sec", file_name, time.time() - start_time)
        # generate the download url
        bucket_location = self.get_bucket_location(bucket_name=BUCKET_NAME)
        object_url = f"""https://s3.dualstack.{bucket_location}.amazonaws.com/{BUCKET_NAME}/{file_name}"""
        return object_url


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
        con.sql(f"""SET temp_directory = '{os.path.join(duck_db_temp, "temp.tmp")}'""")

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

    def __init__(self, params, uid=None):
        self.params = params
        self.HDX_SUPPORTED_FORMATS = ["geojson", "gpkg", "kml", "shp"]
        self.cid = None
        self.uuid = uid
        if self.uuid is None:
            self.uuid = str(uuid.uuid4().hex)

        self.parallel_process_state = False
        self.default_export_base_name = self.params.dataset.dataset_prefix

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

            if resource.get("stats_html"):
                temp_stats_html_path = resource["stats_html"]
                resource["stats_html"] = self.upload_resources(
                    resource_path=temp_stats_html_path
                )
                os.remove(temp_stats_html_path)

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
                format_option = export_format.format_option

                driver_and_layer_options = ""
                if format_option == "GDAL":
                    driver_and_layer_options = f", DRIVER '{export_format.driver_name}'"
                    if layer_creation_options_str:
                        driver_and_layer_options += f", SRS 'EPSG:4326', LAYER_CREATION_OPTIONS {layer_creation_options_str}"

                executable_query = f"""
                    COPY ({query.strip()}) 
                    TO '{export_file_path}' 
                    WITH (FORMAT {format_option}{driver_and_layer_options})
                """

                # executable_query = f"""COPY ({query.strip()}) TO '{export_file_path}' WITH (FORMAT {export_format.format_option}{f", DRIVER '{export_format.driver_name}'{f", SRS 'EPSG:4326', LAYER_CREATION_OPTIONS {layer_creation_options_str}" if layer_creation_options_str else ''}" if export_format.format_option == 'GDAL' else ''})"""
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

            # Post-processing GeoJSON files
            # Adds: stats, HTML stats summary and transliterations
            if export_format.driver_name == "GeoJSON" and (
                self.params.include_stats or self.params.include_translit
            ):
                post_processor = PostProcessor(
                    {
                        "include_stats": self.params.include_stats,
                        "include_translit": self.params.include_translit,
                        "include_stats_html": self.params.include_stats_html,
                    }
                )
                post_processor.stats(
                    category_name=category_name,
                    export_format_path=export_format_path,
                    export_filename=export_filename,
                    file_export_path=file_export_path,
                )

            zip_file_path = os.path.join(file_export_path, f"{export_filename}.zip")
            zip_path = self.file_to_zip(export_format_path, zip_file_path)

            resource = {}
            resource["name"] = f"{export_filename}.zip"
            resource["url"] = zip_path
            resource["format"] = export_format.suffix
            resource["description"] = export_format.driver_name
            resource["size"] = os.path.getsize(zip_path)
            if (
                self.params.include_stats_html
                and export_format.driver_name == "GeoJSON"
            ):
                resource["stats_html"] = f"{file_export_path}/stats-summary.html"

            # resource["last_modified"] = datetime.now().isoformat()
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
                MAX_WORKERS,
            )
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=int(MAX_WORKERS)
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
                self.params.dataset.dataset_prefix,
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
        return self.process_category_result(
            namedtuple("CategoryResult", ["category", "uploaded_resources"])(
                category=category, uploaded_resources=all_uploaded_resources
            )
        )

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
                    "dataset_prefix": self.params.dataset.dataset_prefix,
                    "geometry": {
                        "type": "Feature",
                        "geometry": json.loads(self.params.geometry.model_dump_json()),
                        "properties": {},
                    },
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
            category_name, cron_dataset_info = uploader.upload_dataset(
                self.params.meta and USE_S3_TO_UPLOAD
            )
            cron_dataset_info["resources"].extend(non_hdx_resources)
            return {category_name: cron_dataset_info}

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
        Processes Custom tags and executes category processing in parallel.

        Returns:
        - Dictionary containing the processed dataset information.
        """
        started_at = datetime.now().isoformat()
        processing_time_start = time.time()
        # clean cateories remove {}
        self.params.categories = [
            category for category in self.params.categories if category
        ]
        # Sort categories: Process "building" or "buildings" last
        self.params.categories = sorted(
            self.params.categories,
            key=lambda category: list(category.keys())[0].lower()
            in {"building", "buildings"},
        )

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
            base_table_name = self.params.dataset.dataset_prefix
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
                    uploaded_resources = future.result()
                    dataset_results.append(uploaded_resources)

        else:
            uploaded_resources = self.process_category(self.params.categories[0])
            dataset_results.append(uploaded_resources)
        logging.info("Export generation is done")

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

            # Add customviz if available
            if resource_meta.get("stats_html"):
                dataset_customviz = self.dataset.get("customviz")
                if not dataset_customviz:
                    dataset_customviz = [
                        {
                            "name": resource_meta["name"],
                            "url": resource_meta["stats_html"],
                        }
                    ]
                else:
                    dataset_customviz.append(
                        {
                            "name": resource_meta["name"],
                            "url": resource_meta["stats_html"],
                        }
                    )
                self.dataset.update({"customviz": dataset_customviz})

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
                if LOG_LEVEL == "DEBUG":
                    raise ex
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
                "updated_by_script": f"Hotosm OSM Exports ({datetime.now().strftime('%Y-%m-%dT%H:%M:%S')})",
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


class DownloadMetrics:
    def __init__(self) -> None:
        dbdict = get_db_connection_params()
        self.d_b = Database(dbdict)
        self.con, self.cur = self.d_b.connect()

    def get_summary_stats(
        self,
        start_date: str,
        end_date: str,
        group_by: str,
        folders=None,
        include_locations: bool = False,
        include_referrers: bool = False,
    ):
        """
        Get summary statistics for downloads and uploads."""
        # normalize folders to list
        folder_list = []
        if folders:
            folder_list = [folders] if isinstance(folders, str) else list(folders)

        # build SELECT columns
        cols = [
            f"date_trunc('{group_by}', date) AS kwdate",
            "SUM((summary->>'downloads_count')::numeric) AS total_downloads_count",
            "SUM((summary->>'uploads_count')::numeric) AS total_uploads_count",
            "SUM((summary->>'unique_users')::numeric) AS total_unique_users",
            "SUM((summary->>'unique_downloads')::numeric) AS total_unique_downloads",
            "SUM((summary->>'interactions_count')::numeric) AS total_interactions_count",
            "SUM((summary->>'upload_size')::numeric) AS total_upload_size",
            "SUM((summary->>'download_size')::numeric) AS total_download_size",
        ]
        if include_locations:
            cols.append("JSONB_AGG((summary->>'locations')::json) AS total_locations")
        if include_referrers:
            cols.append("JSONB_AGG((summary->>'referrers')::json) AS total_referrers")

        select_cols = ",\n                ".join(cols)

        # build FROM/JOIN and WHERE
        if folder_list:
            folders_sql = ",".join(f"'{fld}'" for fld in folder_list)
            # lateral join on folders JSON
            from_clause = (
                "metrics CROSS JOIN LATERAL jsonb_each(folders) AS f(key,value)"
            )
            # override base metrics cols to use f.value not summary
            cols = [
                f"date_trunc('{group_by}', date) AS kwdate",
                "SUM((f.value->>'downloads_count')::numeric) AS total_downloads_count",
                "SUM((f.value->>'uploads_count')::numeric) AS total_uploads_count",
                "SUM((f.value->>'unique_users')::numeric) AS total_unique_users",
                "SUM((f.value->>'unique_downloads')::numeric) AS total_unique_downloads",
                "SUM((f.value->>'interactions_count')::numeric) AS total_interactions_count",
                "SUM((f.value->>'upload_size')::numeric) AS total_upload_size",
                "SUM((f.value->>'download_size')::numeric) AS total_download_size",
            ]
            if include_locations:
                cols.append(
                    "JSONB_AGG((f.value->>'locations')::json) AS total_locations"
                )
            if include_referrers:
                cols.append(
                    "JSONB_AGG((summary->>'referrers')::json) AS total_referrers"
                )
            select_cols = ",\n                ".join(cols)
            where_clause = f"date BETWEEN '{start_date}' AND '{end_date}' AND f.key IN ({folders_sql})"
        else:
            from_clause = "metrics"
            where_clause = f"date BETWEEN '{start_date}' AND '{end_date}'"

        # assemble query
        select_query = f"""
            SELECT
                {select_cols}
            FROM
                {from_clause}
            WHERE
                {where_clause}
            GROUP BY
                kwdate
            ORDER BY
                kwdate
        """

        self.cur.execute(select_query)
        rows = self.cur.fetchall()
        self.d_b.close_conn()

        results = []
        for item in rows:
            rec = dict(item)
            # ensure kwdate is a string
            if hasattr(item["kwdate"], "isoformat"):
                rec["kwdate"] = item["kwdate"].date().isoformat()
            if include_locations:
                rec["total_locations"] = dict(
                    sum((Counter(loc) for loc in item["total_locations"]), Counter())
                )
            else:
                rec["total_locations"] = {}
            if include_referrers:
                rec["total_referrers"] = dict(
                    sum((Counter(ref) for ref in item["total_referrers"]), Counter())
                )
            else:
                rec["total_referrers"] = {}
            results.append(rec)
        return results

    def get_meta_downloads(
        self,
        start_date: str,
        end_date: str,
        group_by: str,
        key_prefixes=None,
        limit: int = 100,
        offset: int = 0,
    ):
        """Get metadata download counts per file key."""
        prefixes = (
            [key_prefixes]
            if isinstance(key_prefixes, str)
            else list(key_prefixes or [])
        )
        filter_clause = ""
        if prefixes:
            patterns = ",".join(f"'{pref.strip()}%'" for pref in prefixes)
            filter_clause = f"AND t.key ILIKE ANY(ARRAY[{patterns}]::text[])"

        select_query = f"""
            SELECT
                date_trunc('{group_by}', date) AS kwdate,
                jsonb_object_agg(t.key, (t.value::text)::int) AS downloads_by_file
            FROM
                metrics,
                jsonb_each_text(meta_downloads) AS t(key,value)
            WHERE
                date BETWEEN '{start_date}' AND '{end_date}'
                {filter_clause}
            GROUP BY
                kwdate
            ORDER BY
                kwdate
            LIMIT {limit} OFFSET {offset}
        """

        self.cur.execute(select_query)
        result = self.cur.fetchall()
        self.d_b.close_conn()
        items = []
        for item in result:
            rec = dict(item)
            if hasattr(item["kwdate"], "isoformat"):
                rec["kwdate"] = item["kwdate"].date().isoformat()
            items.append(rec)
        return items
