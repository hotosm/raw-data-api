import psycopg2

from psycopg2 import sql
from psycopg2.extras import DictCursor

from src.galaxy import config
from . import ChangesetResult, FilterParams
from .utils import geom_filter_subquery
from fastapi import APIRouter

router = APIRouter(prefix="/changesets")


@router.post("/", response_model=ChangesetResult)
def get_changesets(params: FilterParams):
    geom_filter_sq = geom_filter_subquery(params.dict())

    t3 = """
        SELECT 
            name,
            id,
            user_id,
            (EACH(added)).key AS added_key,
            (EACH(added)).value::numeric as added_value,
            (EACH(modified)).key AS modified_key,
            (EACH(modified)).value::numeric as modified_value,
            (EACH(deleted)).key AS deleted_key,
            (EACH(deleted)).value::numeric as deleted_value
        from t2
    """

    t3_filters = []
    if params.start_datetime is not None:
        t3_filters.append(
            f"created_at > '{params.start_datetime.isoformat()}'"
        )
    if params.end_datetime is not None:
        t3_filters.append(f"created_at <= '{params.end_datetime.isoformat()}'")
    if params.hashtag is not None:
        t3_filters.append(f"'{params.hashtag}' = ANY(hashtags)")

    if len(t3_filters) > 0:
        filter_sql = " AND ".join(t3_filters)
        t3 += f"WHERE {filter_sql}"

    query = f"""WITH t1 AS ({geom_filter_sq}),
        t2 AS (
        select 
            t1.name,
            cs.id,
            cs.user_id,
            cs.created_at,
            cs.hashtags,
            coalesce(cs.added, hstore('none', '0')) AS added,
            coalesce(cs.modified, hstore('none', '0')) AS modified,
            coalesce(cs.deleted, hstore('none', '0')) AS deleted
        FROM changesets AS cs, t1 where
            ST_INTERSECTS(cs.bbox, t1.boundary)
        ),
        t3 AS ({t3}),
        t4 AS (
        SELECT 
            name,
            count(id) AS total_changesets,
            count(DISTINCT user_id) AS contributors
        from t3 GROUP BY name
        )
        SELECT t4.name,
            t4.total_changesets,
            t4.contributors,
            coalesce(added_filter_highway.added_total, 0) AS added_highway,
            coalesce(modified_filter_highway.modified_total, 0) AS modified_highway,
            coalesce(deleted_filter_highway.deleted_total, 0) AS deleted_highway,
            coalesce(added_filter_highway_km.added_total, 0) AS added_highway_km,
            coalesce(modified_filter_highway_km.modified_total, 0) AS modified_highway_km,
            coalesce(deleted_filter_highway_km.deleted_total, 0) AS deleted_highway_km
        FROM t4
        LEFT JOIN (
            Select name, added_key, sum(added_value) AS added_total from t3 where added_key = 'highway' group by name, added_key
        ) AS added_filter_highway
        ON added_filter_highway.name = t4.name
        LEFT JOIN (
            Select name, modified_key, sum(modified_value) AS modified_total from t3 where modified_key = 'highway' group by name, modified_key
        ) AS modified_filter_highway
        ON modified_filter_highway.name = t4.name
        LEFT JOIN (
            Select name, deleted_key, sum(deleted_value) AS deleted_total from t3 where deleted_key = 'highway' group by name, deleted_key
        ) AS deleted_filter_highway
        ON deleted_filter_highway.name = t4.name
        LEFT JOIN (
            Select name, added_key, sum(added_value) / 1000 AS added_total from t3 where added_key = 'highway_km' group by name, added_key
        ) AS added_filter_highway_km
        ON added_filter_highway_km.name = t4.name
        LEFT JOIN (
            Select name, modified_key, sum(modified_value) / 1000 AS modified_total from t3 where modified_key = 'highway_km' group by name, modified_key
        ) AS modified_filter_highway_km
        ON modified_filter_highway_km.name = t4.name
        LEFT JOIN (
            Select name, deleted_key, sum(deleted_value) / 1000 AS deleted_total from t3 where deleted_key = 'highway_km' group by name, deleted_key
        ) AS deleted_filter_highway_km
        ON deleted_filter_highway_km.name = t4.name;
        """

    db_params = get_db_connection_params()
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(query)
            result = cur.fetchall()

    result_dto = ChangesetResult(**dict(result[0]))

    return result_dto
