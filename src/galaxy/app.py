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

import sys
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
            return True,r_json
        except Exception as e:
            return False,None

class Database:
    """ Database class is used to connect with your database , run query  and get result from it . It has all tests and validation inside class """
    def __init__(self, db_params):
        """Database class constructor"""

        self.db_params = db_params
        print('Database class object created...')

    def connect(self):
        """Database class instance method used to connect to database parameters with error printing"""

        try:
            self.conn = connect(**self.db_params)
            self.cur = self.conn.cursor(cursor_factory=DictCursor)
            print('Database connection has been Successful...')
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
                # catch exception for invalid SQL statement
               
                try:
                    self.cursor.execute(query)
                    try:
                        result = self.cursor.fetchall()
                        # print(result)
                        return result
                    except:
                        return self.cursor.statusmessage
                except Exception as err:
                    print_psycopg2_exception(err)

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
                    print("Connection closed")
        except Exception as err:
            raise err

class Mapathon:
    """Class for mapathon detail report and summary report this is the class that self connects to database and provide you summary and detail report."""
    #constructor
    def __init__(self, db_dict, parameters):
        self.database = Database(db_dict)
        self.con, self.cur = self.database.connect()
        #parameter validation using pydantic model
        self.params = MapathonRequestParams(**parameters)

    # Mapathon class instance method
    def get_summary(self):
        """Function to get summary of your mapathon event """

        changeset_query, hashtag_filter, timestamp_filter = create_changeset_query(
            self.params, self.con, self.cur)
        osm_history_query = create_osm_history_query(changeset_query,
                                                     with_username=False)
        # print(osm_history_query)
        result = self.database.executequery(osm_history_query)
        mapped_features = [MappedFeature(**r) for r in result]
        total_contributor_query = f"""
                SELECT COUNT(distinct user_id) as contributors_count
                FROM osm_changeset
                WHERE {timestamp_filter} AND ({hashtag_filter})
            """
        # print(osm_history_query.encode('utf-8'))

        total_contributors = self.database.executequery(
            total_contributor_query)
        report = MapathonSummary(total_contributors=total_contributors[0].get("contributors_count","None"),
                                 mapped_features=mapped_features)
        return report.json()

    def get_detailed_report(self):
        """Function to get detail report of your mapathon event. It includes individual user contribution"""

        changeset_query, _, _ = create_changeset_query(self.params, self.con,
                                                       self.cur)
        # History Query
        osm_history_query = create_osm_history_query(changeset_query,
                                                     with_username=True)
        result = self.database.executequery(osm_history_query)

        mapped_features = [MappedFeatureWithUser(**r) for r in result]
        # Contribution Query
        contributors_query = create_users_contributions_query(
            self.params, changeset_query)
        # print(contributors_query.encode('utf-8'))
        result = self.database.executequery(contributors_query)
        # contributors = parse_obj_as(List[MapathonContributor], result)
        contributors = [MapathonContributor(**r) for r in result]
        report = MapathonDetail(contributors=contributors,
                                mapped_features=mapped_features)
        # print(Output(osm_history_query,self.con).to_list())
        return report.json()


class Output:
    '''
    Class to convert sql query result to specific output format. It uses Pandas Dataframe
    Parameters:
        supports : list, dict , json and sql query string along with connection
    Returns:
        json,csv,dict,list,dataframe   
    '''
    def __init__(self, result, connection=None):
        """Constructor"""
        if isinstance(result, (list, dict)):
            print(type(result))
            try:
                self.dataframe = pandas.DataFrame(result)
            except Exception as err:
                raise err
        elif isinstance(result, str):
            check, r_json = check_for_json(result)
            if check is True:
                print("i am json")
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
        if self.dataframe.empty : 
            raise ValueError("Dataframe is Null")

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
        if os.path.isfile(output_file_path) is True:
            os.remove(output_file_path)
        try:
            self.dataframe.to_csv(output_file_path, encoding='utf-8')
            return "CSV: Generated"
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
    def __init__(self,db_dict):
        self.db = Database(db_dict)
        self.con, self.cur = self.db.connect()

    def list_users(self, params):
        user_names_str = ",".join(["%s" for n in range(len(params.user_names))])

        query = sql.SQL(f"""SELECT DISTINCT user_id, user_name from osm_changeset
        WHERE created_at between %s AND %s AND user_name IN ({user_names_str})
        """)

        items = (params.from_timestamp, params.to_timestamp, *params.user_names)
        list_users_query = self.cur.mogrify(query, items)

        result = self.db.executequery(list_users_query)

        users_list = [User(**r) for r in result]

        return users_list

    def get_statistics(self, params):
        query = """
            SELECT (each(tags)).key as feature, action, count(distinct id)
            FROM osm_element_history
            WHERE timestamp BETWEEN %s AND %s
            AND uid = %s
            AND type in ('way','relation')
            GROUP BY feature, action
        """

        items = (params.from_timestamp, params.to_timestamp, params.user_id)
        query = self.cur.mogrify(query, items)

        result = self.db.executequery(query)
        summary = [MappedFeature(**r) for r in result]

        return summary

    def get_statistics_with_hashtags(self, params):
        changeset_query, _, _ = create_changeset_query(params, self.con, self.cur)

        # Include user_id filter.
        changeset_query = f"{changeset_query} AND user_id = {params.user_id}"

        base_query = """
            SELECT (each(osh.tags)).key as feature, osh.action, count(distinct osh.id)
            FROM osm_element_history AS osh, T1
            WHERE osh.timestamp BETWEEN %s AND %s
            AND osh.uid = %s
            AND osh.type in ('way','relation')
            AND T1.changeset_id = osh.changeset
            GROUP BY feature, action
        """
        items = (params.from_timestamp, params.to_timestamp, params.user_id)
        base_query = self.cur.mogrify(base_query, items).decode()

        query = f"""
            WITH T1 AS (
                {changeset_query}
            )
            {base_query}
        """

        result = self.db.executequery(query)

        summary = [MappedFeature(**r) for r in result]

        return summary


class DataQuality:
    '''
    Class for data quality report this is the class that self connects to database and provide you detail report about data quality inside specific tasking manager project
    Parameters:
            “project_ids”:[],
            “issue_types”: ["bad_geometry", "bad_value", "incomplete_tags", "all"] 
    Returns:
            JSON    
    '''
    def __init__(self, db_dict, parameters):
        self.db = Database(db_dict)
        self.con, self.cur = self.db.connect()
        #parameter validation using pydantic model
        print(parameters)
        self.params = DataQualityRequestParams(**parameters)

    '''Using pydantic model'''
    # def get_report(self):
    #     """Functions that returns data_quality Report"""
    #     query = data_quality_query(self.params)
    #     print(query)

    #     result = self.db.executequery(query)
    #     print(result)
    #     dataquality_point = [
    #         DataQualityPointFeature(**json.loads(p[0])) for p in result
    #     ]
    #     dataquality_coll = DataQualityPointCollection(
    #         features=dataquality_point)
    #     print(dataquality_coll.json())
    #     return dataquality_coll.json()
    ''' Using our Output class '''

    def get_report(self):
        """Functions that returns data_quality Report"""
      
        query = data_quality_query(self.params)
        result = Output(query, self.con).to_GeoJSON('lat', 'lng')
        print(result)
        return result

