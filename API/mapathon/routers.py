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

# Humanitarian OpenStreetmap Team
# 1100 13th Street NW Suite 800 Washington, D.C. 20005
# <info@hotosm.org>

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
    params: MapathonRequestParams, user_data=Depends(login_required)
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
