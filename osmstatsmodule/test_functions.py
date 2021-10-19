from osm_stats import functions
import testing.postgresql
import pytest
postgresql=None
database=None

Postgresql = testing.postgresql.PostgresqlFactory(cache_initialized_db=True)

def setup_module(module):
    print('*****SETUP*****')
    global postgresql,database
    postgresql = Postgresql()
    database= functions.Database(postgresql.dsn())
    database.connect()
    print(postgresql.dsn())
    
def teardown_module(module):
    print('******TEARDOWN******')
    database.close_conn()
    Postgresql.clear_cache()

def test_create(): 
    createtable=f""" CREATE TABLE test_table (id int, value varchar(256))"""
    print(database.executequery(createtable))

def test_insert():
    insertvalue=f""" INSERT INTO test_table values(1, 'hello'), (2, 'namaste')"""
    print(database.executequery(insertvalue))

def test_query():
    query=f""" SELECT * from test_table;"""
    print(database.executequery(query))
