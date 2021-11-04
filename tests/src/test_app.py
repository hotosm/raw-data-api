#for Relative import let's define our package directory
import sys
print(sys.path)
sys.path.insert(0, './src')

#import libraries 
from galaxy import app
import testing.postgresql
import pytest
from galaxy.validation import models as mapathon_validation
from galaxy.query_builder import builder as mapathon_query_builder
from galaxy import Output
import os.path

# Reference to testing.postgresql db instance
postgresql = None

# Connection to database and query running class from our galaxy module

database = None

# Generate Postgresql class which shares the generated database so that we could use it in all test function (now we don't need to create db everytime whenever the test runs)
Postgresql = testing.postgresql.PostgresqlFactory(cache_initialized_db=True)

global test_param
test_param = {
        "project_ids": [
            11224, 10042, 9906, 1381, 11203, 10681, 8055, 8732, 11193, 7305,
            11210, 10985, 10988, 11190, 6658, 5644, 10913, 6495, 4229
        ],
        "fromTimestamp":
        "2021-08-27T9:00:00",
        "toTimestamp":
        "2021-08-27T11:00:00",
        "hashtags": ["mapandchathour2021"]
    }

def slurp(path):
    """ Reads and returns the entire contents of a file """
    with open(path, 'r') as f:
        return f.read()

def setup_module(module):
    """ Module level set-up called once before any tests in this file are
    executed.  shares a temporary database created in Postgresql and sets it up """

    print('*****SETUP*****')
    global postgresql, database, con, cur , db_dict

    postgresql = Postgresql()
    # passing test credentials to our osm_stat database class for connection
    """ Default credentials : {'port': **dynamic everytime **, 'host': '127.0.0.1', 'user': 'postgres', 'database': 'test'}"""
    db_dict=postgresql.dsn()
    database = app.Database(db_dict)
    # To Ensure the database is in a known state before calling the function we're testing
    con, cur = database.connect()
    # Map of database connection parameters passed to the app we're testing
    print(postgresql.dsn())


def teardown_module(module):
    """ Called after all of the tests in this file have been executed to close
    the database connection and destroy the temporary database """

    print('******TEARDOWN******')
    # close our database connection to avoid memory leaks i.e. available feature in our database class
    database.close_conn()
    # clear cached database at end of tests
    Postgresql.clear_cache()
    if os.path.isfile(filepath) is True:
        os.remove(filepath)



def test_db_create():
    createtable = f""" CREATE TABLE test_table (id int, value varchar(256))"""
    print(database.executequery(createtable))


def test_db_insert():
    insertvalue = f""" INSERT INTO test_table values(1, 'hello'), (2, 'namaste')"""
    print(database.executequery(insertvalue))

def test_populate_data():
    database.executequery(slurp('tests/src/fixtures/mapathon_summary.sql'))


def test_mapathon_osm_history_mapathon_query_builder():
    default_osm_history_query = '\n    WITH T1 AS(\n    SELECT user_id, id as changeset_id, user_name as username\n    FROM osm_changeset\n    WHERE "created_at" between \'2021-08-27T09:00:00\'::timestamp AND \'2021-08-27T11:00:00\'::timestamp AND (("tags" -> \'hashtags\') ~~ \'%hotosm-project-11224 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10042 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-9906 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-1381 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11203 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10681 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-8055 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-8732 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11193 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-7305 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11210 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10985 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10988 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11190 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-6658 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-5644 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10913 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-6495 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-4229 %\' OR ("tags" -> \'hashtags\') ~~ \'%mapandchathour2021 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11224;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10042;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-9906;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-1381;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11203;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10681;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-8055;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-8732;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11193;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-7305;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11210;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10985;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10988;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11190;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-6658;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-5644;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10913;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-6495;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-4229;%\' OR ("tags" -> \'comment\') ~~ \'%mapandchathour2021;%\')\n    )\n    SELECT (each(tags)).key AS feature, action, count(distinct id) AS count FROM osm_element_history AS t2, t1\n    WHERE t1.changeset_id = t2.changeset\n    GROUP BY feature, action ORDER BY count DESC\n    '
    params = mapathon_validation.MapathonRequestParams(**test_param)
    changeset_query, hashtag_filter, timestamp_filter = mapathon_query_builder.create_changeset_query(
        params, con, cur)
    result_osm_history_query = mapathon_query_builder.create_osm_history_query(
        changeset_query, with_username=False)
    print(result_osm_history_query)
    assert result_osm_history_query == default_osm_history_query


