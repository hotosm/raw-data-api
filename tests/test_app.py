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

from src.query_builder.builder import raw_currentdata_extraction_query
from src.validation.models import RawDataCurrentParams


def test_rawdata_current_snapshot_geometry_query():
    """
    Test the raw data current snapshot query on a Polygon geometry with specific
    filters for tags and attributes, using ST_Intersects as the geometry
    comparison method.

    This test covers a specific scenario with a handcrafted query result.
    """
    test_param = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [84.92431640625, 27.766190642387496],
                    [85.31982421875, 27.766190642387496],
                    [85.31982421875, 28.02592458049937],
                    [84.92431640625, 28.02592458049937],
                    [84.92431640625, 27.766190642387496],
                ]
            ],
        },
        "outputType": "geojson",
        "useStWithin": False,
        "filters": {
            "tags": {"point": {"join_or": {"amenity": ["shop", "toilet"]}}},
            "attributes": {"point": ["name"]},
        },
    }
    validated_params = RawDataCurrentParams(**test_param)
    expected_query = """select ST_AsGeoJSON(t0.*) from (select
                    osm_id , tableoid::regclass AS osm_type , tags ->> 'name' as name , geom
                    from
                        nodes
                    where
                        ST_intersects(geom,(select ST_Union(ST_makeValid(ST_GEOMFROMGEOJSON('{"type": "Polygon", "coordinates": [[[84.92431640625, 27.766190642387496], [85.31982421875, 27.766190642387496], [85.31982421875, 28.02592458049937], [84.92431640625, 28.02592458049937], [84.92431640625, 27.766190642387496]]]}'))))) and (tags ->>  'amenity' IN ( 'shop' ,  'toilet' ))) t0 UNION ALL select ST_AsGeoJSON(t1.*) from (select
            osm_id, tableoid::regclass AS osm_type, version,tags,changeset,timestamp,geom
            from
                ways_line
            where
                ST_intersects(geom,(select ST_Union(ST_makeValid(ST_GEOMFROMGEOJSON('{"type": "Polygon", "coordinates": [[[84.92431640625, 27.766190642387496], [85.31982421875, 27.766190642387496], [85.31982421875, 28.02592458049937], [84.92431640625, 28.02592458049937], [84.92431640625, 27.766190642387496]]]}')))))) t1 UNION ALL select ST_AsGeoJSON(t2.*) from (select
            osm_id, tableoid::regclass AS osm_type, version,tags,changeset,timestamp,geom
            from
                ways_poly
            where
                ST_intersects(geom,(select ST_Union(ST_makeValid(ST_GEOMFROMGEOJSON('{"type": "Polygon", "coordinates": [[[84.92431640625, 27.766190642387496], [85.31982421875, 27.766190642387496], [85.31982421875, 28.02592458049937], [84.92431640625, 28.02592458049937], [84.92431640625, 27.766190642387496]]]}')))))) t2 UNION ALL select ST_AsGeoJSON(t3.*) from (select
            osm_id, tableoid::regclass AS osm_type, version,tags,changeset,timestamp,geom
            from
                relations
            where
                ST_intersects(geom,(select ST_Union(ST_makeValid(ST_GEOMFROMGEOJSON('{"type": "Polygon", "coordinates": [[[84.92431640625, 27.766190642387496], [85.31982421875, 27.766190642387496], [85.31982421875, 28.02592458049937], [84.92431640625, 28.02592458049937], [84.92431640625, 27.766190642387496]]]}')))))) t3"""

    query_result = raw_currentdata_extraction_query(
        validated_params,
    )
    assert query_result.encode("utf-8") == expected_query.encode("utf-8")


