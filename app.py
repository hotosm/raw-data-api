import psycopg2
from fastapi import FastAPI
from configparser import ConfigParser
from psycopg2.extras import DictCursor
from geojson_pydantic import FeatureCollection

app = FastAPI()
config = ConfigParser()
config.read("config.txt")


@app.get("/countries", response_model=FeatureCollection)
def get_countries():
    db_params = dict(config.items("PG"))
    conn = psycopg2.connect(**db_params)

    cur = conn.cursor(cursor_factory=DictCursor)
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
