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
'''Main page contains class for database mapathon and funtion for error printing  '''

from .config import get_db_connection_params
from .validation.models import Source
import sys
from fastapi import param_functions
from psycopg2 import connect, sql
from psycopg2.extras import DictCursor
from psycopg2 import OperationalError, errorcodes, errors
from pydantic import validator
from pydantic.types import Json
from pydantic import parse_obj_as
from .validation.models import *
from .query_builder.builder import *
import json
import pandas
import os
from json import loads as json_loads
from geojson import Feature, FeatureCollection, Point
from io import StringIO
from csv import DictWriter
from .config import config
import logging
import orjson
from area import area
import subprocess
from json import dumps
import fiona
from fiona.crs import from_epsg

import logging
# logging.getLogger("imported_module").setLevel(logging.WARNING)
logging.getLogger("fiona").propagate = False  # disable fiona logging


def print_psycopg2_exception(err):
    """ 
    function that handles and parses psycopg2 exceptions
    """
    '''details_exception'''
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
    except Exception as e:
        return False, None


class Database:
    """ Database class is used to connect with your database , run query  and get result from it . It has all tests and validation inside class """

    def __init__(self, db_params):
        """Database class constructor"""

        self.db_params = db_params

    def connect(self):
        """Database class instance method used to connect to database parameters with error printing"""

        try:
            self.conn = connect(**self.db_params)
            self.cur = self.conn.cursor(cursor_factory=DictCursor)
            logging.debug('Database connection has been Successful...')
            return self.conn, self.cur
        except OperationalError as err:
            """pass exception to function"""

            print_psycopg2_exception(err)
            # set the connection to 'None' in case of error
            self.conn = None

    def executequery(self, query):
        """ Function to execute query after connection """
        # Check if the connection was successful
        try:
            if self.conn != None:
                self.cursor = self.cur
                if query != None:
                    # catch exception for invalid SQL statement

                    try:
                        logging.debug('Query sent to Database')
                        self.cursor.execute(query)
                        try:
                            result = self.cursor.fetchall()
                            logging.debug('Result fetched from Database')
                            return result
                        except:
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
            if self.conn != None:
                if self.cursor:
                    self.cursor.close()
                    self.conn.close()
                    logging.debug("Database Connection closed")
        except Exception as err:
            raise err


class Underpass:
    """This class connects to underpass database and responsible for all the underpass related functionality"""

    def __init__(self, parameters=None):
        self.database = Database(get_db_connection_params("UNDERPASS"))
        # self.database = Database(dict(config.items("UNDERPASS")))
        self.con, self.cur = self.database.connect()
        self.params = parameters

    def get_mapathon_summary_result(self):
        osm_history_query, total_contributor_query = generate_mapathon_summary_underpass_query(
            self.params, self.cur)
        # print(osm_history_query)
        osm_history_result = self.database.executequery(osm_history_query)
        total_contributors_result = self.database.executequery(
            total_contributor_query)
        return osm_history_result, total_contributors_result

    def all_training_organisations(self):
        """[Resposible for the total organisations result generation]

        Returns:
            [query_result]: [oid,name]
        """
        training_all_organisations_query = generate_training_organisations_query()
        query_result = self.database.executequery(
            training_all_organisations_query)
        return query_result

    def training_list(self, params):
        filter_training_query = generate_filter_training_query(params)
        training_query = generate_training_query(filter_training_query)
        # print(training_query)
        query_result = self.database.executequery(training_query)
        # print(query_result)
        return query_result


    def get_user_role(self, user_id: int):
        query = f"select role from users_roles where user_id = {user_id}"
        query_result = self.database.executequery(query)

        if len(query_result) == 0:
            return UserRole.NONE

        role_int = query_result[0]["role"]
        user_role = UserRole(role_int)
        
        return user_role


