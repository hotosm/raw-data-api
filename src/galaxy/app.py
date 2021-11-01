'''Main page contains class for database mapathon and funtion for error printing  '''

import sys
from psycopg2 import connect
from psycopg2.extras import DictCursor
from psycopg2 import OperationalError, errorcodes, errors
from pydantic import validator
from .validation.mapathon import *
from .query_builder.mapathon import *
import json 
import pandas
import os

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
    def __init__(self,db_dict, parameters):
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
        report = MapathonSummary(total_contributors=total_contributors[0][0],
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
        contributors = [MapathonContributor(**r) for r in result]
        report = MapathonDetail(contributors=contributors,
                                mapped_features=mapped_features)
        return report.json()


class Output: 
    """Class to convert sql query result to specific output format"""
    def __init__(self,sql_query,connection):
        """Class takes query and connection as parameter"""
        try:
            self.dataframe= pandas.read_sql(sql_query,connection)
        except Exception as err:
            print_psycopg2_exception(err)
    
    def to_JSON(self):
        """Function to convert query result to JSON, Returns JSON"""
        js = self.dataframe.to_json(orient = 'records')
        return js
    
    def to_CSV(self,output_file_path):
        """Function to return CSV data , takes output location string as input"""
        if os.path.isfile(output_file_path) is True:
            os.remove(output_file_path)
        try:
            self.dataframe.to_csv(output_file_path,encoding='utf-8')
            return "CSV: Generated"
        except Exception as err:
            raise err

    def dataframe(self):
        """Function to return panda's dataframe for advanced users"""
        return self.dataframe



    
