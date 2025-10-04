# Backend Module

OSM data import and field update utilities for raw-data-api.

## Prerequisites

- PostgreSQL with PostGIS and H3 extensions
- osm2pgsql >= 1.6.0
- Python 3.12+

## Installation

```bash
uv sync --group backend
```

## Commands

### raw-backend

Import OSM data using osm2pgsql.

**Basic usage:**
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

**With environment variables:**
```bash
export PGHOST=localhost
export PGPORT=5432
export PGUSER=postgres
export PGPASSWORD=postgres
export PGDATABASE=raw

raw-backend --source file.osm.pbf --insert --cache 1000
```

**Options:**
- `--source`: Path to OSM PBF file(s) or URL to download
- `--insert`: Run initial data import
- `--update`: Update fields only
- `--replication`: Enable replication
- `--cache`: Cache size for osm2pgsql (MB)
- `--flat_nodes`: Path for flat nodes file
- `--post_index`: Run post-indexing only
- `--fq`: Field update frequency (h/d/w/m, default: d)
- Extra args at end are forwarded to osm2pgsql

**Pass extra osm2pgsql arguments:**
```bash
raw-backend --source file.osm.pbf --insert --cache 2000 \
  --number-processes 4 --tablespace-index fastspace
```

**Download sample data:**

Sample data (Pokhara, Nepal) is included at `src/backend/sample_data/pokhara_all.osm.pbf`. To test:

```bash
raw-backend --insert --cache 1000
```

### raw-field-update

Update H3 spatial index for features.

```bash
raw-field-update \
  -table ways_poly \
  --h3 h3 \
  --res 6 \
  --f d
```

**Options:**
- `-table`: Target table (nodes, ways_poly, ways_line, relations)
- `--h3`: H3 column name (default: h3)
- `--res`: H3 resolution (default: 6)
- `-f`: Frequency (h=hourly, d=daily, w=weekly, m=monthly)
- `-i/--init`: Initial setup mode
- `--start/--end`: Date range (YYYY-MM-DD)

## Database Setup

Enable required extensions:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS h3 CASCADE;
CREATE EXTENSION IF NOT EXISTS h3_postgis CASCADE;
```

## What Gets Created

After import, you'll have:

**Tables:**
- `nodes` - Point features with geometry and tags
- `ways_line` - LineString features
- `ways_poly` - Polygon features  
- `relations` - Relation features
- `countries` - Country boundaries for filtering
- `users` - OSM user information

**Indexes:**
- Spatial (GIST) indexes on geometry columns
- H3 spatial indexes at resolution 6
- Primary keys on osm_id

**Columns:**
- `osm_id` - OpenStreetMap ID
- `tags` - JSONB key-value pairs
- `geom` - PostGIS geometry
- `h3` - H3 spatial index
- `uid`, `user`, `version`, `changeset`, `timestamp` - OSM metadata

## Module Structure

```
src/backend/
├── importer.py          # Main import (raw-backend)
├── field_updater.py     # H3 updates (raw-field-update)
├── replication          # OSM replication script
├── sql/                 # Schema and index SQL
├── lua/                 # osm2pgsql flex styles
├── countries/           # Country boundary data
└── sample_data/         # Test dataset (Pokhara)
```

## Getting OSM Data

Download from:
- [Geofabrik](https://download.geofabrik.de/) - Regional extracts
- [Planet OSM](https://planet.osm.org/) - Full planet file
- [BBBike](https://extract.bbbike.org/) - Custom extracts

Or use the included sample data for testing.
