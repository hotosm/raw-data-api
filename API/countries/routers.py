import psycopg2
from psycopg2.extras import DictCursor
from fastapi import APIRouter
from fastapi_versioning import  version
from geojson_pydantic import FeatureCollection
from src.galaxy.config import get_db_connection_params

router = APIRouter(prefix="/countries")
@router.get("/", response_model=FeatureCollection)
@version(1,0)
def get_countries():
    db_params = get_db_connection_params()
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(
                """
                with t1 as (
                    SELECT
                        name,
                        tags,
                        (ST_DUMP(boundary)).geom AS geom
                    FROM geoboundaries where priority = true),
                t2 AS (
                    SELECT
                        name,
                        ST_collect(array_agg(geom)) AS geom,
                        tags
                    FROM t1 GROUP BY name, tags)
                SELECT json_build_object('type',
                    'FeatureCollection',
                    'features',
                    json_agg(ST_ASGEOJSON(t2.*)::json))
                FROM t2
                """
            )
            result = cur.fetchall()[0][0]

    return FeatureCollection(**result)
