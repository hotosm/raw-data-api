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

from src.galaxy import app
import testing.postgresql
import pytest
from src.galaxy.validation import models as mapathon_validation
from src.galaxy.query_builder import builder as mapathon_query_builder
from src.galaxy.query_builder.builder import create_UserStats_get_statistics_query,create_userstats_get_statistics_with_hashtags_query,generate_data_quality_TM_query,generate_data_quality_username_query
from src.galaxy.validation.models import UserStatsParams,DataQuality_TM_RequestParams,DataQuality_username_RequestParams
from src.galaxy import Output
import os.path

# Reference to testing.postgresql db instance
postgresql = None

# Connection to database and query running class from our src.galaxy module

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
    # print(database.executequery(createtable))


def test_db_insert():
    insertvalue = f""" INSERT INTO test_table values(1, 'hello'), (2, 'namaste')"""
    # print(database.executequery(insertvalue))

def test_populate_data():
    database.executequery(slurp('tests/src/fixtures/mapathon_summary.sql'))


def test_mapathon_osm_history_mapathon_query_builder():
    default_osm_history_query = '\n    WITH T1 AS(\n    SELECT user_id, id as changeset_id, user_name as username\n    FROM osm_changeset\n    WHERE "created_at" between \'2021-08-27T09:00:00\'::timestamp AND \'2021-08-27T11:00:00\'::timestamp AND (("tags" -> \'hashtags\') ~~ \'%hotosm-project-11224;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10042;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-9906;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-1381;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11203;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10681;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-8055;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-8732;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11193;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-7305;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11210;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10985;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10988;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11190;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-6658;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-5644;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10913;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-6495;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-4229;%\' OR ("tags" -> \'hashtags\') ~~ \'%mapandchathour2021;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11224 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10042 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-9906 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-1381 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11203 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10681 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-8055 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-8732 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11193 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-7305 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11210 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10985 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10988 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11190 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-6658 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-5644 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10913 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-6495 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-4229 %\' OR ("tags" -> \'comment\') ~~ \'%mapandchathour2021 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11224\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11224\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10042\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10042\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-9906\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-9906\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-1381\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-1381\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11203\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11203\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10681\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10681\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-8055\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-8055\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-8732\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-8732\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11193\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11193\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-7305\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-7305\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11210\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11210\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10985\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10985\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10988\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10988\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11190\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11190\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-6658\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-6658\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-5644\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-5644\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10913\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10913\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-6495\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-6495\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-4229\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-4229\' OR ("tags" -> \'hashtags\') ~~ \'%mapandchathour2021\' OR ("tags" -> \'comment\') ~~ \'%mapandchathour2021\')\n    )\n    SELECT (each(tags)).key AS feature, action, count(distinct id) AS count FROM osm_element_history AS t2, t1\n    WHERE t1.changeset_id = t2.changeset\n    GROUP BY feature, action ORDER BY count DESC\n    '
    params = mapathon_validation.MapathonRequestParams(**test_param)
    changeset_query, hashtag_filter, timestamp_filter = mapathon_query_builder.create_changeset_query(
        params, con, cur)
    result_osm_history_query = mapathon_query_builder.create_osm_history_query(
        changeset_query, with_username=False)
    # print(result_osm_history_query.encode('utf-8'))
    assert result_osm_history_query == default_osm_history_query


