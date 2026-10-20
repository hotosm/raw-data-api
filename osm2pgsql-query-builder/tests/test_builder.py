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

import pytest
from geojson_pydantic import Feature, Polygon
from pydantic import ValidationError

from osm2pgsql_query_builder import (
    CategoryBase,
    Filters,
    SnapshotQueryParams,
    build_snapshot_query,
)
from osm2pgsql_query_builder.models import (
    AttributeFilter,
    GeometryValidatorMixin,
    SQLFilter,
    TagsFilter,
)

# Use SnapshotQueryParams directly as the test params model
QueryParams = SnapshotQueryParams


def test_snapshot_geometry_query():
    params = QueryParams(
        geometry=Polygon(
            type="Polygon",
            coordinates=[
                [
                    [84.92431640625, 27.766190642387496],
                    [85.31982421875, 27.766190642387496],
                    [85.31982421875, 28.02592458049937],
                    [84.92431640625, 28.02592458049937],
                    [84.92431640625, 27.766190642387496],
                ]
            ],
        ),
        output_type="geojson",
        use_st_within=False,
        filters=Filters(
            tags={"point": {"join_or": {"amenity": ["shop", "toilet"]}}},
            attributes={"point": ["name"]},
        ),
    )
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

    query_result = build_snapshot_query(params)
    assert query_result.encode("utf-8") == expected_query.encode("utf-8")


def test_snapshot_normal_query():
    params = QueryParams(
        geometry=Polygon(
            type="Polygon",
            coordinates=[
                [
                    [84.92431640625, 27.766190642387496],
                    [85.31982421875, 27.766190642387496],
                    [85.31982421875, 28.02592458049937],
                    [84.92431640625, 28.02592458049937],
                    [84.92431640625, 27.766190642387496],
                ]
            ],
        ),
        use_st_within=False,
        output_type="geojson",
    )
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
    query_result = build_snapshot_query(params)
    assert query_result.encode("utf-8") == expected_query.encode("utf-8")


def test_snapshot_query_st_within():
    params = QueryParams(
        geometry=Polygon(
            type="Polygon",
            coordinates=[
                [
                    [84.92431640625, 27.766190642387496],
                    [85.31982421875, 27.766190642387496],
                    [85.31982421875, 28.02592458049937],
                    [84.92431640625, 28.02592458049937],
                    [84.92431640625, 27.766190642387496],
                ]
            ],
        ),
        output_type="geojson",
    )
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
    query_result = build_snapshot_query(params)
    assert query_result.encode("utf-8") == expected_query.encode("utf-8")


def test_attribute_filter():
    params = QueryParams(
        geometry=Polygon(
            type="Polygon",
            coordinates=[
                [
                    [83.502574, 27.569073],
                    [83.502574, 28.332758],
                    [85.556417, 28.332758],
                    [85.556417, 27.569073],
                    [83.502574, 27.569073],
                ]
            ],
        ),
        output_type="geojson",
        use_st_within=False,
        geometry_type=["polygon", "line"],
        filters=Filters(
            tags={"all_geometry": {"join_or": {"building": ["yes"]}}},
            attributes={"line": ["name"]},
        ),
    )
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
    query_result = build_snapshot_query(
        params,
        g_id=[[1187], [1188]],
    )
    assert query_result.encode("utf-8") == expected_query.encode("utf-8")


def test_and_filters():
    params = QueryParams(
        geometry=Polygon(
            type="Polygon",
            coordinates=[
                [
                    [36.70588085657477, 37.1979648807274],
                    [36.70588085657477, 37.1651408422983],
                    [36.759267544807194, 37.1651408422983],
                    [36.759267544807194, 37.1979648807274],
                    [36.70588085657477, 37.1979648807274],
                ]
            ],
        ),
        output_type="geojson",
        use_st_within=False,
        geometry_type=["polygon"],
        filters=Filters(
            tags={
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
            attributes={
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
        ),
    )
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
    query_result = build_snapshot_query(params)
    assert query_result.encode("utf-8") == expected_query.encode("utf-8")


def test_convert_tags_to_postgres():
    from osm2pgsql_query_builder import convert_tags_to_postgres

    assert (
        convert_tags_to_postgres("tags['building'] = 'yes'")
        == "tags->>'building' = 'yes'"
    )


def test_sanitize_filename():
    from osm2pgsql_query_builder import sanitize_filename

    assert sanitize_filename("my file-name:test") == "my_file_name_test"


def test_sanitize_column_name():
    from osm2pgsql_query_builder import sanitize_column_name

    assert sanitize_column_name("my tag:name") == "my_tag_name"


# --- Model tests ---


def test_snapshot_query_params_basic():
    params = SnapshotQueryParams(
        geometry=Polygon(
            type="Polygon",
            coordinates=[
                [
                    [84.0, 27.0],
                    [85.0, 27.0],
                    [85.0, 28.0],
                    [84.0, 28.0],
                    [84.0, 27.0],
                ]
            ],
        ),
    )
    assert params.output_type == "geojson"
    assert params.use_st_within is True
    assert params.centroid is False
    assert params.filters is None


def test_snapshot_query_params_with_filters():
    params = SnapshotQueryParams(
        geometry=Polygon(
            type="Polygon",
            coordinates=[
                [
                    [84.0, 27.0],
                    [85.0, 27.0],
                    [85.0, 28.0],
                    [84.0, 28.0],
                    [84.0, 27.0],
                ]
            ],
        ),
        filters={
            "tags": {"all_geometry": {"join_or": {"building": []}}},
            "attributes": {"all_geometry": ["name"]},
        },
    )
    assert params.filters is not None
    assert params.filters.tags.all_geometry.join_or == {"building": []}
    assert params.filters.attributes.all_geometry == ["name"]


def test_snapshot_query_params_geometry_from_feature():
    params = SnapshotQueryParams(
        geometry={
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [84.0, 27.0],
                        [85.0, 27.0],
                        [85.0, 28.0],
                        [84.0, 28.0],
                        [84.0, 27.0],
                    ]
                ],
            },
        },
    )
    # GeometryValidatorMixin extracts geometry from Feature
    assert params.geometry.type == "Polygon"


def test_snapshot_query_params_camel_case_alias():
    params = SnapshotQueryParams(
        **{
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [84.0, 27.0],
                        [85.0, 27.0],
                        [85.0, 28.0],
                        [84.0, 28.0],
                        [84.0, 27.0],
                    ]
                ],
            },
            "outputType": "shp",
            "useStWithin": False,
            "geometryType": ["point"],
        }
    )
    assert params.output_type == "shp"
    assert params.use_st_within is False
    assert params.geometry_type == ["point"]


def test_category_base_valid():
    cat = CategoryBase(
        types=["points", "lines"],
        select=["name", "highway"],
        where="tags['highway'] IS NOT NULL",
    )
    assert cat.types == ["points", "lines"]
    assert cat.select == ["name", "highway"]


def test_category_base_invalid_type():
    with pytest.raises(ValidationError):
        CategoryBase(
            types=["invalid_type"],
            select=["name"],
            where="tags['building'] IS NOT NULL",
        )