class Insight:
    """This class connects to Insight database and responsible for all the Insight related functionality"""

    def __init__(self, parameters=None):
        self.database = Database(get_db_connection_params("INSIGHTS"))
        # self.database = Database(dict(config.items("INSIGHTS_PG")))
        self.con, self.cur = self.database.connect()
        self.params = parameters

    def get_mapathon_summary_result(self):
        changeset_query, hashtag_filter, timestamp_filter = create_changeset_query(
            self.params, self.con, self.cur)
        osm_history_query = create_osm_history_query(changeset_query,
                                                     with_username=False)
        total_contributor_query = f"""
                SELECT COUNT(distinct user_id) as contributors_count
                FROM osm_changeset
                WHERE {timestamp_filter}
            """
        if len(hashtag_filter) > 0:
            total_contributor_query += f""" AND ({hashtag_filter})"""

        # print(osm_history_query)
        osm_history_result = self.database.executequery(osm_history_query)
        total_contributors_result = self.database.executequery(
            total_contributor_query)
        return osm_history_result, total_contributors_result

    def get_mapathon_detailed_result(self):
        changeset_query, _, _ = create_changeset_query(
            self.params, self.con, self.cur)
        # History Query
        osm_history_query = create_osm_history_query(changeset_query,
                                                     with_username=True)
        contributors_query = create_users_contributions_query(
            self.params, changeset_query)
        osm_history_result = self.database.executequery(osm_history_query)
        total_contributors_result = self.database.executequery(
            contributors_query)
        return osm_history_result, total_contributors_result


class TaskingManager:
    """ This class connects to the Tasking Manager database and is responsible for all the TM related functionality. """

    def __init__(self, parameters=None):
        self.database = Database(get_db_connection_params("TM"))
        self.con, self.cur = self.database.connect()
        self.params = parameters

    def extract_project_ids(self):
        test_hashtag = "hotosm-project-"
        ids = []

        if (len(self.params.project_ids) > 0):
            ids.extend(self.params.project_ids)

        if(len(self.params.hashtags) > 0):
            for hashtag in self.params.hashtags:
                if test_hashtag in hashtag:
                    if len(hashtag[15:]) > 0:
                        ids.append(hashtag[15:])
        return ids

    def get_tasks_mapped_and_validated_per_user(self):
        project_ids = self.extract_project_ids()
        if len(project_ids) > 0:
            tasks_mapped_query, tasks_validated_query = create_user_tasks_mapped_and_validated_query(project_ids,
                                                                                                     self.params.from_timestamp, self.params.to_timestamp)
            tasks_mapped_result = self.database.executequery(
                tasks_mapped_query)
            tasks_validated_result = self.database.executequery(
                tasks_validated_query)
            return tasks_mapped_result, tasks_validated_result
        return [], []

    def get_time_spent_mapping_and_validating_per_user(self):
        project_ids = self.extract_project_ids()
        if len(project_ids) > 0:
            time_spent_mapping_query, time_spent_validating_query = create_user_time_spent_mapping_and_validating_query(project_ids,
                                                                                                                        self.params.from_timestamp, self.params.to_timestamp)
            time_spent_mapping_result = self.database.executequery(
                time_spent_mapping_query)
            time_spent_validating_result = self.database.executequery(
                time_spent_validating_query)
            return time_spent_mapping_result, time_spent_validating_result
        return [], []


    def get_validators_stats(self):
        query = generate_tm_validators_stats_query(self.cur, self.params)
        result = [dict(r) for r in self.database.executequery(query)]

        indexes = ['user_id', 'username']
        columns = ['project_id', 'country', 'total_tasks', 'tasks_mapped', 'tasks_validated']

        df = pandas.DataFrame(result)
        out = pandas.pivot_table(df,
            values='cnt',
            index=indexes,
            columns=columns,
            fill_value=0
        ).swaplevel(0, 1).reset_index()

        stream = StringIO()
        out.to_csv(stream)

        return iter(stream.getvalue())

    def list_teams(self):
        query = generate_tm_teams_list()
        results_dicts = [dict(r) for r in self.database.executequery(query)]

        stream = StringIO()

        csv_keys: List[str] = list(results_dicts[0].keys())
        writer = DictWriter(stream, fieldnames=csv_keys)
        writer.writeheader()

        [writer.writerow(row) for row in results_dicts]

        return iter(stream.getvalue())

    def list_teams_metadata(self):
        query = generate_list_teams_metadata()
        results_dicts = [dict(r) for r in self.database.executequery(query)]

        results_dicts = [{**r, "function": TeamMemberFunction(r["function"]).name.lower()}
            for r in results_dicts]

        stream = StringIO()

        csv_keys: List[str] = list(results_dicts[0].keys())
        writer = DictWriter(stream, fieldnames=csv_keys)
        writer.writeheader()

        [writer.writerow(row) for row in results_dicts]

        return iter(stream.getvalue())