def test_mapathon_total_contributor_mapathon_query_builder():
    default_total_contributor_query = '\n                SELECT COUNT(distinct user_id) as contributors_count\n                FROM osm_changeset\n                WHERE "created_at" between \'2021-08-27T09:00:00\'::timestamp AND \'2021-08-27T11:00:00\'::timestamp\n             AND (("tags" -> \'hashtags\') ~~ \'%hotosm-project-11224;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10042;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-9906;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-1381;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11203;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10681;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-8055;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-8732;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11193;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-7305;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11210;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10985;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10988;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11190;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-6658;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-5644;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10913;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-6495;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-4229;%\' OR ("tags" -> \'hashtags\') ~~ \'%mapandchathour2021;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11224 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10042 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-9906 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-1381 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11203 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10681 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-8055 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-8732 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11193 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-7305 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11210 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10985 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10988 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11190 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-6658 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-5644 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10913 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-6495 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-4229 %\' OR ("tags" -> \'comment\') ~~ \'%mapandchathour2021 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11224\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11224\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10042\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10042\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-9906\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-9906\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-1381\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-1381\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11203\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11203\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10681\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10681\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-8055\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-8055\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-8732\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-8732\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11193\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11193\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-7305\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-7305\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11210\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11210\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10985\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10985\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10988\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10988\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11190\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11190\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-6658\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-6658\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-5644\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-5644\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10913\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10913\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-6495\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-6495\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-4229\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-4229\' OR ("tags" -> \'hashtags\') ~~ \'%mapandchathour2021\' OR ("tags" -> \'comment\') ~~ \'%mapandchathour2021\')'
    params = mapathon_validation.MapathonRequestParams(**test_param)
    changeset_query, hashtag_filter, timestamp_filter = mapathon_query_builder.create_changeset_query(
        params, con, cur)
    result_total_contributor_query = f"""
                SELECT COUNT(distinct user_id) as contributors_count
                FROM osm_changeset
                WHERE {timestamp_filter} AND ({hashtag_filter})
            """
    # print(result_total_contributor_query.encode('utf-8'))
    # print(result_total_contributor_query.encode('utf-8'))
    
    assert result_total_contributor_query == default_total_contributor_query

def test_mapathon_users_contributors_mapathon_query_builder():
    default_users_contributors_query = '\n                SELECT COUNT(distinct user_id) as contributors_count\n                FROM osm_changeset\n                WHERE "created_at" between \'2021-08-27T09:00:00\'::timestamp AND \'2021-08-27T11:00:00\'::timestamp AND (("tags" -> \'hashtags\') ~~ \'%hotosm-project-11224;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10042;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-9906;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-1381;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11203;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10681;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-8055;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-8732;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11193;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-7305;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11210;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10985;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10988;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11190;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-6658;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-5644;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10913;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-6495;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-4229;%\' OR ("tags" -> \'hashtags\') ~~ \'%mapandchathour2021;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11224 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10042 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-9906 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-1381 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11203 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10681 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-8055 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-8732 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11193 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-7305 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11210 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10985 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10988 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11190 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-6658 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-5644 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10913 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-6495 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-4229 %\' OR ("tags" -> \'comment\') ~~ \'%mapandchathour2021 %\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11224\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11224\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10042\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10042\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-9906\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-9906\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-1381\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-1381\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11203\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11203\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10681\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10681\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-8055\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-8055\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-8732\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-8732\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11193\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11193\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-7305\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-7305\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11210\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11210\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10985\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10985\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10988\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10988\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11190\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11190\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-6658\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-6658\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-5644\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-5644\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10913\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10913\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-6495\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-6495\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-4229\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-4229\' OR ("tags" -> \'hashtags\') ~~ \'%mapandchathour2021\' OR ("tags" -> \'comment\') ~~ \'%mapandchathour2021\')\n            '
    params = mapathon_validation.MapathonRequestParams(**test_param)
    changeset_query, _, _ = mapathon_query_builder.create_changeset_query(params, con,
                                                       cur)
    result_users_contributors_query = mapathon_query_builder.create_users_contributions_query(
            params, changeset_query)
    assert result_users_contributors_query == default_users_contributors_query


def test_mapathon_summary():
    params = mapathon_validation.MapathonRequestParams(**test_param)
    changeset_query, hashtag_filter, timestamp_filter = mapathon_query_builder.create_changeset_query(
        params, con, cur)
    result_osm_history_query = mapathon_query_builder.create_osm_history_query(
        changeset_query, with_username=False)

    result = database.executequery(result_osm_history_query)
    print(result)
    expected_report=[['building', 'create', 78], ['highway', 'modify', 6], ['natural', 'create', 5], ['water', 'create', 4], ['highway', 'create', 4], ['name:en', 'modify', 1], ['name:ne', 'modify', 1], ['name', 'modify', 1], ['ref', 'modify', 1], ['source', 'modify', 1], ['int_ref', 'modify', 1]]
    assert result == expected_report

