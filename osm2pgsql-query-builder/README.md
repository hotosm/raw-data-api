# osm2pgsql-query-builder

SQL query builder for [osm2pgsql](https://osm2pgsql.org/)-format PostgreSQL databases.

Takes filter parameters (geometry, tags, attributes, geometry type) and generates PostGIS SQL queries against the standard osm2pgsql table schema (`nodes`, `ways_line`, `ways_poly`, `relations`).

Extracted from [raw-data-api](https://github.com/hotosm/raw-data-api) so the logic can be reused in other projects that work with osm2pgsql databases (e.g. [PostPass](https://github.com/hotosm/postpass)).

## Install

```bash
pip install osm2pgsql-query-builder
```

Or from a local checkout (e.g. within the raw-data-api monorepo):

```bash
pip install ./osm2pgsql-query-builder
```

## Usage

### Snapshot query (quick start)

Use `SnapshotQueryParams` to build a params object and generate SQL:

```python
from osm2pgsql_query_builder import SnapshotQueryParams, build_snapshot_query

params = SnapshotQueryParams(
    geometry={
        "type": "Polygon",
        "coordinates": [[
            [84.924, 27.766],
            [85.319, 27.766],
            [85.319, 28.025],
            [84.924, 28.025],
            [84.924, 27.766],
        ]],
    },
    filters={
        "tags": {"all_geometry": {"join_or": {"building": []}}},
        "attributes": {"all_geometry": ["name"]},
    },
)

sql = build_snapshot_query(params)
```

### Custom export categories (YAML/JSON config)

Use `CategoryBase` for parsing category definitions from config files:

```python
from osm2pgsql_query_builder import CategoryBase

# Parse a single category from a YAML/JSON config
category = CategoryBase(
    types=["lines", "polygons"],
    select=["name", "highway"],
    where="tags['highway'] IS NOT NULL",
)

# Use the parsed values with the builder functions
from osm2pgsql_query_builder import convert_tags_to_postgres

where_sql = convert_tags_to_postgres(category.where)
# → "tags->>'highway' IS NOT NULL"
```

### Extending the models

`SnapshotQueryParams` and `CategoryBase` are designed to be subclassed for
application-specific fields:

```python
from osm2pgsql_query_builder import SnapshotQueryParams, CategoryBase
from pydantic import Field
from typing import List, Optional

class MyParams(SnapshotQueryParams):
    file_name: Optional[str] = None
    min_zoom: Optional[int] = None

class MyCategory(CategoryBase):
    formats: List[str] = Field(...)
```

## Available functions

| Function | Description |
| --- | --- |
| `build_snapshot_query` | Full snapshot extraction query with tag/attribute/geometry filters |
| `build_geometry_type_query` | Separate queries per geometry type (point/line/polygon) with schemas |
| `build_plain_geojson_query` | Simple query from tag filters and bbox |
| `build_geom_filter` | Geometry intersection filter clause |
| `build_column_select` | Column SELECT clause from attribute list |
| `build_tag_filter` | WHERE clause from tag filters |
| `parse_filters` | Parse filter dict into per-geometry-type filters |
| `build_where_clause` | WHERE clause with grid/country index support |
| `convert_tags_to_postgres` | Convert `tags['key']` syntax to `tags->>'key'` |
| `sanitize_filename` | Sanitize a string for use as a file name |
| `sanitize_column_name` | Sanitize a string for use as a SQL column alias |

## Models

| Model | Description |
| --- | --- |
| `SnapshotQueryParams` | Pydantic model for snapshot query parameters (geometry, filters, output type, etc.) |
| `CategoryBase` | Pydantic model for category config (types, select, where) |
| `Filters` | Tag + attribute filter container |
| `TagsFilter` | Per-geometry-type tag filters (point/line/polygon/all_geometry) |
| `AttributeFilter` | Per-geometry-type attribute column lists |
| `SQLFilter` | Single filter with join_or / join_and dicts |
| `GeometryValidatorMixin` | Mixin that extracts Polygon/MultiPolygon from Feature/FeatureCollection |
| `BaseModel` | Pydantic BaseModel with camelCase alias support |

## Development

```bash
uv sync --extra dev
uv run pytest
```

Build the package:

```bash
uv build
```