class Mapathon:
    """Class for mapathon detail report and summary report this is the class that self connects to database and provide you summary and detail report."""

    # constructor
    def __init__(self, parameters, source):
        # parameter validation using pydantic model
        if type(parameters) is MapathonRequestParams:
            self.params = parameters
        else:
            self.params = MapathonRequestParams(**parameters)

        if source == "underpass":
            self.database = Underpass(self.params)
        elif source == "insight":
            self.database = Insight(self.params)
        else:
            raise ValueError("Source is not Supported")

    # Mapathon class instance method
    def get_summary(self):
        """Function to get summary of your mapathon event """
        osm_history_result, total_contributors = self.database.get_mapathon_summary_result()
        mapped_features = [MappedFeature(**r) for r in osm_history_result]
        report = MapathonSummary(total_contributors=total_contributors[0].get(
            "contributors_count", "None"),
            mapped_features=mapped_features)
        return report

    def get_detailed_report(self):
        """Function to get detail report of your mapathon event. It includes individual user contribution"""
        osm_history_result, total_contributors = self.database.get_mapathon_detailed_result()
        mapped_features = [MappedFeatureWithUser(
            **r) for r in osm_history_result]
        contributors = [MapathonContributor(**r) for r in total_contributors]

        tm = TaskingManager(self.params)
        tasks_mapped_results, tasks_validated_results = tm.get_tasks_mapped_and_validated_per_user()
        time_mapping_results, time_validating_results = tm.get_time_spent_mapping_and_validating_per_user()
        tasks_mapped_stats, tasks_validated_stats, time_mapping_stats, time_validating_stats = [], [], [], []
        if (len(tasks_mapped_results) > 0):
            for r in tasks_mapped_results:
                r[1] = r[1] if r[1] > 0 else 0
            tasks_mapped_stats = [MappedTaskStats(
                **r) for r in tasks_mapped_results]
        if (len(tasks_validated_results) > 0):
            for r in tasks_validated_results:
                r[1] = r[1] if r[1] > 0 else 0
            tasks_validated_stats = [ValidatedTaskStats(
                **r) for r in tasks_validated_results]
        if (len(time_mapping_results) > 0):
            for t in time_mapping_results:
                t[1] = t[1].total_seconds() if t[1] else 0.0
            time_mapping_stats = [TimeSpentMapping(
                **r) for r in time_mapping_results]
        if (len(time_validating_results) > 0):
            for t in time_validating_results:
                t[1] = t[1].total_seconds() if t[1] else 0.0
            time_validating_stats = [TimeSpentValidating(
                **r) for r in time_validating_results]

        tm_stats = [TMUserStats(tasks_mapped=tasks_mapped_stats,
                                tasks_validated=tasks_validated_stats,
                                time_spent_mapping=time_mapping_stats,
                                time_spent_validating=time_validating_stats)]

        report = MapathonDetail(contributors=contributors,
                                mapped_features=mapped_features,
                                tm_stats=tm_stats)
        # print(Output(osm_history_query,self.con).to_list())
        return report


class Output:
    """Class to convert sql query result to specific output format. It uses Pandas Dataframe

    Parameters:
        supports : list, dict , json and sql query string along with connection

    Returns:
        json,csv,dict,list,dataframe
    """

    def __init__(self, result, connection=None):
        """Constructor"""
        # print(result)
        if isinstance(result, (list, dict)):
            # print(type(result))
            try:
                self.dataframe = pandas.DataFrame(result)
            except Exception as err:
                raise err
        elif isinstance(result, str):
            check, r_json = check_for_json(result)
            if check is True:
                # print("i am json")
                try:
                    self.dataframe = pandas.json_normalize(r_json)
                except Exception as err:
                    raise err
            else:
                if connection is not None:
                    try:
                        self.dataframe = pandas.read_sql_query(
                            result, connection)
                    except Exception as err:
                        raise err
                else:
                    raise ValueError("Connection is required for SQL Query")
        else:
            raise ValueError("Input type " + str(type(result)) +
                             " is not supported")
        # print(self.dataframe)
        if self.dataframe.empty:
            return []

    def get_dataframe(self):
        # print(self.dataframe)
        return self.dataframe

    def to_JSON(self):
        """Function to convert query result to JSON, Returns JSON"""
        # print(self.dataframe)
        js = self.dataframe.to_json(orient='records')
        return js

    def to_list(self):
        """Function to convert query result to list, Returns list"""

        result_list = self.dataframe.values.tolist()
        return result_list

    def to_dict(self):
        """Function to convert query result to dict, Returns dict"""
        dic = self.dataframe.to_dict(orient='records')
        return dic

    def to_CSV(self, output_file_path):
        """Function to return CSV data , takes output location string as input"""
        try:
            self.dataframe.to_csv(output_file_path, encoding='utf-8')
            return "CSV: Generated at : " + str(output_file_path)
        except Exception as err:
            raise err

    def to_GeoJSON(self, lat_column, lng_column):
        '''to_Geojson converts pandas dataframe to geojson , Currently supports only Point Geometry and hence takes parameter of lat and lng ( You need to specify lat lng column )'''
        # print(self.dataframe)
        # columns used for constructing geojson object
        properties = self.dataframe.drop([lat_column, lng_column],
                                         axis=1).to_dict('records')

        features = self.dataframe.apply(
            lambda row: Feature(geometry=Point(
                (float(row[lng_column]), float(row[lat_column]))),
                properties=properties[row.name]),
            axis=1).tolist()

        # whole geojson object
        feature_collection = FeatureCollection(features=features)
        return feature_collection


