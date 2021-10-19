from osm_stats import functions
import testing.postgresql
import pytest

# Reference to testing.postgresql db instance
postgresql=None

# Connection to database and query running class from our osm_stats module

database=None


# Generate Postgresql class which shares the generated database so that we could use it in all test function (now we don't need to create db everytime whenever the test runs)
Postgresql = testing.postgresql.PostgresqlFactory(cache_initialized_db=True)

def setup_module(module):
    """ Module level set-up called once before any tests in this file are
    executed.  shares a temporary database created in Postgresql and sets it up """

    print('*****SETUP*****')
    global postgresql,database

    postgresql = Postgresql()
    # passing test credentials to our osm_stat database class for connection 
    """ Default credentials : {'port': **dynamic everytime **, 'host': '127.0.0.1', 'user': 'postgres', 'database': 'test'}"""
    database= functions.Database(postgresql.dsn())
    # To Ensure the database is in a known state before calling the function we're testing
    database.connect()
    # Map of database connection parameters passed to the functions we're testing
    print(postgresql.dsn())
 

def teardown_module(module):
    """ Called after all of the tests in this file have been executed to close
    the database connection and destroy the temporary database """

    print('******TEARDOWN******')
    # close our database connection to avoid memory leaks i.e. available feature in our database class 
    database.close_conn()
    # clear cached database at end of tests
    Postgresql.clear_cache()

def test_create(): 
    createtable=f""" CREATE TABLE test_table (id int, value varchar(256))"""
    print(database.executequery(createtable))

def test_insert():
    insertvalue=f""" INSERT INTO test_table values(1, 'hello'), (2, 'namaste')"""
    print(database.executequery(insertvalue))

def test_query():
    query=f""" SELECT * from test_table;"""
    result=database.executequery(query)
    print(result)
    # validating the query result either it is right or not 
    assert result == [(1, 'hello'), (2, 'namaste')]