def test_rawdata_current_snapshot_normal_query():
    """
    Test the raw data current snapshot query on a Polygon geometry without
    specific filters for tags and attributes, using ST_Intersects as the
    geometry comparison method.

    This test covers a basic scenario with a handcrafted query result.
    """
    test_param = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [84.92431640625, 27.766190642387496],
                    [85.31982421875, 27.766190642387496],
                    [85.31982421875, 28.02592458049937],
                    [84.92431640625, 28.02592458049937],
                    [84.92431640625, 27.766190642387496],
                ]
            ],
        },
        "useStWithin": False,
        "outputType": "geojson",
    }
    validated_params = RawDataCurrentParams(**test_param)
    expected_query = """select ST_AsGeoJSON(t0.*) from (select
                    osm_id, tableoid::regclass AS osm_type, version,tags,changeset,timestamp,geom
                    from
                        nodes
                    where
                        ST_intersects(geom,(select ST_Union(ST_makeValid(ST_GEOMFROMGEOJSON('{"type": "Polygon", "coordinates": [[[84.92431640625, 27.766190642387496], [85.31982421875, 27.766190642387496], [85.31982421875, 28.02592458049937], [84.92431640625, 28.02592458049937], [84.92431640625, 27.766190642387496]]]}')))))) t0 UNION ALL select ST_AsGeoJSON(t1.*) from (select
            osm_id, tableoid::regclass AS osm_type, version,tags,changeset,timestamp,geom
            from
                ways_line
            where
                ST_intersects(geom,(select ST_Union(ST_makeValid(ST_GEOMFROMGEOJSON('{"type": "Polygon", "coordinates": [[[84.92431640625, 27.766190642387496], [85.31982421875, 27.766190642387496], [85.31982421875, 28.02592458049937], [84.92431640625, 28.02592458049937], [84.92431640625, 27.766190642387496]]]}')))))) t1 UNION ALL select ST_AsGeoJSON(t2.*) from (select
            osm_id, tableoid::regclass AS osm_type, version,tags,changeset,timestamp,geom
            from
                ways_poly
            where
                ST_intersects(geom,(select ST_Union(ST_makeValid(ST_GEOMFROMGEOJSON('{"type": "Polygon", "coordinates": [[[84.92431640625, 27.766190642387496], [85.31982421875, 27.766190642387496], [85.31982421875, 28.02592458049937], [84.92431640625, 28.02592458049937], [84.92431640625, 27.766190642387496]]]}')))))) t2 UNION ALL select ST_AsGeoJSON(t3.*) from (select
            osm_id, tableoid::regclass AS osm_type, version,tags,changeset,timestamp,geom
            from
                relations
            where
                ST_intersects(geom,(select ST_Union(ST_makeValid(ST_GEOMFROMGEOJSON('{"type": "Polygon", "coordinates": [[[84.92431640625, 27.766190642387496], [85.31982421875, 27.766190642387496], [85.31982421875, 28.02592458049937], [84.92431640625, 28.02592458049937], [84.92431640625, 27.766190642387496]]]}')))))) t3"""
    query_result = raw_currentdata_extraction_query(
        validated_params,
    )
    assert query_result.encode("utf-8") == expected_query.encode("utf-8")