class UserStats:
    def __init__(self):
        self.db = Database(get_db_connection_params("INSIGHTS"))
        # self.db = Database(dict(config.items("INSIGHTS_PG")))
        self.con, self.cur = self.db.connect()

    def list_users(self, params):
        user_names_str = ",".join(
            ["%s" for n in range(len(params.user_names))])

        query = sql.SQL(
            f"""SELECT DISTINCT user_id, user_name from osm_changeset
        WHERE created_at between %s AND %s AND user_name IN ({user_names_str})
        """)

        items = (params.from_timestamp, params.to_timestamp,
                 *params.user_names)
        list_users_query = self.cur.mogrify(query, items)

        result = self.db.executequery(list_users_query)

        users_list = [User(**r) for r in result]

        return users_list

    def get_statistics(self, params):
        query = create_UserStats_get_statistics_query(params, self.con,
                                                      self.cur)
        result = self.db.executequery(query)
        summary = [UserStatistics(**r) for r in result]
        return summary

    def get_statistics_with_hashtags(self, params):
        query = create_userstats_get_statistics_with_hashtags_query(
            params, self.con, self.cur)
        result = self.db.executequery(query)
        summary = [UserStatistics(**r) for r in result]
        return summary


class DataQualityHashtags:
    def __init__(self, params: DataQualityHashtagParams):
        self.db = Database(get_db_connection_params("UNDERPASS"))
        # self.db = Database(dict(config.items("UNDERPASS")))
        self.con, self.cur = self.db.connect()
        self.params = params

    @staticmethod
    def to_csv_stream(results):
        stream = StringIO()

        features = results.get("features")

        if len(features) == 0:
            return iter("")

        properties_keys = list(features[0].get("properties").keys())
        csv_keys = [*properties_keys, "latitude", "longitude"]

        writer = DictWriter(stream, fieldnames=csv_keys)
        writer.writeheader()

        for row in features:
            longitude, latitude = item.get("geometry").get("coordinates")
            row = {**item.get("properties"),
                   'latitude': latitude, 'longitude': longitude}

            writer.writerow(row)

        return iter(stream.getvalue())

    @staticmethod
    def to_geojson(results):
        features = []
        for row in results:
            geojson_feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [row["lon"], row["lat"]]
                },
                "properties": {
                    "created_at": row["created_at"],
                    "changeset_id": row["changeset_id"],
                    "osm_id": row["osm_id"],
                    "issue_type": row["issues"].split(",")
                }
            }
            features.append(Feature(**geojson_feature))

        feature_collection = FeatureCollection(features=features)

        return feature_collection

    def get_report(self):
        query = generate_data_quality_hashtag_reports(self.cur, self.params)
        results = self.db.executequery(query)
        feature_collection = DataQualityHashtags.to_geojson(results)

        return feature_collection


