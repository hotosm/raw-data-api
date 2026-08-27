# Copyright (C) 2026 Humanitarian OpenStreetmap Team

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

"""Tests for the PostPass query builder (osm2pgsql_query_builder.postpass)."""

import pytest
from pydantic import ValidationError

from osm2pgsql_query_builder.postpass_module import (
    BboxFilter,
    PostPassQueryParams,
    build_postpass_bbox_filter,
    build_postpass_query,
    wrap_postpass_geojson,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

NAIROBI_BBOX = {"minx": 36.7, "miny": -1.3, "maxx": 36.9, "maxy": -1.2}

NAIROBI_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [36.7, -1.3],
            [36.9, -1.3],
            [36.9, -1.2],
            [36.7, -1.2],
            [36.7, -1.3],
        ]
    ],
}


# ---------------------------------------------------------------------------
# BboxFilter tests
# ---------------------------------------------------------------------------


def test_bbox_filter_valid():
    bbox = BboxFilter(**NAIROBI_BBOX)
    assert bbox.minx == 36.7
    assert bbox.miny == -1.3
    assert bbox.maxx == 36.9
    assert bbox.maxy == -1.2


def test_bbox_filter_inverted_x():
    with pytest.raises(ValidationError, match="minx"):
        BboxFilter(minx=36.9, miny=-1.3, maxx=36.7, maxy=-1.2)


def test_bbox_filter_inverted_y():
    with pytest.raises(ValidationError, match="miny"):
        BboxFilter(minx=36.7, miny=-1.2, maxx=36.9, maxy=-1.3)


# ---------------------------------------------------------------------------
# PostPassQueryParams tests
# ---------------------------------------------------------------------------


def test_params_with_explicit_bbox():
    params = PostPassQueryParams(bbox=NAIROBI_BBOX)
    assert params.bbox.minx == 36.7
    assert params.geometry is None


def test_params_with_polygon_geometry():
    params = PostPassQueryParams(geometry=NAIROBI_POLYGON)
    assert params.geometry is not None
    assert params.bbox is None
    bbox = params.get_bbox()
    assert round(bbox.minx, 1) == 36.7
    assert round(bbox.maxy, 1) == -1.2


def test_params_with_feature_geometry():
    feature = {
        "type": "Feature",
        "properties": {},
        "geometry": NAIROBI_POLYGON,
    }
    params = PostPassQueryParams(geometry=feature)
    # GeometryValidatorMixin should unwrap to the inner geometry
    assert params.geometry.type == "Polygon"


def test_params_requires_geometry_or_bbox():
    with pytest.raises(ValidationError, match="Either 'geometry' or 'bbox'"):
        PostPassQueryParams()


def test_params_invalid_geometry_type():
    with pytest.raises(ValidationError, match="Invalid geometry_type"):
        PostPassQueryParams(bbox=NAIROBI_BBOX, geometry_type=["raster"])


def test_params_geometry_type_deduplication():
    params = PostPassQueryParams(
        bbox=NAIROBI_BBOX,
        geometry_type=["point", "point", "line"],
    )
    assert len(params.geometry_type) == 2
    assert set(params.geometry_type) == {"point", "line"}


def test_get_bbox_prefers_explicit():
    params = PostPassQueryParams(
        bbox=NAIROBI_BBOX,
        geometry=NAIROBI_POLYGON,
    )
    bbox = params.get_bbox()
    assert bbox.minx == 36.7  # uses explicit bbox, not derived


def test_get_tables_defaults_all():
    params = PostPassQueryParams(bbox=NAIROBI_BBOX)
    tables = params.get_tables()
    assert set(tables) == {"postpass_point", "postpass_line", "postpass_polygon"}


def test_get_tables_filtered():
    params = PostPassQueryParams(bbox=NAIROBI_BBOX, geometry_type=["point"])
    assert params.get_tables() == ["postpass_point"]


# ---------------------------------------------------------------------------
# build_postpass_bbox_filter
# ---------------------------------------------------------------------------


def test_build_bbox_filter_output():
    bbox = BboxFilter(**NAIROBI_BBOX)
    clause = build_postpass_bbox_filter(bbox)
    assert "ST_MakeBox2D" in clause
    assert "ST_SetSRID" in clause
    assert "4326" in clause
    assert "36.7" in clause
    assert "-1.3" in clause


# ---------------------------------------------------------------------------
# build_postpass_query — geometry type routing
# ---------------------------------------------------------------------------


def test_query_points_only():
    params = PostPassQueryParams(
        bbox=NAIROBI_BBOX,
        geometry_type=["point"],
    )
    sql = build_postpass_query(params)
    assert "postpass_point" in sql
    assert "postpass_line" not in sql
    assert "postpass_polygon" not in sql


def test_query_all_tables_by_default():
    params = PostPassQueryParams(bbox=NAIROBI_BBOX)
    sql = build_postpass_query(params)
    assert "postpass_point" in sql
    assert "postpass_line" in sql
    assert "postpass_polygon" in sql
    assert "UNION ALL" in sql


