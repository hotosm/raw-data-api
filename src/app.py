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
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from json import dumps
from json import loads as json_loads

import boto3
import humanize
import orjson
import requests
from area import area
from fastapi import HTTPException
from geojson import FeatureCollection
from psycopg2 import OperationalError, connect
from psycopg2.extras import DictCursor

from src.config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    BUCKET_NAME,
    ENABLE_TILES,
    EXPORT_MAX_AREA_SQKM,
)
from src.config import EXPORT_PATH as export_path
from src.config import INDEX_THRESHOLD as index_threshold
from src.config import POLYGON_STATISTICS_API_URL
from src.config import USE_CONNECTION_POOLING as use_connection_pooling
from src.config import get_db_connection_params, level
from src.config import logger as logging
from src.query_builder.builder import (
    check_exisiting_country,
    check_last_updated_rawdata,
    extract_geometry_type_query,
    generate_polygon_stats_graphql_query,
    get_countries_query,
    get_country_geojson,
    get_country_id_query,
    get_osm_feature_query,
    raw_currentdata_extraction_query,
    raw_extract_plain_geojson,
)
from src.validation.models import RawDataOutputType

# import instance for pooling
if use_connection_pooling:
    from src.db_session import database_instance
else:
    database_instance = None
import logging as log

# assigning global variable of pooling so that it
# will be accessible from any function within this script
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
                    logging.debug("Database Connection closed")
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
        """Function written to support ogr type extractions as well , In this way we will be able to support all file formats supported by Ogr , Currently it is slow when dataset gets bigger as compared to our own conversion method but rich in feature and data types even though it is slow"""
        db_items = get_db_connection_params()
        # format query if it has " in string"
        query_path = os.path.join(working_dir, "export_query.sql")
        # writing to .sql to pass in ogr2ogr because we don't want to pass too much argument on command with sql
        with open(query_path, "w", encoding="UTF-8") as file:
            file.write(query)
        # for mbtiles we need additional input as well i.e. minzoom and maxzoom , setting default at max=22 and min=10
        if ENABLE_TILES:
            if outputtype == RawDataOutputType.MBTILES.value:
                if params.min_zoom and params.max_zoom:
                    cmd = """ogr2ogr -overwrite -f MBTILES  -dsco MINZOOM={min_zoom} -dsco MAXZOOM={max_zoom} {export_path} PG:"host={host} user={username} dbname={db} password={password}" -sql @"{pg_sql_select}" -lco ENCODING=UTF-8 -progress""".format(
                        min_zoom=params.min_zoom,
                        max_zoom=params.max_zoom,
                        export_path=dump_temp_path,
                        host=db_items.get("host"),
                        username=db_items.get("user"),
                        db=db_items.get("dbname"),
                        password=db_items.get("password"),
                        pg_sql_select=query_path,
                    )
                else:
                    cmd = """ogr2ogr -overwrite -f MBTILES  -dsco ZOOM_LEVEL_AUTO=YES {export_path} PG:"host={host} user={username} dbname={db} password={password}" -sql @"{pg_sql_select}" -lco ENCODING=UTF-8 -progress""".format(
                        export_path=dump_temp_path,
                        host=db_items.get("host"),
                        username=db_items.get("user"),
                        db=db_items.get("dbname"),
                        password=db_items.get("password"),
                        pg_sql_select=query_path,
                    )
                run_ogr2ogr_cmd(cmd)

        if outputtype == RawDataOutputType.FLATGEOBUF.value:
            cmd = """ogr2ogr -overwrite -f FLATGEOBUF {export_path} PG:"host={host} port={port} user={username} dbname={db} password={password}" -sql @"{pg_sql_select}" -lco ENCODING=UTF-8 -progress VERIFY_BUFFERS=NO""".format(
                export_path=dump_temp_path,
                host=db_items.get("host"),
                port=db_items.get("port"),
                username=db_items.get("user"),
                db=db_items.get("dbname"),
                password=db_items.get("password"),
                pg_sql_select=query_path,
            )
            run_ogr2ogr_cmd(cmd)

        if outputtype == RawDataOutputType.GEOPARQUET.value:
            cmd = """ogr2ogr -overwrite -f Parquet {export_path} PG:"host={host} port={port} user={username} dbname={db} password={password}" -sql @"{pg_sql_select}" -lco ENCODING=UTF-8 -progress""".format(
                export_path=dump_temp_path,
                host=db_items.get("host"),
                port=db_items.get("port"),
                username=db_items.get("user"),
                db=db_items.get("dbname"),
                password=db_items.get("password"),
                pg_sql_select=query_path,
            )
            run_ogr2ogr_cmd(cmd)

        if outputtype == RawDataOutputType.PGDUMP.value:
            cmd = """ogr2ogr -overwrite --config PG_USE_COPY YES -f PGDump {export_path} PG:"host={host} port={port} user={username} dbname={db} password={password}" -sql @"{pg_sql_select}" -lco SRID=4326 -progress""".format(
                export_path=dump_temp_path,
                host=db_items.get("host"),
                port=db_items.get("port"),
                username=db_items.get("user"),
                db=db_items.get("dbname"),
                password=db_items.get("password"),
                pg_sql_select=query_path,
            )
            run_ogr2ogr_cmd(cmd)

        if outputtype == RawDataOutputType.KML.value:
            cmd = """ogr2ogr -overwrite -f KML {export_path} PG:"host={host} port={port} user={username} dbname={db} password={password}" -sql @"{pg_sql_select}" -lco ENCODING=UTF-8 -progress""".format(
                export_path=dump_temp_path,
                host=db_items.get("host"),
                port=db_items.get("port"),
                username=db_items.get("user"),
                db=db_items.get("dbname"),
                password=db_items.get("password"),
                pg_sql_select=query_path,
            )
            run_ogr2ogr_cmd(cmd)

        if outputtype == RawDataOutputType.CSV.value:
            cmd = """ogr2ogr -overwrite -f CSV  {export_path} PG:"host={host} port={port} user={username} dbname={db} password={password}" -sql @"{pg_sql_select}" -lco ENCODING=UTF-8 -progress""".format(
                export_path=dump_temp_path,
                host=db_items.get("host"),
                port=db_items.get("port"),
                username=db_items.get("user"),
                db=db_items.get("dbname"),
                password=db_items.get("password"),
                pg_sql_select=query_path,
            )
            run_ogr2ogr_cmd(cmd)

        if outputtype == RawDataOutputType.GEOPACKAGE.value:
            cmd = """ogr2ogr -overwrite -f GPKG {export_path} PG:"host={host} port={port} user={username} dbname={db} password={password}" -sql @"{pg_sql_select}" -lco ENCODING=UTF-8 -progress""".format(
                export_path=dump_temp_path,
                host=db_items.get("host"),
                port=db_items.get("port"),
                username=db_items.get("user"),
                db=db_items.get("dbname"),
                password=db_items.get("password"),
                pg_sql_select=query_path,
            )
            run_ogr2ogr_cmd(cmd)
        # clear query file we don't need it anymore
        os.remove(query_path)

    @staticmethod
    def query2geojson(con, extraction_query, dump_temp_file_path):
        """Function written from scratch without being dependent on any library, Provides better performance for geojson binding"""
        # creating geojson file
        pre_geojson = """{"type": "FeatureCollection","features": ["""
        post_geojson = """]}"""
        logging.debug(extraction_query)
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
            countries
            if len(countries) > 0 and len(countries) <= 3
            else None,  # don't go through countires if they are more than 3
            country_export,
        )

    @staticmethod
    def geojson2tiles(geojson_path, tile_path, tile_layer_name):
        """Responsible for geojson to tiles"""
        cmd = """tippecanoe -zg --projection=EPSG:4326 -o {tile_output_path} -l {tile_layer_name} {geojson_input_path} --force""".format(
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
                    file_name=self.params.file_name
                    if self.params.file_name
                    else "Export",
                )  # using ogr2ogr
            if output_type in ["fgb", "gpkg", "sql", "parquet", "csv"]:
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

    def upload(self, file_path, file_name, file_suffix="zip"):
        """Used for transferring file to s3 after reading path from the user , It will wait for the upload to complete
        Parameters :file_path --- your local file path to upload ,
            file_prefix -- prefix for the filename which is stored
        sample function call :
            S3FileTransfer.transfer(file_path="exports",file_prefix="upload_test")"""
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

    def __init__(self, geojson):
        """
        Initialize PolygonStats with the provided GeoJSON.

        Args:
            geojson (dict): GeoJSON representation of the polygon.
        """
        self.API_URL = POLYGON_STATISTICS_API_URL
        self.INPUT_GEOM = dumps(geojson)

    @staticmethod
    def get_building_pattern_statement(
        osm_building_count,
        ai_building_count,
        avg_timestamp,
        osm_building_count_6_months,
    ):
        """
        Translates building stats to a human-readable statement.

        Args:
            osm_building_count (int): Count of buildings from OpenStreetMap.
            ai_building_count (int): Count of buildings from AI estimates.
            avg_timestamp (str): Average timestamp of data.
            osm_building_count_6_months (int): Count of buildings updated in the last 6 months.

        Returns:
            str: Human-readable building statement.
        """
        building_statement = f"OpenStreetMap contains roughly {humanize.intword(osm_building_count)} buildings in this region. Based on AI-mapped estimates, this is approximately {round((osm_building_count/ai_building_count)*100)}% of the total buildings. The average age of data for this region is {avg_timestamp}, and {round((osm_building_count_6_months/ai_building_count)*100)}% buildings were added or updated in the last 6 months."
        return building_statement

    @staticmethod
    def get_road_pattern_statement(
        osm_highway_length,
        ai_highway_length,
        avg_timestamp,
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
        road_statement = f"OpenStreetMap contains roughly {humanize.intword(osm_highway_length)} km of roads in this region. Based on AI-mapped estimates, this is approximately {round(osm_highway_length/ai_highway_length*100)} % of the total road length in the dataset region. The average age of data for the region is {avg_timestamp}, and {round((osm_highway_length_6_months/osm_highway_length)*100)}% of roads were added or updated in the last 6 months."
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
            response = requests.post(self.API_URL, json=payload, timeout=20)
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
            100 - combined_data["osmRoadGapsPercentage"]
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
            combined_data["building_count_6_months"],
        )

        road_summary = self.get_road_pattern_statement(
            combined_data["highway_length"],
            combined_data["aiRoadCountEstimation"],
            combined_data["averageEditTime"],
            combined_data["highway_length_6_months"],
        )

        return_stats = {
            "summary": {"building": building_summary, "road": road_summary},
            "raw": {
                "population": combined_data["population"],
                "populatedAreaKm2": combined_data["populatedAreaKm2"],
                "averageEditTime": combined_data["averageEditTime"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "lastEditTime": combined_data["lastEditTime"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "osmBuildingsCount": combined_data["osmBuildingsCount"],
                "osmHighwayLengthKm": combined_data["highway_length"],
                "osmUsersCount": combined_data["osmUsersCount"],
                "aiBuildingsCountEstimationKm": combined_data[
                    "aiBuildingsCountEstimation"
                ],
                "aiRoadCountEstimationKm": combined_data["aiRoadCountEstimation"],
                "buildingCount6Months": combined_data["building_count_6_months"],
                "highwayLength6Months": combined_data["highway_length_6_months"],
            },
            "meta": {
                "indicators": "https://github.com/hotosm/raw-data-api/tree/develop/docs/src/stats/indicators.md",
                "metrics": "https://github.com/hotosm/raw-data-api/tree/develop/docs/src/stats/metrics.md",
            },
        }

        return return_stats
