import sys
from psycopg2 import connect
from configparser import ConfigParser
from psycopg2.extras import DictCursor
from psycopg2 import OperationalError, errorcodes, errors
from pydantic import validator
from .validation import *
from .query_builder import *

# Reading database credentials from config.txt
config = ConfigParser()
config.read("config.txt")

# print(dict(config.items("PG")))


# function that handles and parses psycopg2 exceptions
def print_psycopg2_exception(err):
    # details_exception
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

    # Database class constructor
    def __init__(self, db_params):
        self.db_params = db_params
        print('Database class object created...')

    # Database class instance method

    def connect(self):
        try:
            self.conn = connect(**self.db_params)
            self.cur = self.conn.cursor(cursor_factory=DictCursor)
            print('Database connection has been Successful...')
            return self.conn, self.cur
        except OperationalError as err:
            # pass exception to function
            print_psycopg2_exception(err)
            # set the connection to 'None' in case of error
            self.conn = None

    def executequery(self, query):
        # Check if the connection was successful
        try:
            if self.conn != None:
                self.cursor = self.cur
                print("cursor object:", self.cursor, "\n")
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

        #function for clossing connection to avoid memory leaks
    def close_conn(self):
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
    #constructor
    def __init__(self, parameters):
        self.database = Database(dict(config.items("INSIGHTS_PG")))
        self.con, self.cur = self.database.connect()
        #parameter validation using pydantic model
        self.params = MapathonRequestParams(**parameters)

    # Mapathon class instance method
    def get_summary(self):
        changeset_query, hashtag_filter, timestamp_filter = create_changeset_query(
            self.params, self.con, self.cur)
        osm_history_query = create_osm_history_query(changeset_query,
                                                     with_username=False)
        result = self.database.executequery(osm_history_query)
        mapped_features = [MappedFeature(**r) for r in result]
        total_contributor_query = f"""
                SELECT COUNT(distinct user_id) as contributors_count
                FROM osm_changeset
                WHERE {timestamp_filter} AND ({hashtag_filter})
            """
        # print(total_contributor_query.encode('utf-8'))
        # print(str(osm_history_query))

        total_contributors = self.database.executequery(
            total_contributor_query)
        report = MapathonSummary(total_contributors=total_contributors[0][0],
                                 mapped_features=mapped_features)
        return report.json()