def test_query_two_tables():
    params = PostPassQueryParams(
        bbox=NAIROBI_BBOX,
        geometry_type=["point", "line"],
    )
    sql = build_postpass_query(params)
    assert "postpass_point" in sql
    assert "postpass_line" in sql
    assert "postpass_polygon" not in sql
    assert sql.count("UNION ALL") == 1


# ---------------------------------------------------------------------------
# build_postpass_query — tag filters
# ---------------------------------------------------------------------------


def test_query_with_all_geometry_filter():
    params = PostPassQueryParams(
        bbox=NAIROBI_BBOX,
        geometry_type=["point"],
        filters={
            "tags": {
                "all_geometry": {"join_or": {"amenity": ["school", "hospital"]}}
            }
        },
    )
    sql = build_postpass_query(params)
    assert "amenity" in sql
    assert "school" in sql
    assert "hospital" in sql


def test_query_single_value_tag():
    params = PostPassQueryParams(
        bbox=NAIROBI_BBOX,
        geometry_type=["line"],
        filters={
            "tags": {"all_geometry": {"join_or": {"highway": ["primary"]}}}
        },
    )
    sql = build_postpass_query(params)
    assert "highway" in sql
    assert "primary" in sql
    assert "postpass_line" in sql


def test_query_join_and_filter():
    params = PostPassQueryParams(
        bbox=NAIROBI_BBOX,
        geometry_type=["polygon"],
        filters={
            "tags": {
                "all_geometry": {
                    "join_and": {
                        "building": ["yes"],
                        "amenity": ["school"],
                    }
                }
            }
        },
    )
    sql = build_postpass_query(params)
    assert "building" in sql
    assert "amenity" in sql
    assert "AND" in sql


def test_query_no_filters_just_bbox():
    params = PostPassQueryParams(
        bbox=NAIROBI_BBOX,
        geometry_type=["point"],
    )
    sql = build_postpass_query(params)
    assert "ST_MakeBox2D" in sql
    assert "WHERE" in sql


# ---------------------------------------------------------------------------
# build_postpass_query — attribute projection
# ---------------------------------------------------------------------------


def test_query_with_attributes():
    params = PostPassQueryParams(
        bbox=NAIROBI_BBOX,
        geometry_type=["point"],
    )
    sql = build_postpass_query(params, attributes=["name", "amenity"])
    assert "tags ->> 'name' AS name" in sql
    assert "tags ->> 'amenity' AS amenity" in sql


def test_query_without_attributes_returns_tags_column():
    params = PostPassQueryParams(bbox=NAIROBI_BBOX, geometry_type=["point"])
    sql = build_postpass_query(params)
    assert "osm_id, tags, geom" in sql


def test_query_attribute_with_colon_sanitized():
    params = PostPassQueryParams(bbox=NAIROBI_BBOX, geometry_type=["point"])
    sql = build_postpass_query(params, attributes=["addr:street"])
    # colon should be replaced with underscore in column alias
    assert "addr_street" in sql


# ---------------------------------------------------------------------------
# wrap_postpass_geojson
# ---------------------------------------------------------------------------


def test_wrap_geojson_structure():
    inner = "SELECT osm_id, tags, geom FROM postpass_point WHERE geom && bbox"
    wrapped = wrap_postpass_geojson(inner)
    assert "json_build_object" in wrapped
    assert "'FeatureCollection'" in wrapped
    assert "ST_AsGeoJSON" in wrapped
    assert "COALESCE" in wrapped
    assert "[]" in wrapped  # empty fallback


def test_wrap_geojson_strips_trailing_semicolon():
    inner = "SELECT osm_id, tags, geom FROM postpass_point;"
    wrapped = wrap_postpass_geojson(inner)
    # The inner query should not contain the semicolon
    assert "postpass_point;" not in wrapped


def test_full_pipeline_bbox():
    """End-to-end: bbox params → query → wrapped GeoJSON SQL."""
    params = PostPassQueryParams(
        bbox=NAIROBI_BBOX,
        geometry_type=["point"],
        filters={
            "tags": {
                "all_geometry": {"join_or": {"amenity": ["school", "hospital"]}}
            }
        },
    )
    sql = wrap_postpass_geojson(build_postpass_query(params))
    assert "FeatureCollection" in sql
    assert "postpass_point" in sql
    assert "amenity" in sql


def test_full_pipeline_from_polygon():
    """End-to-end: polygon geometry → bbox derived → query built."""
    params = PostPassQueryParams(
        geometry=NAIROBI_POLYGON,
        geometry_type=["point"],
    )
    sql = build_postpass_query(params)
    assert "postpass_point" in sql
    assert "ST_MakeBox2D" in sql


def test_top_level_import():
    """PostPass symbols are importable from the package root."""
    from osm2pgsql_query_builder import (
        BboxFilter,
        PostPassQueryParams,
        build_postpass_query,
        wrap_postpass_geojson,
    )
    assert BboxFilter is not None
    assert PostPassQueryParams is not None
    assert callable(build_postpass_query)
    assert callable(wrap_postpass_geojson)