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
from src.galaxy.query_builder.builder import raw_currentdata_extraction_query
from src.galaxy.validation.models import RawDataCurrentParams
import os.path
from json import dumps

# Reference to testing.postgresql db instance
postgresql = None

# Connection to database and query running class from our src.galaxy module

database = None
filepath = None

# Generate Postgresql class which shares the generated database so that we could use it in all test function (now we don't need to create db everytime whenever the test runs)
Postgresql = testing.postgresql.PostgresqlFactory(cache_initialized_db=True)


def slurp(path):
    """ Reads and returns the entire contents of a file """
    with open(path, 'r') as f:
        return f.read()


def setup_module(module):
    """ Module level set-up called once before any tests in this file are
    executed.  shares a temporary database created in Postgresql and sets it up """

    print('*****SETUP*****')
    global postgresql, database, con, cur, db_dict

    postgresql = Postgresql()
    # passing test credentials to our osm_stat database class for connection
    """ Default credentials : {'port': **dynamic everytime **, 'host': '127.0.0.1', 'user': 'postgres', 'database': 'test'}"""
    db_dict = postgresql.dsn()
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
    if filepath:
        if os.path.isfile(filepath) is True:
            os.remove(filepath)


# def test_populate_data():
#     database.executequery(slurp('tests/src/fixtures/mapathon_summary.sql'))


def test_rawdata_current_snapshot_geometry_query():

    test_param = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [
                        84.92431640625,
                        27.766190642387496
                    ],
                    [
                        85.31982421875,
                        27.766190642387496
                    ],
                    [
                        85.31982421875,
                        28.02592458049937
                    ],
                    [
                        84.92431640625,
                        28.02592458049937
                    ],
                    [
                        84.92431640625,
                        27.766190642387496
                    ]
                ]
            ]
        },
        "outputType": "GeoJSON",
        "filters": {"tags": {"point": {"amenity": ["shop", "toilet"]}}, "attributes": {"point": ["name"]}}
    }
    validated_params = RawDataCurrentParams(**test_param)
    expected_query = """select ST_AsGeoJSON(t0.*) from (select
                    osm_id , tags ->> 'name' as name , geom
                    from
                        nodes
                    where
                        ST_intersects(ST_GEOMFROMGEOJSON('{"coordinates": [[[84.92431640625, 27.766190642387496], [85.31982421875, 27.766190642387496], [85.31982421875, 28.02592458049937], [84.92431640625, 28.02592458049937], [84.92431640625, 27.766190642387496]]], "type": "Polygon"}'), geom) and (tags ->>  'amenity' IN ( 'shop'  ,  'toilet' ))) t0 UNION ALL select ST_AsGeoJSON(t1.*) from (select
            osm_id ,version,tags::text as tags,changeset,timestamp::text,geom
            from
                ways_line
            where
                ST_intersects(ST_GEOMFROMGEOJSON('{"coordinates": [[[84.92431640625, 27.766190642387496], [85.31982421875, 27.766190642387496], [85.31982421875, 28.02592458049937], [84.92431640625, 28.02592458049937], [84.92431640625, 27.766190642387496]]], "type": "Polygon"}'), geom)) t1 UNION ALL select ST_AsGeoJSON(t2.*) from (select
            osm_id ,version,tags::text as tags,changeset,timestamp::text,geom
            from
                ways_poly
            where
                ST_intersects(ST_GEOMFROMGEOJSON('{"coordinates": [[[84.92431640625, 27.766190642387496], [85.31982421875, 27.766190642387496], [85.31982421875, 28.02592458049937], [84.92431640625, 28.02592458049937], [84.92431640625, 27.766190642387496]]], "type": "Polygon"}'), geom)) t2 UNION ALL select ST_AsGeoJSON(t3.*) from (select
            osm_id ,version,tags::text as tags,changeset,timestamp::text,geom
            from
                relations
            where
                ST_intersects(ST_GEOMFROMGEOJSON('{"coordinates": [[[84.92431640625, 27.766190642387496], [85.31982421875, 27.766190642387496], [85.31982421875, 28.02592458049937], [84.92431640625, 28.02592458049937], [84.92431640625, 27.766190642387496]]], "type": "Polygon"}'), geom)) t3"""
    query_result = raw_currentdata_extraction_query(
        validated_params, None, dumps(dict(validated_params.geometry)))
    assert query_result.encode('utf-8') == expected_query.encode('utf-8')