class DataQuality:
    """Class for data quality report this is the class that self connects to database and provide you detail report about data quality inside specific tasking manager project

    Parameters:
           params and inputtype : Currently supports : TM for tasking manager id , username for OSM Username reports and hashtags for Osm hashtags
    Returns:
        [GeoJSON,CSV ]: [description]
    """

    def __init__(self, parameters, inputtype):
        self.db = Database(get_db_connection_params("UNDERPASS"))
        # self.db = Database(dict(config.items("UNDERPASS")))
        self.con, self.cur = self.db.connect()
        self.inputtype = inputtype
        # parameter validation using pydantic model
        if self.inputtype == "TM":
            if type(parameters) is DataQuality_TM_RequestParams:
                self.params = parameters
            else:
                self.params = DataQuality_TM_RequestParams(**parameters)
        elif self.inputtype == "username":
            if type(parameters) is DataQuality_username_RequestParams:
                self.params = parameters
            else:
                self.params = DataQuality_username_RequestParams(**parameters)
        else:
            raise ValueError("Input Type Must be in ['TM','username']")

    def get_report(self):
        """Functions that returns data_quality Report"""
        if self.inputtype == "TM":
            query = generate_data_quality_TM_query(self.params)
        elif self.inputtype == "username":
            query = generate_data_quality_username_query(self.params, self.cur)
        try:
            result = Output(query, self.con).to_GeoJSON('lat', 'lng')
            return result
        except Exception as err:
            return err
        # print(result)

    def get_report_as_csv(self, filelocation):
        """Functions that returns data_quality Report as CSV Format , requires file path where csv is meant to be generated"""

        if self.inputtype == "TM":
            query = generate_data_quality_TM_query(self.params)
        elif self.inputtype == "username":
            query = generate_data_quality_username_query(self.params, self.cur)
        try:
            result = Output(query, self.con).to_CSV(filelocation)
            return result
        except Exception as err:
            return err


class Training:
    """[Class responsible for Training data API]
    """

    def __init__(self, source):
        if source == Source.UNDERPASS.value:
            self.database = Underpass()
        else:
            raise ValueError("Source is not Supported")

    def get_all_organisations(self):
        """[Generates result for all list of available organisations within the database.]

        Returns:
            [type]: [List of Training Organisations ( id, name )]
        """
        query_result = self.database.all_training_organisations()
        Training_organisations_list = [
            TrainingOrganisations(**r) for r in query_result]
        # print(Training_organisations_list)
        return Training_organisations_list

    def get_trainingslist(self, params: TrainingParams):
        query_result = self.database.training_list(params)
        Trainings_list = [Trainings(**r) for r in query_result]
        # print(Trainings_list)
        return Trainings_list

class OrganizationHashtags:
    """[Class responsible for Organization Hashtag data API]
    """

    def __init__(self, params: OrganizationHashtagParams):
        self.db = Database(get_db_connection_params("INSIGHTS"))
        # self.db = Database(dict(config.items("INSIGHTS_PG")))
        self.con, self.cur = self.db.connect()
        self.params = params
        self.query = generate_organization_hashtag_reports(
            self.cur, self.params)

    def get_report(self):
        query_result = self.db.executequery(self.query)
        results = [OrganizationHashtag(**r) for r in query_result]
        return results

    def get_report_as_csv(self, filelocation):
        try:
            result = Output(self.query, self.con).to_CSV(filelocation)
            return result
        except Exception as err:
            return err  