def test_output_JSON():
    """Function to test to_json functionality of Output Class """
    global summary_query
    summary_query = f""" WITH T1 AS(
    SELECT user_id, id as changeset_id, user_name as username
    FROM osm_changeset
    WHERE "created_at" between '2021-08-27T09:00:00'::timestamp AND '2021-08-27T11:00:00'::timestamp AND (("tags" -> 'hashtags') ~~ '%hotosm-project-11224 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-10042 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-9906 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-1381 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-11203 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-10681 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-8055 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-8732 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-11193 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-7305 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-11210 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-10985 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-10988 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-11190 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-6658 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-5644 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-10913 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-6495 %' OR ("tags" -> 'hashtags') ~~ '%hotosm-project-4229 %' OR ("tags" -> 'hashtags') ~~ '%mapandchathour2021 %' OR ("tags" -> 'comment') ~~ '%hotosm-project-11224;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-10042;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-9906;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-1381;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-11203;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-10681;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-8055;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-8732;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-11193;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-7305;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-11210;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-10985;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-10988;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-11190;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-6658;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-5644;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-10913;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-6495;%' OR ("tags" -> 'comment') ~~ '%hotosm-project-4229;%' OR ("tags" -> 'comment') ~~ '%mapandchathour2021;%')
    )
    SELECT (each(tags)).key AS feature, action, count(distinct id) AS count FROM osm_element_history AS t2, t1
    WHERE t1.changeset_id = t2.changeset
    GROUP BY feature, action ORDER BY count DESC;"""
    exp_result='[{"feature":"building","action":"create","count":78},{"feature":"highway","action":"modify","count":6},{"feature":"natural","action":"create","count":5},{"feature":"water","action":"create","count":4},{"feature":"highway","action":"create","count":4},{"feature":"name:en","action":"modify","count":1},{"feature":"name:ne","action":"modify","count":1},{"feature":"name","action":"modify","count":1},{"feature":"ref","action":"modify","count":1},{"feature":"source","action":"modify","count":1},{"feature":"int_ref","action":"modify","count":1}]'
    jsonresult= Output(summary_query,con).to_JSON()
    # print(jsonresult)
    assert jsonresult == exp_result

def test_output_CSV():
    """Function to test to_CSV functionality of Output Class """
    global filepath
    filepath='tests/src/fixtures/csv_output.csv'
    csv_out=Output(summary_query,con).to_CSV(filepath)
    # print(csv_out)
    assert os.path.isfile(filepath) == True

def test_data_quality_TM_query():
    """Function to test data quality TM query generator of Data Quality Class """
    data_quality_params= {
        "project_ids": [
            9928,4730,5663
        ],
        "issue_types": ["badgeom", "badvalue"],
        "Output_type": "GeoJSON"
    }
    validated_params=DataQuality_TM_RequestParams(**data_quality_params)
    expected_result="   with t1 as (\n        select id\n                From changesets \n                WHERE\n                  'hotosm-project-9928'=ANY(hashtags) OR 'hotosm-project-4730'=ANY(hashtags) OR 'hotosm-project-5663'=ANY(hashtags)\n            ),\n        t2 AS (\n             SELECT osm_id as Osm_id,\n                change_id as Changeset_id,\n                timestamp::text as Changeset_timestamp,\n                status::text as Issue_type,\n                ST_X(location::geometry) as lng,\n                ST_Y(location::geometry) as lat\n\n        FROM validation join t1 on change_id = t1.id\n        WHERE\n        'badgeom'=ANY(status) OR 'badvalue'=ANY(status)\n                )\n        select *\n        from t2\n        "
    query_result=generate_data_quality_TM_query(validated_params)
    # print(query_result.encode('utf-8'))

    assert query_result == expected_result

def test_data_quality_username_query():
    """Function to test data quality username query generator of Data Quality Class """
    data_quality_params= {
    "osm_usernames": [
        "MANUEL_PC","piticasuno","LCrawford1833"
    ],
    "issue_types": ["badgeom","badvalue"],
    "fromTimestamp": "2021-10-7T9:00:00",
    "toTimestamp": "2021-11-5T11:00:00",
    "Output_type": "GeoJSON"
}
    validated_params=DataQuality_username_RequestParams(**data_quality_params)
    expected_result="   with t1 as (\n        select id,username as username\n                From users \n                WHERE\n                  'MANUEL_PC'=username OR 'piticasuno'=username OR 'LCrawford1833'=username\n            ),\n        t2 AS (\n             SELECT osm_id as Osm_id,\n                change_id as Changeset_id,\n                timestamp::text as Changeset_timestamp,\n                status::text as Issue_type,\n                t1.username as username,\n                ST_X(location::geometry) as lng,\n                ST_Y(location::geometry) as lat\n                \n        FROM validation join t1 on user_id = t1.id  \n        WHERE\n        ('badgeom'=ANY(status) OR 'badvalue'=ANY(status)) AND (timestamp between '2021-10-07 09:00:00' and  '2021-11-05 11:00:00')\n                )\n        select *\n        from t2\n        "
    query_result=generate_data_quality_username_query(validated_params)
    # print(query_result.encode('utf-8'))
    assert query_result == expected_result

