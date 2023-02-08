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
from json import dumps
from json import loads as json_loads

import boto3
import orjson
from area import area
from fastapi import HTTPException
from geojson import FeatureCollection
from psycopg2 import OperationalError, connect
from psycopg2.extras import DictCursor

from src.config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    BUCKET_NAME,
    export_path,
    get_db_connection_params,
    grid_index_threshold,
    level,
)
from src.config import logger as logging
from src.config import use_connection_pooling
from src.query_builder.builder import (
    check_last_updated_rawdata,
    extract_geometry_type_query,
    get_country_id_query,
    get_grid_id_query,
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
        # start_time=time.time()
        logging.debug("Calling command : %s", cmd)
        process = subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            shell=True,
            preexec_fn=os.setsid,
            timeout=60 * 60 * 6,  # setting timeout of 6 hour
        )
        logging.debug(process)
    except Exception as ex:
        logging.error(ex.output)
        # process.kill()
        # # Send the signal to all the process groups
        # os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        # if os.path.exists(binding_file_dir):
        #     shutil.rmtree(binding_file_dir)
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
            logging.debug("Database connection has been Successful...")
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
                dbdict = get_db_connection_params("RAW_DATA")
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
        db_items = get_db_connection_params("RAW_DATA")
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
                db=db_items.get("database"),
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
                db=db_items.get("database"),
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
                db=db_items.get("database"),
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
        db_items = get_db_connection_params("RAW_DATA")
        # format query if it has " in string"
        query_path = os.path.join(working_dir, "export_query.sql")
        # writing to .sql to pass in ogr2ogr because we don't want to pass too much argument on command with sql
        with open(query_path, "w", encoding="UTF-8") as file:
            file.write(query)
        # for mbtiles we need additional input as well i.e. minzoom and maxzoom , setting default at max=22 and min=10
        if outputtype == RawDataOutputType.MBTILES.value:
            cmd = """ogr2ogr -overwrite -f MBTILES  -dsco MINZOOM={min_zoom} -dsco MAXZOOM={max_zoom} {export_path} PG:"host={host} user={username} dbname={db} password={password}" -sql @"{pg_sql_select}" -lco ENCODING=UTF-8 -progress""".format(
                min_zoom=params.min_zoom,
                max_zoom=params.max_zoom,
                export_path=dump_temp_path,
                host=db_items.get("host"),
                username=db_items.get("user"),
                db=db_items.get("database"),
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
                db=db_items.get("database"),
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
                db=db_items.get("database"),
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
                db=db_items.get("database"),
                password=db_items.get("password"),
                pg_sql_select=query_path,
            )
            run_ogr2ogr_cmd(cmd)

        if outputtype == RawDataOutputType.CSV.value:
            cmd = """ogr2ogr -overwrite -f CSV  {export_path} PG:"host={host} port={port} user={username} dbname={db} password={password}" -sql @"{pg_sql_select}" -lco -progress""".format(
                export_path=dump_temp_path,
                host=db_items.get("host"),
                port=db_items.get("port"),
                username=db_items.get("user"),
                db=db_items.get("database"),
                password=db_items.get("password"),
                pg_sql_select=query_path,
            )
            run_ogr2ogr_cmd(cmd)

        if outputtype == RawDataOutputType.GEOPACKAGE.value:
            cmd = """ogr2ogr -overwrite -f GPKG {export_path} PG:"host={host} port={port} user={username} dbname={db} password={password}" -sql @"{pg_sql_select}" -lco -progress""".format(
                export_path=dump_temp_path,
                host=db_items.get("host"),
                port=db_items.get("port"),
                username=db_items.get("user"),
                db=db_items.get("database"),
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
    def get_grid_id(geom, cur, country_export=False):
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
        # only apply grid in the logic if it exceeds the 5000 Sqkm
        grid_id = None

        # country = None

        if int(geom_area) > grid_index_threshold or country_export:
            # this will be applied only when polygon gets bigger we will be slicing index size to search
            country_query = get_country_id_query(geometry_dump)
            # check if polygon intersects two countries
            cur.execute(country_query)
            # count = 0
            result_country = cur.fetchall()
            logging.debug(result_country)
            countries = [f[0] for f in result_country] 
            if country_export:
                if len(countries)>0:
                    for row in result_country:
                        countries = row[0]  # get which has higher % intersection
                        break
            # for s in result_country:
            #     count += 1
            # if count == 1:  # intersects with only one country
            #     for row in result_country:
            #         country = row[0]
            #         break
            # else:  # intersect with multiple countries or no country ,  use grid index instead
            #     if country_export:  # force country index
            #         # if count == 0:
            #         #     # geom didn't intersected with any country
            #         #     logging.warning("Geom didn't intersect with any country")
            #         #     # use default grid index
            #         #     #TODO
            #         #     # cur.execute(get_grid_id_query(geometry_dump))
            #         #     # grid_id = cur.fetchall()
            #         # else:
            #         for row in result_country:
            #             country = row[0]  # get which has higher % intersection
            #             break
            #     else:
            #         country=coun
            #     #     cur.execute(get_grid_id_query(geometry_dump))
            #     #     grid_id = cur.fetchall()
            cur.close()
        return grid_id, geometry_dump, geom_area, countries if len(countries)>0 else None

    @staticmethod
    def to_geojson_raw(results):
        """Responsible for geojson writing"""
        features = [orjson.loads(row[0]) for row in results]
        feature_collection = FeatureCollection(features=features)

        return feature_collection

    def extract_current_data(self, exportname):
        """Responsible for Extracting rawdata current snapshot, Initially it creates a geojson file , Generates query , run it with 1000 chunk size and writes it directly to the geojson file and closes the file after dump
        Args:
            exportname: takes filename as argument to create geojson file passed from routers

        Returns:
            geom_area: area of polygon supplied
            working_dir: dir where results are saved
        """
        # first check either geometry needs grid or not for querying
        grid_id, geometry_dump, geom_area, country = RawData.get_grid_id(
            self.params.geometry, self.cur, self.params.country_export
        )
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
            if output_type == RawDataOutputType.GEOJSON.value:
                RawData.query2geojson(
                    self.con,
                    raw_currentdata_extraction_query(
                        self.params,
                        g_id=grid_id,
                        c_id=country,
                        geometry_dump=geometry_dump,
                    ),
                    dump_temp_file_path,
                )  # uses own conversion class
            elif output_type == RawDataOutputType.SHAPEFILE.value:
                (
                    point_query,
                    line_query,
                    poly_query,
                    point_schema,
                    line_schema,
                    poly_schema,
                ) = extract_geometry_type_query(
                    self.params, ogr_export=True, g_id=grid_id, c_id=country
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
            else:
                RawData.ogr_export(
                    query=raw_currentdata_extraction_query(
                        self.params, grid_id, country, geometry_dump, ogr_export=True
                    ),
                    outputtype=output_type,
                    dump_temp_path=dump_temp_file_path,
                    working_dir=working_dir,
                    params=self.params,
                )  # uses ogr export to export
            return geom_area, working_dir
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

    def extract_plain_geojson(self):
        """Gets geojson for small area : Performs direct query with/without geometry"""
        query = raw_extract_plain_geojson(self.params, inspect_only=True)
        self.cur.execute(query)
        analyze_fetched = self.cur.fetchall()
        rows = list(
            filter(lambda x: x.startswith("rows"), analyze_fetched[0][0].split())
        )
        approx_returned_rows = rows[0].split("=")[1]
        logging.debug("Approximated query output : %s", approx_returned_rows)

        if int(approx_returned_rows) > 500:
            self.cur.close()
            RawData.close_con(self.con)
            raise HTTPException(
                status_code=500,
                detail=f"Query returned {approx_returned_rows} rows (This endpoint supports upto 1000) , Use /current-snapshot/ for larger extraction",
            )

        extraction_query = raw_extract_plain_geojson(self.params)
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
        # instantiate upload
        start_time = time.time()

        try:
            if level is log.DEBUG:
                self.s_3.upload_file(
                    file_path,
                    BUCKET_NAME,
                    file_name,
                    Callback=ProgressPercentage(file_path),
                )
            else:
                self.s_3.upload_file(file_path, BUCKET_NAME, file_name)

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


class ProgressPercentage(object):
    """Determines the project percentage of aws s3 upload file call

    Args:
        object (_type_): _description_
    """

    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        """returns log percentage"""
        # To simplify, assume this is hooked up to a single filename
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            logging.debug(
                "\r%s  %s / %s  (%.2f%%)",
                self._filename,
                self._seen_so_far,
                self._size,
                percentage,
            )