def test_mapathon_total_contributor_mapathon_query_builder():
    default_total_contributor_query = '\n                SELECT COUNT(distinct user_id) as contributors_count\n                FROM osm_changeset\n                WHERE "created_at" between \'2021-08-27T09:00:00\'::timestamp AND \'2021-08-27T11:00:00\'::timestamp AND (("tags" -> \'hashtags\') ~~ \'%hotosm-project-11224 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10042 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-9906 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-1381 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11203 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10681 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-8055 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-8732 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11193 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-7305 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11210 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10985 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10988 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11190 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-6658 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-5644 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10913 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-6495 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-4229 %\' OR ("tags" -> \'hashtags\') ~~ \'%mapandchathour2021 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11224;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10042;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-9906;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-1381;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11203;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10681;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-8055;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-8732;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11193;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-7305;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11210;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10985;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10988;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11190;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-6658;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-5644;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10913;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-6495;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-4229;%\' OR ("tags" -> \'comment\') ~~ \'%mapandchathour2021;%\')\n            '
    params = mapathon_validation.MapathonRequestParams(**test_param)
    changeset_query, hashtag_filter, timestamp_filter = mapathon_query_builder.create_changeset_query(
        params, con, cur)
    result_total_contributor_query = f"""
                SELECT COUNT(distinct user_id) as contributors_count
                FROM osm_changeset
                WHERE {timestamp_filter} AND ({hashtag_filter})
            """
    print(result_total_contributor_query)
    
    assert result_total_contributor_query == default_total_contributor_query

def test_mapathon_users_contributors_mapathon_query_builder():
    default_users_contributors_query = '\n    WITH T1 AS(\n    SELECT user_id, id as changeset_id, user_name as username\n    FROM osm_changeset\n    WHERE "created_at" between \'2021-08-27T09:00:00\'::timestamp AND \'2021-08-27T11:00:00\'::timestamp AND (("tags" -> \'hashtags\') ~~ \'%hotosm-project-11224 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10042 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-9906 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-1381 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11203 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10681 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-8055 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-8732 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11193 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-7305 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11210 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10985 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10988 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11190 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-6658 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-5644 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10913 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-6495 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-4229 %\' OR ("tags" -> \'hashtags\') ~~ \'%mapandchathour2021 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11224;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10042;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-9906;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-1381;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11203;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10681;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-8055;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-8732;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11193;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-7305;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11210;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10985;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10988;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11190;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-6658;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-5644;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10913;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-6495;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-4229;%\' OR ("tags" -> \'comment\') ~~ \'%mapandchathour2021;%\')\n    ),\n    T2 AS (\n        SELECT (each(tags)).key AS feature,\n            user_id,\n            username,\n            count(distinct id) AS count\n        FROM osm_element_history AS t2, t1\n        WHERE t1.changeset_id    = t2.changeset\n        GROUP BY feature, user_id, username\n    ),\n    T3 AS (\n        SELECT user_id,\n            username,\n            SUM(count) AS total_buildings\n        FROM T2\n        WHERE feature = \'building\'\n        GROUP BY user_id, username\n    )\n    SELECT user_id,\n        username,\n        total_buildings,\n        public.tasks_per_user(user_id,\n            \'11224,10042,9906,1381,11203,10681,8055,8732,11193,7305,11210,10985,10988,11190,6658,5644,10913,6495,4229\',\n            \'2021-08-27T09:00:00\',\n            \'2021-08-27T11:00:00\',\n            \'MAPPED\') AS mapped_tasks,\n        public.tasks_per_user(user_id,\n            \'11224,10042,9906,1381,11203,10681,8055,8732,11193,7305,11210,10985,10988,11190,6658,5644,10913,6495,4229\',\n            \'2021-08-27T09:00:00\',\n            \'2021-08-27T11:00:00\',\n            \'VALIDATED\') AS validated_tasks,\n        public.editors_per_user(user_id,\n            \'2021-08-27T09:00:00\',\n            \'2021-08-27T11:00:00\') AS editors\n    FROM T3;\n    '
    params = mapathon_validation.MapathonRequestParams(**test_param)
    changeset_query, _, _ = mapathon_query_builder.create_changeset_query(params, con,
                                                       cur)
    result_users_contributors_query = mapathon_query_builder.create_users_contributions_query(
            params, changeset_query)
    print(result_users_contributors_query)
    assert result_users_contributors_query == default_users_contributors_query