def test_rawdata_current_snapshot_normal_query_ST_within():
    """
    Test the raw data current snapshot query on a Polygon geometry without
    specific filters for tags and attributes, using ST_Within as the
    geometry comparison method.

    This test covers a scenario similar to the other normal query tests with
    ST_Within instead of ST_Intersects.
    """
    test_param = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [84.92431640625, 27.766190642387496],
                    [85.31982421875, 27.766190642387496],
                    [85.31982421875, 28.02592458049937],
                    [84.92431640625, 28.02592458049937],
                    [84.92431640625, 27.766190642387496],
                ]
            ],
        },
        "outputType": "geojson",
    }
    validated_params = RawDataCurrentParams(**test_param)
    expected_query = """select ST_AsGeoJSON(t0.*) from (select
                    osm_id, tableoid::regclass AS osm_type, version,tags,changeset,timestamp,geom
                    from
                        nodes
                    where
                        ST_within(geom,(select ST_Union(ST_makeValid(ST_GEOMFROMGEOJSON('{"type": "Polygon", "coordinates": [[[84.92431640625, 27.766190642387496], [85.31982421875, 27.766190642387496], [85.31982421875, 28.02592458049937], [84.92431640625, 28.02592458049937], [84.92431640625, 27.766190642387496]]]}')))))) t0 UNION ALL select ST_AsGeoJSON(t1.*) from (select
            osm_id, tableoid::regclass AS osm_type, version,tags,changeset,timestamp,geom
            from
                ways_line
            where
                ST_within(geom,(select ST_Union(ST_makeValid(ST_GEOMFROMGEOJSON('{"type": "Polygon", "coordinates": [[[84.92431640625, 27.766190642387496], [85.31982421875, 27.766190642387496], [85.31982421875, 28.02592458049937], [84.92431640625, 28.02592458049937], [84.92431640625, 27.766190642387496]]]}')))))) t1 UNION ALL select ST_AsGeoJSON(t2.*) from (select
            osm_id, tableoid::regclass AS osm_type, version,tags,changeset,timestamp,geom
            from
                ways_poly
            where
                ST_within(geom,(select ST_Union(ST_makeValid(ST_GEOMFROMGEOJSON('{"type": "Polygon", "coordinates": [[[84.92431640625, 27.766190642387496], [85.31982421875, 27.766190642387496], [85.31982421875, 28.02592458049937], [84.92431640625, 28.02592458049937], [84.92431640625, 27.766190642387496]]]}')))))) t2 UNION ALL select ST_AsGeoJSON(t3.*) from (select
            osm_id, tableoid::regclass AS osm_type, version,tags,changeset,timestamp,geom
            from
                relations
            where
                ST_within(geom,(select ST_Union(ST_makeValid(ST_GEOMFROMGEOJSON('{"type": "Polygon", "coordinates": [[[84.92431640625, 27.766190642387496], [85.31982421875, 27.766190642387496], [85.31982421875, 28.02592458049937], [84.92431640625, 28.02592458049937], [84.92431640625, 27.766190642387496]]]}')))))) t3"""
    query_result = raw_currentdata_extraction_query(
        validated_params,
    )
    assert query_result.encode("utf-8") == expected_query.encode("utf-8")


def test_attribute_filter_rawdata():
    """
    Test the raw data current snapshot query on a Polygon geometry with
    specific attributes filter and tags filter with ST_Intersects and
    ST_Union, and using a specific grid ID list.

    This test covers a complex scenario with multiple conditions and
    a specific grid ID list.
    """
    test_param = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [83.502574, 27.569073],
                    [83.502574, 28.332758],
                    [85.556417, 28.332758],
                    [85.556417, 27.569073],
                    [83.502574, 27.569073],
                ]
            ],
        },
        "outputType": "geojson",
        "useStWithin": False,
        "geometryType": ["polygon", "line"],
        "filters": {
            "attributes": {"line": ["name"]},
            "tags": {"all_geometry": {"join_or": {"building": ["yes"]}}},
        },
    }
    validated_params = RawDataCurrentParams(**test_param)
    expected_query = """select ST_AsGeoJSON(t0.*) from (select
            osm_id , tableoid::regclass AS osm_type , tags ->> 'name' as name , geom
            from
                ways_line
            where
                ST_intersects(geom,(select ST_Union(ST_makeValid(ST_GEOMFROMGEOJSON('{"type": "Polygon", "coordinates": [[[83.502574, 27.569073], [83.502574, 28.332758], [85.556417, 28.332758], [85.556417, 27.569073], [83.502574, 27.569073]]]}'))))) and (tags ->> 'building' = 'yes')) t0 UNION ALL select ST_AsGeoJSON(t1.*) from (select
                osm_id , tableoid::regclass AS osm_type , tags ->> 'name' as name , geom
                from
                    relations
                where
                    ST_intersects(geom,(select ST_Union(ST_makeValid(ST_GEOMFROMGEOJSON('{"type": "Polygon", "coordinates": [[[83.502574, 27.569073], [83.502574, 28.332758], [85.556417, 28.332758], [85.556417, 27.569073], [83.502574, 27.569073]]]}'))))) and (tags ->> 'building' = 'yes') and (geometrytype(geom)='MULTILINESTRING')) t1 UNION ALL select ST_AsGeoJSON(t2.*) from (select
            osm_id, tableoid::regclass AS osm_type, version,tags,changeset,timestamp,geom
            from
                ways_poly
            where
                (grid = 1187 OR grid = 1188) and (ST_intersects(geom,(select ST_Union(ST_makeValid(ST_GEOMFROMGEOJSON('{"type": "Polygon", "coordinates": [[[83.502574, 27.569073], [83.502574, 28.332758], [85.556417, 28.332758], [85.556417, 27.569073], [83.502574, 27.569073]]]}')))))) and (tags ->> 'building' = 'yes')) t2 UNION ALL select ST_AsGeoJSON(t3.*) from (select
            osm_id, tableoid::regclass AS osm_type, version,tags,changeset,timestamp,geom
            from
                relations
            where
                ST_intersects(geom,(select ST_Union(ST_makeValid(ST_GEOMFROMGEOJSON('{"type": "Polygon", "coordinates": [[[83.502574, 27.569073], [83.502574, 28.332758], [85.556417, 28.332758], [85.556417, 27.569073], [83.502574, 27.569073]]]}'))))) and (tags ->> 'building' = 'yes') and (geometrytype(geom)='POLYGON' or geometrytype(geom)='MULTIPOLYGON')) t3"""
    query_result = raw_currentdata_extraction_query(
        validated_params,
        g_id=[[1187], [1188]],
    )
    assert query_result.encode("utf-8") == expected_query.encode("utf-8")