def test_rawdata_current_snapshot_normal_query():
    test_param = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [
                        84.92431640625,
                        27.766190642387496
                    ],
                    [
                        85.31982421875,
                        27.766190642387496
                    ],
                    [
                        85.31982421875,
                        28.02592458049937
                    ],
                    [
                        84.92431640625,
                        28.02592458049937
                    ],
                    [
                        84.92431640625,
                        27.766190642387496
                    ]
                ]
            ]
        },
        "outputType": "GeoJSON"
    }
    validated_params = RawDataCurrentParams(**test_param)
    expected_query = """select ST_AsGeoJSON(t0.*) from (select
                    osm_id ,version,tags::text as tags,changeset,timestamp::text,geom
                    from
                        nodes
                    where
                        ST_intersects(ST_GEOMFROMGEOJSON('{"coordinates": [[[84.92431640625, 27.766190642387496], [85.31982421875, 27.766190642387496], [85.31982421875, 28.02592458049937], [84.92431640625, 28.02592458049937], [84.92431640625, 27.766190642387496]]], "type": "Polygon"}'), geom)) t0 UNION ALL select ST_AsGeoJSON(t1.*) from (select
            osm_id ,version,tags::text as tags,changeset,timestamp::text,geom
            from
                ways_line
            where
                ST_intersects(ST_GEOMFROMGEOJSON('{"coordinates": [[[84.92431640625, 27.766190642387496], [85.31982421875, 27.766190642387496], [85.31982421875, 28.02592458049937], [84.92431640625, 28.02592458049937], [84.92431640625, 27.766190642387496]]], "type": "Polygon"}'), geom)) t1 UNION ALL select ST_AsGeoJSON(t2.*) from (select
            osm_id ,version,tags::text as tags,changeset,timestamp::text,geom
            from
                ways_poly
            where
                ST_intersects(ST_GEOMFROMGEOJSON('{"coordinates": [[[84.92431640625, 27.766190642387496], [85.31982421875, 27.766190642387496], [85.31982421875, 28.02592458049937], [84.92431640625, 28.02592458049937], [84.92431640625, 27.766190642387496]]], "type": "Polygon"}'), geom)) t2 UNION ALL select ST_AsGeoJSON(t3.*) from (select
            osm_id ,version,tags::text as tags,changeset,timestamp::text,geom
            from
                relations
            where
                ST_intersects(ST_GEOMFROMGEOJSON('{"coordinates": [[[84.92431640625, 27.766190642387496], [85.31982421875, 27.766190642387496], [85.31982421875, 28.02592458049937], [84.92431640625, 28.02592458049937], [84.92431640625, 27.766190642387496]]], "type": "Polygon"}'), geom)) t3"""
    query_result = raw_currentdata_extraction_query(
        validated_params, None, dumps(dict(validated_params.geometry)))
    assert query_result.encode('utf-8') == expected_query.encode('utf-8')


def test_attribute_filter_rawdata():
    test_param = {"geometry": {"type": "Polygon", "coordinates": [[[83.502574, 27.569073], [83.502574, 28.332758], [85.556417, 28.332758], [85.556417, 27.569073], [
        83.502574, 27.569073]]]}, "outputType": "GeoJSON", "geometryType": ["polygon", "line"], "filters": {"attributes": {"line": ["name"]}, "tags": {"all_geometry": {"building": ["yes"]}}}}
    validated_params = RawDataCurrentParams(**test_param)
    expected_query = """select ST_AsGeoJSON(t0.*) from (select
            osm_id , tags ->> 'name' as name , geom
            from
                ways_line
            where
                ST_intersects(ST_GEOMFROMGEOJSON('{"coordinates": [[[83.502574, 27.569073], [83.502574, 28.332758], [85.556417, 28.332758], [85.556417, 27.569073], [83.502574, 27.569073]]], "type": "Polygon"}'), geom) and (tags ->> 'building' = 'yes')) t0 UNION ALL select ST_AsGeoJSON(t1.*) from (select
                osm_id , tags ->> 'name' as name , geom
                from
                    relations
                where
                    ST_intersects(ST_GEOMFROMGEOJSON('{"coordinates": [[[83.502574, 27.569073], [83.502574, 28.332758], [85.556417, 28.332758], [85.556417, 27.569073], [83.502574, 27.569073]]], "type": "Polygon"}'), geom) and (tags ->> 'building' = 'yes') and (geometrytype(geom)='MULTILINESTRING')) t1 UNION ALL select ST_AsGeoJSON(t2.*) from (select
            osm_id ,version,tags::text as tags,changeset,timestamp::text,geom
            from
                ways_poly
            where
                (grid = 1187 OR grid = 1188) and ST_intersects(ST_GEOMFROMGEOJSON('{"coordinates": [[[83.502574, 27.569073], [83.502574, 28.332758], [85.556417, 28.332758], [85.556417, 27.569073], [83.502574, 27.569073]]], "type": "Polygon"}'), geom) and (tags ->> 'building' = 'yes')) t2 UNION ALL select ST_AsGeoJSON(t3.*) from (select
            osm_id ,version,tags::text as tags,changeset,timestamp::text,geom
            from
                relations
            where
                ST_intersects(ST_GEOMFROMGEOJSON('{"coordinates": [[[83.502574, 27.569073], [83.502574, 28.332758], [85.556417, 28.332758], [85.556417, 27.569073], [83.502574, 27.569073]]], "type": "Polygon"}'), geom) and (tags ->> 'building' = 'yes') and (geometrytype(geom)='POLYGON' or geometrytype(geom)='MULTIPOLYGON')) t3"""
    query_result = raw_currentdata_extraction_query(
        validated_params, [[1187], [1188]], dumps(dict(validated_params.geometry)))
    assert query_result.encode('utf-8') == expected_query.encode('utf-8')
