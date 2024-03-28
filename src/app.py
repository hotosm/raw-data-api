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
from src.config_old import (
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
from src.config_old import EXPORT_PATH as export_path
from src.config_old import INDEX_THRESHOLD as index_threshold
from src.config_old import (
    PARALLEL_PROCESSING_CATEGORIES,
    POLYGON_STATISTICS_API_URL,
    PROCESS_SINGLE_CATEGORY_IN_POSTGRES,
)
from src.config_old import USE_CONNECTION_POOLING as use_connection_pooling
from src.config_old import (
    USE_DUCK_DB_FOR_CUSTOM_EXPORTS,
    USE_S3_TO_UPLOAD,
    get_db_connection_params,
    level,
)
from src.config_old import logger as logging
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
        # Reader imports
        import duckdb
        from src.config_old import DUCK_DB_MEMORY_LIMIT, DUCK_DB_THREAD_LIMIT

if ENABLE_HDX_EXPORTS:
    # Reader imports
    from hdx.data.dataset import Dataset
    from hdx.data.resource import Resource
    from src.config_old import HDX_MAINTAINER, HDX_OWNER_ORG, HDX_URL_PREFIX


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
