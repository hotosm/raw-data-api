from fastapi import APIRouter, Depends

import psycopg2

from psycopg2.extras import DictCursor

from .. import config

from . import (
    MappedFeature,
    MapathonSummary,
    MapathonRequestParams,
    MappedFeatureWithUser,
    MapathonContributor,
    MapathonDetail,
)

from .utils import (
    create_changeset_query,
    create_osm_history_query,
    create_users_contributions_query,
)

from ..auth import login_required

router = APIRouter(prefix="/mapathon")


@router.post("/detail", response_model=MapathonDetail)
def get_mapathon_detailed_report(
    # params: MapathonRequestParams, user_data=Depends(login_required)
    params: MapathonRequestParams

):
    db_params = dict(config.items("INSIGHTS_PG"))
    conn = psycopg2.connect(**db_params)

    cur = conn.cursor(cursor_factory=DictCursor)

    changeset_query, _, _ = create_changeset_query(params, conn, cur)

    # OSM element history query.
    osm_history_query = create_osm_history_query(
        changeset_query, with_username=True
    )

    cur.execute(osm_history_query)
    result = cur.fetchall()

    mapped_features = [MappedFeatureWithUser(**r) for r in result]

    contributors_query = create_users_contributions_query(
        params, changeset_query
    )
    cur.execute(contributors_query)
    result = cur.fetchall()

    contributors = [MapathonContributor(**r) for r in result]

    report = MapathonDetail(
        contributors=contributors, mapped_features=mapped_features
    )

    return report


@router.post("/summary", response_model=MapathonSummary)
def get_mapathon_summary(params: MapathonRequestParams):
    db_params = dict(config.items("INSIGHTS_PG"))
    conn = psycopg2.connect(**db_params)

    cur = conn.cursor(cursor_factory=DictCursor)

    changeset_query, hashtag_filter, timestamp_filter = create_changeset_query(
        params, conn, cur
    )

    # OSM element history query.
    osm_history_query = create_osm_history_query(
        changeset_query, with_username=False
    )

    cur.execute(osm_history_query)
    result = cur.fetchall()

    mapped_features = [MappedFeature(**r) for r in result]

    # Get total contributors.
    cur.execute(
        f"""
        SELECT COUNT(distinct user_id) as contributors_count
        FROM osm_changeset
        WHERE {timestamp_filter} AND ({hashtag_filter})
    """
    )
    total_contributors = cur.fetchone().get("contributors_count")

    report = MapathonSummary(
        total_contributors=total_contributors, mapped_features=mapped_features
    )

    return report