class RawData:
    """Class responsible for the Rawdata Extraction from available sources , Currently Works for Underpass source Current Snapshot
    Returns:
    Geojson Zip file 
    Supports:
    -Any Key value pair of osm tags 
    -A Polygon
    -Osm element type (Optional)
    """

    def __init__(self, parameters=None,dbdict=None):
        if parameters:
            if type(parameters) is not RawDataCurrentParams:
                self.params = RawDataCurrentParams(**parameters)
            else :
                self.params=parameters

        if dbdict is None :
            self.db = Database(dict(config.items("RAW_DATA")))
        else :
            self.db = Database(dict(dbdict))

        self.con, self.cur = self.db.connect()

    def get_query_con(self):
        """Provides Query and connection to user so that they can perform query by themselves"""
        #options="-c search_path=schema_name" can be used for defining schema in dict
      
        g_id,geom_dump,geom_area=RawData.get_grid_id(self.params.geometry,self.db)
        
        extraction_query=raw_currentdata_extraction_query(self.params, g_id, geom_dump,ogr_export=True)
        
        return self.con,extraction_query


    @staticmethod
    def to_geojson(results):
        """Responsible for converting query result to featurecollection , It is absolute now ~ not used anymore

        Args:
            results (_type_): Query Result geojson per feature string

        Returns:
            _type_: featurecollection
        """
        logging.debug('Geojson Binding Started !')
        feature_collection = FeatureCollection(
            features=[orjson.loads(row[0]) for row in results])
        logging.debug('Geojson Binding Done !')
        return feature_collection

    def extract_historical_data(self):
        """Idea is to extract historical data , Currently not maintained

        Returns:
            _type_: geojson featurecollection
        """
        extraction_query = raw_historical_data_extraction_query(
            self.cur, self.con, self.params)
        results = self.db.executequery(extraction_query)
        return RawData.to_geojson(results)

    @staticmethod
    def ogr_export(outputtype,query=None, export_path=None ,point_query=None, line_query=None, poly_query=None,dump_temp_file_path=None):
        """Function written to support ogr type extractions as well , In this way we will be able to support all file formats supported by Ogr , Currently it is slow when dataset gets bigger as compared to our own conversion method but rich in feature and data types even though it is slow"""
        db_items = dict(config.items("RAW_DATA"))
        if query:
            formatted_query = query.replace('"', '\\"')
        # for mbtiles we need additional input as well i.e. minzoom and maxzoom , setting default at max=22 and min=10
        if outputtype is RawDataOutputType.MBTILES.value:
            cmd = '''ogr2ogr -overwrite -f \"{outputtype}\" -dsco MINZOOM=10 -dsco MAXZOOM=22 {export_path} PG:"host={host} user={username} dbname={db} password={password}" -sql "{pg_sql_select}" -progress'''.format(
                outputtype=outputtype, export_path=export_path, host=db_items.get('host'), username=db_items.get('user'), db=db_items.get('database'), password=db_items.get('password'), pg_sql_select=formatted_query)

        elif outputtype is RawDataOutputType.SHAPEFILE.value: 
            file_paths = []
            outputtype="ESRI Shapefile"
            # print(point_query)
            if point_query:
                formatted_query = point_query.replace('"', '\\"')
                point_file_path = f"""{dump_temp_file_path}_point.shp"""
                cmd = '''ogr2ogr -overwrite -f \"{outputtype}\" {export_path} PG:"host={host} user={username} dbname={db} password={password}" -sql "{pg_sql_select}" -progress'''.format(
                    outputtype=outputtype, export_path=point_file_path, host=db_items.get('host'), username=db_items.get('user'), db=db_items.get('database'), password=db_items.get('password'), pg_sql_select=formatted_query)
                logging.debug("Calling ogr2ogr-Point Shapefile")
                run = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
                logging.debug(run.stdout.read())
                file_paths.append(point_file_path)
                file_paths.append(f"""{dump_temp_file_path}_point.shx""")
                # file_paths.append(f"""{dump_temp_file_path}_point.cpg""")
                file_paths.append(f"""{dump_temp_file_path}_point.dbf""")
                file_paths.append(f"""{dump_temp_file_path}_point.prj""")
            if line_query:
                formatted_query = line_query.replace('"', '\\"')

                line_file_path = f"""{dump_temp_file_path}_line.shp"""
                cmd = '''ogr2ogr -overwrite -f \"{outputtype}\" {export_path} PG:"host={host} user={username} dbname={db} password={password}" -sql "{pg_sql_select}" -progress'''.format(
                    outputtype=outputtype, export_path=line_file_path, host=db_items.get('host'), username=db_items.get('user'), db=db_items.get('database'), password=db_items.get('password'), pg_sql_select=formatted_query)
                logging.debug("Calling ogr2ogr-Line Shapefile")
                run = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
                logging.debug(run.stdout.read())
                file_paths.append(line_file_path)
                file_paths.append(f"""{dump_temp_file_path}_line.shx""")
                # file_paths.append(f"""{dump_temp_file_path}_line.cpg""")
                file_paths.append(f"""{dump_temp_file_path}_line.dbf""")
                file_paths.append(f"""{dump_temp_file_path}_line.prj""")
            if poly_query:
                formatted_query = poly_query.replace('"', '\\"')
                # print(poly_query)
                poly_file_path = f"""{dump_temp_file_path}_poly.shp"""
                cmd = '''ogr2ogr -overwrite -f \"{outputtype}\" {export_path} PG:"host={host} user={username} dbname={db} password={password}" -sql "{pg_sql_select}" -progress'''.format(
                    outputtype=outputtype, export_path=poly_file_path, host=db_items.get('host'), username=db_items.get('user'), db=db_items.get('database'), password=db_items.get('password'), pg_sql_select=formatted_query)
                logging.debug("Calling ogr2ogr-Poly Shapefile")
                run = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
                logging.debug(run.stdout.read())
                file_paths.append(poly_file_path)
                file_paths.append(f"""{dump_temp_file_path}_poly.shx""")
                # file_paths.append(f"""{dump_temp_file_path}_poly.cpg""")
                file_paths.append(f"""{dump_temp_file_path}_poly.dbf""")
                file_paths.append(f"""{dump_temp_file_path}_poly.prj""")
            return file_paths
        else:
            cmd = '''ogr2ogr -overwrite -f \"{outputtype}\" {export_path} PG:"host={host} user={username} dbname={db} password={password}" -sql "{pg_sql_select}" -progress'''.format(
                outputtype=outputtype, export_path=export_path, host=db_items.get('host'), username=db_items.get('user'), db=db_items.get('database'), password=db_items.get('password'), pg_sql_select=formatted_query)
        # print(cmd)
        logging.debug("Calling ogr2ogr")
        run = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        logging.debug(run.stdout.read())
        return export_path

    @staticmethod
    def query2geojson(con, extraction_query, dump_temp_file_path):
        """Function written from scratch without being dependent on any library, Provides better performance for geojson binding"""
        print(extraction_query)
        pre_geojson = """{"type": "FeatureCollection","features": ["""
        post_geojson = """]}"""
        with open(dump_temp_file_path, 'a', encoding='utf-8') as f:  # directly writing query result to the file one by one without holding them in object so that it will not eat up our memory
            f.write(pre_geojson)
            logging.debug('Server side Cursor Query Sent with 1000 Chunk Size')
            with con.cursor(name='fetch_raw') as cursor:  # using server side cursor
                cursor.itersize = 1000  # chunk size to get 1000 row at a time in client side
                cursor.execute(extraction_query)
                first = True
                for row in cursor:
                    if first:
                        first = False
                        f.write(row[0])
                    else:
                        f.write(',')
                        f.write(row[0])
                cursor.close()  # closing connection to avoid memory issues
                con.close()
            f.write(post_geojson)
        f.close()
        logging.debug(f"""Server side Query Result  Post Processing Done""")

    @staticmethod
    def query2shapefile(con, point_query, line_query, poly_query, point_schema, line_schema, poly_schema, dump_temp_file_path):
        # schema: it is a simple dictionary with geometry and properties as keys
        # schema = {'geometry': 'LineString','properties': {'test': 'int'}}
        file_paths = []
        if point_query:
            logging.debug(f"""Writing Point Shapefile""")

            schema = {'geometry': 'Point', 'properties': point_schema, }
            point_file_path = f"""{dump_temp_file_path}_point.shp"""
            # open a fiona object
            pointShp = fiona.open(point_file_path, mode='w', driver='ESRI Shapefile', encoding='UTF-8',
                                  schema=schema, crs="EPSG:4326")

            with con.cursor(name='fetch_raw') as cursor:  # using server side cursor
                cursor.itersize = 1000  # chunk size to get 1000 row at a time in client side
                cursor.execute(point_query)
                for row in cursor:
                    pointShp.write(orjson.loads(row[0]))

                cursor.close()  # closing connection to avoid memory issues
                # close fiona object
            pointShp.close()
            file_paths.append(point_file_path)
            file_paths.append(f"""{dump_temp_file_path}_point.shx""")
            file_paths.append(f"""{dump_temp_file_path}_point.cpg""")
            file_paths.append(f"""{dump_temp_file_path}_point.dbf""")
            file_paths.append(f"""{dump_temp_file_path}_point.prj""")

        if line_query:
            logging.debug(f"""Writing Line Shapefile""")

            schema = {'geometry': 'LineString', 'properties': line_schema, }
            # print(schema)
            line_file_path = f"""{dump_temp_file_path}_line.shp"""
            with fiona.open(line_file_path, 'w', encoding='UTF-8', crs=from_epsg(4326), driver='ESRI Shapefile', schema=schema) as layer:
                with con.cursor(name='fetch_raw') as cursor:  # using server side cursor
                    cursor.itersize = 1000  # chunk size to get 1000 row at a time in client side
                    cursor.execute(line_query)
                    for row in cursor:
                        layer.write(orjson.loads(row[0]))

                    cursor.close()  # closing connection to avoid memory issues
                # close fiona object
                layer.close()
            file_paths.append(line_file_path)
            file_paths.append(f"""{dump_temp_file_path}_line.shx""")
            file_paths.append(f"""{dump_temp_file_path}_line.cpg""")
            file_paths.append(f"""{dump_temp_file_path}_line.dbf""")
            file_paths.append(f"""{dump_temp_file_path}_line.prj""")

        if poly_query:
            logging.debug(f"""Writing Poly Shapefile""")

            poly_file_path = f"""{dump_temp_file_path}_poly.shp"""
            schema = {'geometry': 'Polygon', 'properties': poly_schema, }

            with fiona.open(poly_file_path, 'w', encoding='UTF-8', crs=from_epsg(4326), driver='ESRI Shapefile', schema=schema) as layer:
                with con.cursor(name='fetch_raw') as cursor:  # using server side cursor
                    cursor.itersize = 1000  # chunk size to get 1000 row at a time in client side
                    cursor.execute(poly_query)
                    for row in cursor:
                        layer.write(orjson.loads(row[0]))

                    cursor.close()  # closing connection to avoid memory issues
                # close fiona object
                layer.close()
            file_paths.append(poly_file_path)
            file_paths.append(f"""{dump_temp_file_path}_poly.shx""")
            file_paths.append(f"""{dump_temp_file_path}_poly.cpg""")
            file_paths.append(f"""{dump_temp_file_path}_poly.dbf""")
            file_paths.append(f"""{dump_temp_file_path}_poly.prj""")

        con.close()

        return file_paths
    
    @staticmethod
    def get_grid_id(geom,db):
        geometry_dump = dumps(dict(geom))
        geom_area = int(area(json.loads(geom.json())) * 1E-6)
        if geom_area > 5000:
            # this will be applied only when polygon gets bigger we will be slicing index size to search
            grid_id = db.executequery(
                get_grid_id_query(geometry_dump))
        else:
            grid_id = None
        return grid_id, geometry_dump,geom_area

    def extract_current_data(self, exportname):
        """Responsible for Extracting rawdata current snapshot, Initially it creates a geojson file , Generates query , run it with 1000 chunk size and writes it directly to the geojson file and closes the file after dump 
        Args:
            exportname: takes filename as argument to create geojson file passed from routers

        Returns:
            _file_path_: geojson file location path
        """
        grid_id,geometry_dump,geom_area=RawData.get_grid_id(self.params.geometry,self.db)
        if self.params.output_type is None:
            # if nothing is supplied then default output type will be geojson
            output_type = RawDataOutputType.GEOJSON.value
        else:
            output_type = self.params.output_type
        try:
            path = config.get("EXPORT_CONFIG", "path")
        except : 
            path = 'exports/' # first tries to import from config, if not defined creates exports in home directory 
        
        # print(path)
        # Check whether the export path exists or not
        isExist = os.path.exists(path)
        if not isExist:
            # Create a exports directory because it does not exist
            os.makedirs(path)
        dump_temp_file_path = f"""{path}{exportname}.{output_type.lower()}"""

        # currently we have only geojson binding function written other than that we have depend on ogr
        if output_type is RawDataOutputType.GEOJSON.value:
            RawData.query2geojson(self.con, raw_currentdata_extraction_query(
                self.params, g_id=grid_id, geometry_dump=geometry_dump), dump_temp_file_path)  # uses own conversion class
        elif output_type is RawDataOutputType.SHAPEFILE.value:
            point_query, line_query, poly_query, point_schema, line_schema, poly_schema = extract_geometry_type_query(
                self.params,ogr_export=True)
            dump_temp_file_path = f"""{path}{exportname}"""
            filepaths = RawData.ogr_export(outputtype=output_type,point_query=point_query, line_query=line_query, poly_query=poly_query,dump_temp_file_path=dump_temp_file_path) #using ogr2ogr
            # filepaths = RawData.query2shapefile(self.con, point_query, line_query, poly_query, point_schema, line_schema, poly_schema, dump_temp_file_path) #using fiona
            return filepaths, geom_area
        else:
            filepaths=RawData.ogr_export(query=raw_currentdata_extraction_query(self.params, grid_id, geometry_dump, ogr_export=True), export_path=dump_temp_file_path, outputtype=output_type)  # uses ogr export to export
            
        return [dump_temp_file_path], geom_area

    def check_status(self):
        """Gives status about DB update, Substracts with current time and last db update time"""
        status_query = check_last_updated_rawdata()
        behind_time = self.db.executequery(status_query)
        behind_time_min = behind_time[0][0].total_seconds()/60
        return behind_time_min