def test_mapathon_summary():
    global summary_query
    summary_query = f""" WITH T1 AS(
    SELECT user_id, id as changeset_id, user_name as username
    FROM osm_changeset
    WHERE "created_at" between '2021-08-27T09:00:00'::timestamp AND '2021-08-27T11:00:00'::timestamp AND (("tags" -> 'hashtags') ~~ '%hotosm-project-11224 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-10042 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-9906 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-1381 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-11203 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-10681 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-8055 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-8732 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-11193 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-7305 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-11210 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-10985 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-10988 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-11190 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-6658 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-5644 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-10913 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-6495 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-4229 %' OR ("tags" -> 'hashtags') ~~ '%mapandchathour2021 %' OR ("tags" -> 'comment') ~~ '%hotosm-project-11224;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-10042;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-9906;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-1381;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-11203;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-10681;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-8055;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-8732;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-11193;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-7305;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-11210;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-10985;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-10988;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-11190;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-6658;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-5644;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-10913;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-6495;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-4229;%' OR ("tags" -> 'comment') ~~ '%mapandchathour2021;%')
    )
    SELECT (each(tags)).key AS feature, action, count(distinct id) AS count FROM osm_element_history AS t2, t1
    WHERE t1.changeset_id = t2.changeset
    GROUP BY feature, action ORDER BY count DESC;"""
    result = database.executequery(summary_query)
    expected_report=[['building', 'create', 78], ['highway', 'modify', 6], ['natural', 'create', 5], ['water', 'create', 4], ['highway', 'create', 4], ['name:en', 'modify', 1], ['name:ne', 'modify', 1], ['name', 'modify', 1], ['ref', 'modify', 1], ['source', 'modify', 1], ['int_ref', 'modify', 1]]
    assert result == expected_report

def test_output_JSON():
    """Function to test to_json functionality of Output Class """
    exp_result='[{"feature":"building","action":"create","count":78},{"feature":"highway","action":"modify","count":6},{"feature":"natural","action":"create","count":5},{"feature":"water","action":"create","count":4},{"feature":"highway","action":"create","count":4},{"feature":"name:en","action":"modify","count":1},{"feature":"name:ne","action":"modify","count":1},{"feature":"name","action":"modify","count":1},{"feature":"ref","action":"modify","count":1},{"feature":"source","action":"modify","count":1},{"feature":"int_ref","action":"modify","count":1}]'
    jsonresult= Output(summary_query,con).to_JSON()
    print(jsonresult)
    assert jsonresult == exp_result

def test_output_CSV():
    """Function to test to_CSV functionality of Output Class """
    global filepath
    filepath='tests/src/fixtures/csv_output.csv'
    csv_out=Output(summary_query,con).to_CSV(filepath)
    print(csv_out)
    assert os.path.isfile(filepath) == True