def test_userstats_get_statistics_with_hashtags_query():
    """Function to  test userstats class's get_statistics query generator """
    test_params= {
        "userId": 11593794,
        "fromTimestamp": "2021-08-27T9:00:00",
        "toTimestamp": "2021-08-27T11:00:00",
        "hashtags": [
            "mapandchathour2021"
        ],
        "projectIds": [11224, 10042, 9906, 1381, 11203, 10681, 8055, 8732, 11193, 7305, 11210,
                10985, 10988, 11190, 6658, 5644, 10913, 6495, 4229]
        }
    validated_params=UserStatsParams(**test_params)
    expected_result="""\n            WITH T1 AS (\n                \n    SELECT user_id, id as changeset_id, user_name as username\n    FROM osm_changeset\n    WHERE "created_at" between \'2021-08-27T09:00:00\'::timestamp AND \'2021-08-27T11:00:00\'::timestamp AND (("tags" -> \'hashtags\') ~~ \'%hotosm-project-11224;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10042;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-9906;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-1381;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11203;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10681;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-8055;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-8732;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11193;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-7305;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11210;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10985;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10988;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-11190;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-6658;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-5644;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-10913;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-6495;%\' OR ("tags" -> \'hashtags\') ~~ \'%hotosm-project-4229;%\' OR ("tags" -> \'hashtags\') ~~ \'%mapandchathour2021 %\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11224;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10042;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-9906;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-1381;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11203;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10681;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-8055;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-8732;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11193;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-7305;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11210;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10985;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10988;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-11190;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-6658;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-5644;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-10913;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-6495;%\' OR ("tags" -> \'comment\') ~~ \'%hotosm-project-4229;%\' OR ("tags" -> \'comment\') ~~ \'%mapandchathour2021;%\')\n     AND user_id = 11593794\n            )\n            \n            SELECT (each(osh.tags)).key as feature, osh.action, count(distinct osh.id)\n            FROM osm_element_history AS osh, T1\n            WHERE osh.timestamp BETWEEN \'2021-08-27T09:00:00\'::timestamp AND \'2021-08-27T11:00:00\'::timestamp\n            AND osh.uid = 11593794\n            AND osh.type in (\'way\',\'relation\')\n            AND T1.changeset_id = osh.changeset\n            GROUP BY feature, action\n        \n        """
    query_result=create_userstats_get_statistics_with_hashtags_query(validated_params,con,cur)
    # print(query_result.encode('utf-8'))
    assert query_result == expected_result

def test_userstats_get_statistics_query():
    """Function to  test userstats class's get_statistics query generator """
    test_params= {
        "userId": 11593794,
        "fromTimestamp": "2021-08-27T9:00:00",
        "toTimestamp": "2021-08-27T11:00:00",
        "hashtags": [
        ],
        "projectIds": [11224, 10042, 9906, 1381, 11203, 10681, 8055, 8732, 11193, 7305, 11210,
                10985, 10988, 11190, 6658, 5644, 10913, 6495, 4229]
        }
    validated_params=UserStatsParams(**test_params)
    expected_result="""\n            SELECT (each(tags)).key as feature, action, count(distinct id)\n            FROM osm_element_history\n            WHERE timestamp BETWEEN '2021-08-27T09:00:00'::timestamp AND '2021-08-27T11:00:00'::timestamp\n            AND uid = 11593794\n            AND type in ('way','relation')\n            GROUP BY feature, action\n        """
    query_result=create_UserStats_get_statistics_query(validated_params,con,cur)
    # print(query_result)
    assert query_result == expected_result.encode('utf-8')