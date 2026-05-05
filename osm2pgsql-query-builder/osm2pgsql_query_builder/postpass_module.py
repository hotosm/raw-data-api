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

"""PostPass query builder.

Generates SQL for the Geofabrik PostPass API
(https://postpass.geofabrik.de/api/0.2/interpreter).

PostPass and osm2pgsql use the same tag column format (``tags ->> 'key'``)
so all filter helpers are reused from this package.  The only
PostPass-specific pieces are:

* Different table names: ``postpass_point``, ``postpass_line``,
  ``postpass_polygon``
* Bbox geometry expressed with the ``&&`` operator (fast index scan)
  rather than ``ST_intersects`` against a full polygon
* A ``json_build_object`` GeoJSON wrapper suitable for the PostPass
  HTTP response format

Example usage::

    from osm2pgsql_query_builder.postpass import (
        PostPassQueryParams,
        build_postpass_query,
        wrap_postpass_geojson,
    )

    params = PostPassQueryParams(
        bbox={"minx": 36.7, "miny": -1.3, "maxx": 36.9, "maxy": -1.2},
        filters={
            "tags": {"all_geometry": {"join_or": {"amenity": ["school", "hospital"]}}}
        },
        geometry_type=["point"],
    )

    sql = wrap_postpass_geojson(build_postpass_query(params))
"""

from __future__ import annotations

import logging
from typing import List, Optional, Union

from geojson_pydantic import Feature, FeatureCollection, MultiPolygon, Polygon
from pydantic import Field, field_validator, model_validator

from .builder import build_column_select, build_tag_filter, parse_filters
from .models import BaseModel, Filters

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PostPass table mapping
# ---------------------------------------------------------------------------

#: Maps geometry-type name → PostPass table name.
POSTPASS_TABLE_MAP: dict[str, str] = {
    "point": "postpass_point",
    "line": "postpass_line",
    "polygon": "postpass_polygon",
}

#: Default geometry types queried when none is specified.
ALL_POSTPASS_GEOMETRY_TYPES: list[str] = ["point", "line", "polygon"]


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class BboxFilter(BaseModel):
    """Axis-aligned bounding box in WGS-84 (EPSG:4326).

    All four fields are required; coordinates must be in decimal degrees.

    Example::

        BboxFilter(minx=36.7, miny=-1.3, maxx=36.9, maxy=-1.2)

    Or from a dict::

        BboxFilter(**{"minx": 36.7, "miny": -1.3, "maxx": 36.9, "maxy": -1.2})
    """

    minx: float = Field(..., description="Western longitude boundary")
    miny: float = Field(..., description="Southern latitude boundary")
    maxx: float = Field(..., description="Eastern longitude boundary")
    maxy: float = Field(..., description="Northern latitude boundary")

    @model_validator(mode="after")
    def validate_bounds(self) -> "BboxFilter":
        if self.minx >= self.maxx:
            raise ValueError(
                f"minx ({self.minx}) must be less than maxx ({self.maxx})"
            )
        if self.miny >= self.maxy:
            raise ValueError(
                f"miny ({self.miny}) must be less than maxy ({self.maxy})"
            )
        return self


