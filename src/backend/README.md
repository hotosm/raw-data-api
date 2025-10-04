# Backend Module

This module provides standardized OSM data import and field update utilities.

## Installation

Install the project with backend dependencies:

```bash
uv sync --group backend
```

## Commands

### raw-backend

Import OSM data using osm2pgsql with standardized configuration.

```bash
raw-backend \
  --source path/to/file.osm.pbf \
  --host localhost \
  --port 5432 \
  --user postgres \
  --password postgres \
  --database raw \
  --insert \
  --cache 1000
```

**Key options:**
- `--insert`: Run initial data import
- `--update`: Update fields only
- `--replication`: Enable replication
- `--cache`: Cache size for osm2pgsql
- `--flat_nodes`: Path for flat nodes file
- `--post_index`: Run post-indexing only
- Extra args passed at the end are forwarded to osm2pgsql

**Example with extra osm2pgsql args:**
```bash
raw-backend --insert --cache 2000 --number-processes 4 --drop
```

### raw-field-update

Update H3 index and other fields for OSM features.

```bash
raw-field-update \
  -table ways_poly \
  --h3 h3 \
  --res 6 \
  --f d
```

**Key options:**
- `-table`: Target table (nodes, ways_poly, ways_line, relations)
- `--h3`: H3 column name
- `--res`: H3 resolution (default: 6)
- `-f`: Frequency (h=hourly, d=daily, w=weekly, m=monthly)
- `-i/--init`: Initial setup mode

## Configuration

Database connection can be set via environment variables:
- `PGHOST`
- `PGPORT`
- `PGUSER`
- `PGPASSWORD`
- `PGDATABASE`

## Structure

- `importer.py`: Main import logic (raw-backend)
- `field_updater.py`: Field update logic (raw-field-update)
- `sql/`: SQL schema and index files
- `lua/`: osm2pgsql flex output styles
- `login.py`: OSM authentication utilities