def test_and_filters():
    """
    Test the raw data current snapshot query on a Polygon geometry with
    complex conditions for tags filter using multiple join_and,
    ST_Intersects and ST_Union.

    This test covers a specific scenario with multiple join_and clauses
    for joined tags.
    """
    test_param = {
        "fileName": "Destroyed_Buildings_Turkey",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [36.70588085657477, 37.1979648807274],
                    [36.70588085657477, 37.1651408422983],
                    [36.759267544807194, 37.1651408422983],
                    [36.759267544807194, 37.1979648807274],
                    [36.70588085657477, 37.1979648807274],
                ]
            ],
        },
        "outputType": "geojson",
        "useStWithin": False,
        "geometryType": ["polygon"],
        "filters": {
            "tags": {
                "point": {},
                "line": {},
                "polygon": {
                    "join_or": {},
                    "join_and": {
                        "destroyed:building": ["yes"],
                        "damage:date": ["2023-02-06"],
                    },
                },
            },
            "attributes": {
                "point": [],
                "line": [],
                "polygon": [
                    "building",
                    "destroyed:building",
                    "damage:date",
                    "name",
                    "source",
                ],
            },
        },
    }
    validated_params = RawDataCurrentParams(**test_param)
    expected_query = """select ST_AsGeoJSON(t0.*) from (select
            osm_id , tableoid::regclass AS osm_type , tags ->> 'building' as building , tags ->> 'destroyed:building' as destroyed_building , tags ->> 'damage:date' as damage_date , tags ->> 'name' as name , tags ->> 'source' as source , geom
            from
                ways_poly
            where
                ST_intersects(geom,(select ST_Union(ST_makeValid(ST_GEOMFROMGEOJSON('{"type": "Polygon", "coordinates": [[[36.70588085657477, 37.1979648807274], [36.70588085657477, 37.1651408422983], [36.759267544807194, 37.1651408422983], [36.759267544807194, 37.1979648807274], [36.70588085657477, 37.1979648807274]]]}'))))) and (tags ->> 'destroyed:building' = 'yes' AND tags ->> 'damage:date' = '2023-02-06')) t0 UNION ALL select ST_AsGeoJSON(t1.*) from (select
            osm_id , tableoid::regclass AS osm_type , tags ->> 'building' as building , tags ->> 'destroyed:building' as destroyed_building , tags ->> 'damage:date' as damage_date , tags ->> 'name' as name , tags ->> 'source' as source , geom
            from
                relations
            where
                ST_intersects(geom,(select ST_Union(ST_makeValid(ST_GEOMFROMGEOJSON('{"type": "Polygon", "coordinates": [[[36.70588085657477, 37.1979648807274], [36.70588085657477, 37.1651408422983], [36.759267544807194, 37.1651408422983], [36.759267544807194, 37.1979648807274], [36.70588085657477, 37.1979648807274]]]}'))))) and (tags ->> 'destroyed:building' = 'yes' AND tags ->> 'damage:date' = '2023-02-06') and (geometrytype(geom)='POLYGON' or geometrytype(geom)='MULTIPOLYGON')) t1"""
    query_result = raw_currentdata_extraction_query(
        validated_params,
    )
    assert query_result.encode("utf-8") == expected_query.encode("utf-8")