class PostPassQueryParams(BaseModel):
    """Parameters for PostPass SQL query generation.

    Accepts **either** a full GeoJSON geometry (bbox is derived from its
    envelope) **or** an explicit :class:`BboxFilter`.  At least one must
    be supplied.

    ``filters`` uses the same structure as :class:`~.models.SnapshotQueryParams`
    so existing filter configs can be reused without modification.

    ``geometry_type`` controls which PostPass tables are queried.  Defaults
    to all three (``["point", "line", "polygon"]``).

    Example — explicit bbox::

        PostPassQueryParams(
            bbox={"minx": 36.7, "miny": -1.3, "maxx": 36.9, "maxy": -1.2},
            filters={
                "tags": {
                    "all_geometry": {"join_or": {"amenity": ["school", "hospital"]}}
                }
            },
            geometry_type=["point"],
        )

    Example — derive bbox from a GeoJSON polygon::

        PostPassQueryParams(
            geometry={
                "type": "Polygon",
                "coordinates": [[[36.7, -1.3], [36.9, -1.3],
                                  [36.9, -1.2], [36.7, -1.2], [36.7, -1.3]]],
            },
            filters={"tags": {"all_geometry": {"join_or": {"building": []}}}},
        )
    """

    geometry: Optional[
        Union[Polygon, MultiPolygon, Feature, FeatureCollection]
    ] = Field(
        default=None,
        description=(
            "GeoJSON geometry (Polygon/MultiPolygon/Feature/FeatureCollection). "
            "The bbox is automatically extracted from the envelope. "
            "Either this or bbox must be provided."
        ),
    )
    bbox: Optional[BboxFilter] = Field(
        default=None,
        description=(
            "Explicit bounding box in WGS-84. "
            "Either this or geometry must be provided."
        ),
    )
    filters: Optional[Filters] = Field(
        default=None,
        description=(
            "Tag and attribute filters. "
            "Uses the same structure as SnapshotQueryParams."
        ),
        json_schema_extra={
            "example": {
                "tags": {"all_geometry": {"join_or": {"amenity": ["school"]}}},
                "attributes": {"all_geometry": ["name"]},
            }
        },
    )
    geometry_type: Optional[List[str]] = Field(
        default=None,
        description=(
            "Which PostPass tables to query: 'point', 'line', 'polygon'. "
            "Defaults to all three."
        ),
        json_schema_extra={"example": ["point", "polygon"]},
    )

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("geometry")
    @classmethod
    def _extract_polygon(
            cls,
            value: Optional[Union[Polygon, MultiPolygon, Feature, FeatureCollection]],
    ) -> Optional[Union[Polygon, MultiPolygon]]:
        """Unwrap Feature / FeatureCollection, enforce Polygon/MultiPolygon."""
        if value is None:
            return None
        if value.type == "Feature":
            if value.geometry.type not in ("Polygon", "MultiPolygon"):
                raise ValueError(
                    f"Feature geometry must be Polygon or MultiPolygon, "
                    f"got {value.geometry.type}"
                )
            return value.geometry
        if value.type == "FeatureCollection":
            if len(value.features) != 1:
                raise ValueError(
                    "FeatureCollection must contain exactly one feature"
                )
            geom = value.features[0].geometry
            if geom.type not in ("Polygon", "MultiPolygon"):
                raise ValueError(
                    f"Feature geometry must be Polygon or MultiPolygon, "
                    f"got {geom.type}"
                )
            return geom
        return value

    @field_validator("geometry_type")
    @classmethod
    def _validate_geometry_types(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return value
        invalid = [g for g in value if g not in POSTPASS_TABLE_MAP]
        if invalid:
            raise ValueError(
                f"Invalid geometry_type values: {invalid}. "
                f"Must be one of: {list(POSTPASS_TABLE_MAP)}"
            )
        return list(set(value))  # deduplicate

    @model_validator(mode="after")
    def _require_geometry_or_bbox(self) -> "PostPassQueryParams":
        if self.geometry is None and self.bbox is None:
            raise ValueError("Either 'geometry' or 'bbox' must be provided")
        return self

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_bbox(self) -> BboxFilter:
        """Return the effective bbox.

        If ``bbox`` was supplied explicitly, return it directly.
        Otherwise compute the envelope of the ``geometry``.
        """
        if self.bbox is not None:
            return self.bbox

        # Derive bbox from geometry envelope
        def _flatten(coords):
            if not coords:
                return []
            if isinstance(coords[0], (int, float)):
                return [coords]
            return [pt for ring in coords for pt in _flatten(ring)]

        raw = self.geometry.model_dump()
        coords = raw.get("coordinates", [])
        points = _flatten(coords)
        if not points:
            raise ValueError("Cannot extract bbox: geometry has no coordinates")

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return BboxFilter(
            minx=min(xs), miny=min(ys), maxx=max(xs), maxy=max(ys)
        )

    def get_tables(self) -> list[str]:
        """Return the PostPass table names to query."""
        types = self.geometry_type or ALL_POSTPASS_GEOMETRY_TYPES
        return [POSTPASS_TABLE_MAP[t] for t in types]


# ---------------------------------------------------------------------------
# Query builders
# ---------------------------------------------------------------------------


def build_postpass_bbox_filter(bbox: BboxFilter) -> str:
    """Build a PostGIS bbox filter using the ``&&`` operator.

    The ``&&`` operator uses the spatial index for a fast bounding-box
    pre-filter, equivalent to ``ST_intersects(geom, ST_MakeEnvelope(...))``.

    Args:
        bbox: A :class:`BboxFilter` instance.

    Returns:
        A SQL fragment suitable for a WHERE clause, e.g.::

            geom && ST_SetSRID(ST_MakeBox2D(ST_MakePoint(36.7, -1.3),
                                            ST_MakePoint(36.9, -1.2)), 4326)
    """
    return (
        f"geom && ST_SetSRID("
        f"ST_MakeBox2D("
        f"ST_MakePoint({bbox.minx}, {bbox.miny}), "
        f"ST_MakePoint({bbox.maxx}, {bbox.maxy})"
        f"), 4326)"
    )


def build_postpass_query(
        params: PostPassQueryParams,
        attributes: Optional[List[str]] = None,
) -> str:
    """Build SQL SELECT statements for PostPass tables.

    Generates one sub-query per geometry type (or per table in
    ``params.geometry_type``) and joins them with ``UNION ALL``.

    Args:
        params:     A :class:`PostPassQueryParams` instance.
        attributes: Optional list of OSM tag keys to project as named
                    columns (e.g. ``["name", "amenity"]``).  When omitted,
                    only ``osm_id``, ``tags``, and ``geom`` are returned.

    Returns:
        A SQL string that can be sent directly to the PostPass API.

    Example output::

        SELECT osm_id, tags, geom
        FROM postpass_point
        WHERE (tags ->> 'amenity' IN ('school', 'hospital'))
          AND geom && ST_SetSRID(ST_MakeBox2D(...), 4326)
        UNION ALL
        SELECT osm_id, tags, geom
        FROM postpass_line
        WHERE ...
    """
    bbox = params.get_bbox()
    tables = params.get_tables()

    # --- SELECT clause ---
    if attributes:
        from .builder import sanitize_column_name
        col_parts = ["osm_id"]
        for attr in attributes:
            col_parts.append(
                f"tags ->> '{attr.strip()}' AS {sanitize_column_name(attr.strip())}"
            )
        col_parts.append("geom")
        select_sql = ", ".join(col_parts)
    else:
        select_sql = "osm_id, tags, geom"

    # --- WHERE clauses ---
    bbox_clause = build_postpass_bbox_filter(bbox)

    # Parse tag filters (reuses the shared parse_filters / build_tag_filter)
    tag_where: Optional[str] = None
    if params.filters:
        filters_dict = params.filters.model_dump()
        (
            _tags,
            _attributes,
            _point_attr,
            _line_attr,
            _poly_attr,
            _master_attr,
            point_tag_filter,
            line_tag_filter,
            poly_tag_filter,
            master_tag_filter,
        ) = parse_filters(filters_dict)

        # For PostPass we apply master_tag_filter (all_geometry) to every table,
        # and geometry-specific filters where they match.
        # Build a simple combined filter for all tables (PostPass has no
        # per-geometry per-table differentiation in its schema).
        all_filters = [f for f in [
            master_tag_filter,
            point_tag_filter,
            line_tag_filter,
            poly_tag_filter,
        ] if f]
        if all_filters:
            built = [build_tag_filter(f) for f in all_filters if f]
            built = [b for b in built if b]
            tag_where = " AND ".join(f"({b})" for b in built) if built else None

    # --- Assemble per-table sub-queries ---
    sub_queries: list[str] = []
    for table in tables:
        where_parts = []
        if tag_where:
            where_parts.append(tag_where)
        where_parts.append(bbox_clause)

        where_sql = " AND ".join(where_parts)
        sub_queries.append(
            f"SELECT {select_sql} FROM {table} WHERE {where_sql}"
        )

    return "\nUNION ALL\n".join(sub_queries)


def wrap_postpass_geojson(base_sql: str) -> str:
    """Wrap a SELECT query in a GeoJSON FeatureCollection builder.

    The inner query must return at least ``osm_id``, ``geom``, and ``tags``.
    The ``COALESCE`` ensures an empty ``[]`` is returned rather than ``null``
    when no features match.

    Args:
        base_sql: Raw SQL from :func:`build_postpass_query`.

    Returns:
        SQL that produces a single-row result containing the full
        GeoJSON FeatureCollection as a JSON object.
    """
    inner = base_sql.rstrip(";")
    return (
        "SELECT json_build_object(\n"
        "    'type', 'FeatureCollection',\n"
        "    'features', COALESCE(json_agg(\n"
        "        json_build_object(\n"
        "            'type',       'Feature',\n"
        "            'id',         sub.osm_id,\n"
        "            'geometry',   ST_AsGeoJSON(sub.geom)::json,\n"
        "            'properties', sub.tags\n"
        "        )\n"
        "    ), '[]'::json)\n"
        ")\n"
        f"FROM (\n{inner}\n) AS sub"
    )


