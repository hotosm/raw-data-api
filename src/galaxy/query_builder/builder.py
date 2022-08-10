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

from doctest import master
from itertools import filterfalse
from numpy import poly
from psycopg2 import sql
from json import dumps
import re
from ..validation.models import Frequency, OsmElementRawData, GeometryTypeRawData as geomtype , SupportedFilters, SupportedGeometryFilters
HSTORE_COLUMN = "tags"


def create_hashtag_filter_query(project_ids, hashtags, cur, conn,prefix=False):
    '''returns hastag filter query '''

    # merged_items = [*project_ids , *hashtags]
    if prefix : # default prefix is c
        filter_query = "(c.{hstore_column} -> %s) ~~* %s"
    else :
        filter_query = "({hstore_column} -> %s) ~~* %s"

    hashtag_filter_values = [
        *[f"%hotosm-project-{i};%" if project_ids is not None else '' for i in project_ids],
        *[f"%{i};%" for i in hashtags],
    ]
    hashtag_tags_filters = [
        cur.mogrify(filter_query, ("hashtags", i)).decode()
        for i in hashtag_filter_values
    ]

    comment_filter_values = [
        *[f"%hotosm-project-{i} %" if project_ids is not None else '' for i in project_ids],
        *[f"%{i} %" for i in hashtags],
    ]
    comment_tags_filters = [
        cur.mogrify(filter_query, ("comment", i)).decode()
        for i in comment_filter_values
    ]

    # Include cases for hasthags and comments found at the end of the string.
    no_char_filter_values = [
        *[f"%hotosm-project-{i}" if project_ids is not None else '' for i in project_ids],
        *[f"%{i}" for i in hashtags],
    ]
    no_char_filter_values = [
        [cur.mogrify(filter_query, (k, i)).decode()
         for k in ("hashtags", "comment")]
        for i in no_char_filter_values
    ]

    no_char_filter_values = [
        item for sublist in no_char_filter_values for item in sublist]

    hashtag_filter = [*hashtag_tags_filters, *
                      comment_tags_filters, *no_char_filter_values]

    hashtag_filter = [
        sql.SQL(f).format(hstore_column=sql.Identifier(HSTORE_COLUMN))
        for f in hashtag_filter
    ]

    hashtag_filter = sql.SQL(" OR ").join(hashtag_filter).as_string(conn)

    return hashtag_filter


def create_timestamp_filter_query(column_name,from_timestamp, to_timestamp, cur,prefix=False):
    '''returns timestamp filter query '''

    timestamp_column = column_name
    # Subquery to filter changesets matching hashtag and dates.
    if prefix:
        timestamp_filter = sql.SQL("c.{timestamp_column} between %s AND %s").format(
            timestamp_column=sql.Identifier(timestamp_column))
    else :
        timestamp_filter = sql.SQL("{timestamp_column} between %s AND %s").format(
            timestamp_column=sql.Identifier(timestamp_column))
    timestamp_filter = cur.mogrify(timestamp_filter,
                                   (from_timestamp, to_timestamp)).decode()

    return timestamp_filter


def create_changeset_query(params, conn, cur):
    '''returns the changeset query'''

    hashtag_filter = create_hashtag_filter_query(params.project_ids,
                                                 params.hashtags, cur, conn)
    timestamp_filter = create_timestamp_filter_query("created_at", params.from_timestamp,
                                                     params.to_timestamp, cur)

    changeset_query = f"""
    SELECT user_id, id as changeset_id, user_name as username
    FROM osm_changeset
    WHERE {timestamp_filter} AND ({hashtag_filter})
    """

    return changeset_query, hashtag_filter, timestamp_filter


def create_osm_history_query(changeset_query, with_username):
    '''returns osm history query'''

    column_names = [
        f"(each({HSTORE_COLUMN})).key AS feature",
        "action",
        "count(distinct id) AS count",
    ]
    group_by_names = ["feature", "action"]

    if with_username is True:
        column_names.append("username")
        group_by_names.extend(["user_id", "username"])

    order_by = (["count DESC"]
                if with_username is False else ["user_id", "action", "count"])
    order_by = ", ".join(order_by)

    columns = ", ".join(column_names)
    group_by_columns = ", ".join(group_by_names)

    query = f"""
    WITH T1 AS({changeset_query})
    SELECT {columns} FROM osm_element_history AS t2, t1
    WHERE t1.changeset_id = t2.changeset
    GROUP BY {group_by_columns} ORDER BY {order_by}
    """

    return query


def create_userstats_get_statistics_with_hashtags_query(params, con, cur):
    changeset_query, _, _ = create_changeset_query(params, con, cur)

    # Include user_id filter.
    changeset_query = f"{changeset_query} AND user_id = {params.user_id}"

    base_query = """
            SELECT (each(osh.tags)).key as feature, osh.action, count(distinct osh.id)
            FROM osm_element_history AS osh, T1
            WHERE osh.timestamp BETWEEN %s AND %s
            AND osh.uid = %s
            AND osh.type in ('way','relation')
            AND T1.changeset_id = osh.changeset
            GROUP BY feature, action
        """
    items = (params.from_timestamp, params.to_timestamp, params.user_id)
    base_query = cur.mogrify(base_query, items).decode()

    query = f"""
            WITH T1 AS (
                {changeset_query}
            )
            {base_query}
        """
    return query


def create_UserStats_get_statistics_query(params, con, cur):
    query = """
            SELECT (each(tags)).key as feature, action, count(distinct id)
            FROM osm_element_history
            WHERE timestamp BETWEEN %s AND %s
            AND uid = %s
            AND type in ('way','relation')
            GROUP BY feature, action
        """

    items = (params.from_timestamp, params.to_timestamp, params.user_id)
    query = cur.mogrify(query, items)
    return query
def create_userstats_get_statistics_with_hashtags_query(params,con,cur):
        hashtag_filter = create_hashtag_filter_query(params.project_ids,
                                                 params.hashtags, cur, con,prefix=True)
        timestamp_filter=create_timestamp_filter_query("created_at",params.from_timestamp, params.to_timestamp,cur,prefix=True)
        query = f"""
        select
            sum(added_buildings)::int as added_buildings,
            sum(modified_buildings)::int as  modified_buildings,
            sum(added_highway)::int as added_highway,
            sum(modified_highway)::int as modified_highway,
            sum(added_highway_meters)::float as added_highway_meters,
            sum(modified_highway_meters)::float as modified_highway_meters
        from
            public.all_changesets_stats s
        join public.osm_changeset c on
            c.id = s.changeset
        where
            {timestamp_filter}
            and c.user_id = {params.user_id} and ({hashtag_filter})"""
        return query

def create_UserStats_get_statistics_query(params,con,cur):
        query = """
        select
            sum(added_buildings)::int as added_buildings,
            sum(modified_buildings)::int as  modified_buildings,
            sum(added_highway)::int as added_highway,
            sum(modified_highway)::int as modified_highway,
            sum(added_highway_meters)::float as added_highway_meters,
            sum(modified_highway_meters)::float as modified_highway_meters
        from
            public.all_changesets_stats s
        join public.osm_changeset c on
            c.id = s.changeset
        where
            c.created_at between %s and %s
            and c.user_id = %s"""
        items = (params.from_timestamp, params.to_timestamp, params.user_id)
        query = cur.mogrify(query, items)
        return query


def create_users_contributions_query(params, changeset_query):
    '''returns user contribution query'''

    project_ids = ",".join([str(p) for p in params.project_ids])
    from_timestamp = params.from_timestamp.isoformat()
    to_timestamp = params.to_timestamp.isoformat()

    query = f"""
    WITH T1 AS({changeset_query}),
    T2 AS (
        SELECT (each(tags)).key AS feature,
            user_id,
            username,
            count(distinct id) AS count
        FROM osm_element_history AS t2, t1
        WHERE t1.changeset_id    = t2.changeset
        GROUP BY feature, user_id, username
    ),
    T3 AS (
        SELECT user_id,
            username,
            SUM(count) AS total_buildings
        FROM T2
        WHERE feature = 'building'
        GROUP BY user_id, username
    )
    SELECT user_id,
        username,
        total_buildings,
        public.editors_per_user(user_id,
        '{from_timestamp}',
        '{to_timestamp}') AS editors
    FROM T3;
    """
    return query


def create_user_tasks_mapped_and_validated_query(project_ids, from_timestamp, to_timestamp):
    tm_project_ids = ",".join([str(p) for p in project_ids])

    mapped_query = f"""
        SELECT th.user_id, COUNT(th.task_id) as tasks_mapped
            FROM PUBLIC.task_history th
            WHERE th.action_text = 'MAPPED'
            AND th.action_date BETWEEN '{from_timestamp}' AND '{to_timestamp}'
            AND th.project_id IN ({tm_project_ids})
            GROUP BY th.user_id;
    """
    validated_query = f"""
        SELECT th.user_id, COUNT(th.task_id) as tasks_validated
            FROM PUBLIC.task_history th
            WHERE th.action_text = 'VALIDATED'
            AND th.action_date BETWEEN '{from_timestamp}' AND '{to_timestamp}'
            AND th.project_id IN ({tm_project_ids})
            GROUP BY th.user_id;
    """
    return mapped_query, validated_query


def create_user_time_spent_mapping_and_validating_query(project_ids, from_timestamp, to_timestamp):
    tm_project_ids = ",".join([str(p) for p in project_ids])

    time_spent_mapping_query = f"""
        SELECT user_id, SUM(CAST(TO_TIMESTAMP(action_text, 'HH24:MI:SS') AS TIME)) AS time_spent_mapping
        FROM public.task_history
        WHERE
            (action = 'LOCKED_FOR_MAPPING'
            OR action = 'AUTO_UNLOCKED_FOR_MAPPING')
            AND action_date BETWEEN '{from_timestamp}' AND '{to_timestamp}'
            AND project_id IN ({tm_project_ids})
        GROUP BY user_id;
    """

    time_spent_validating_query = f"""
        SELECT user_id, SUM(CAST(TO_TIMESTAMP(action_text, 'HH24:MI:SS') AS TIME)) AS time_spent_validating
        FROM public.task_history
        WHERE action = 'LOCKED_FOR_VALIDATION'
            AND action_date BETWEEN '{from_timestamp}' AND '{to_timestamp}'
            AND project_id IN ({tm_project_ids})
        GROUP BY user_id;
    """
    return time_spent_mapping_query, time_spent_validating_query


def generate_data_quality_hashtag_reports(cur, params):
    if params.hashtags is not None and len(params.hashtags) > 0:
        filter_hashtags = ", ".join(["%s"] * len(params.hashtags))
        filter_hashtags = cur.mogrify(
            sql.SQL(filter_hashtags), params.hashtags).decode()
        filter_hashtags = f"AND unnest_hashtags in ({filter_hashtags})"
    else:
        filter_hashtags = ""

    if params.geometry is not None:
        geometry_dump = dumps(dict(params.geometry))
        geom_filter = f"WHERE ST_CONTAINS(ST_GEOMFROMGEOJSON('{geometry_dump}'), location)"
    else:
        geom_filter = ""

    issue_types = ", ".join(["%s"] * len(params.issue_type))
    issue_types_str = [i for i in params.issue_type]
    issue_types = cur.mogrify(sql.SQL(issue_types), issue_types_str).decode()

    timestamp_filter = cur.mogrify(sql.SQL(
        "created_at BETWEEN %s AND %s"), (params.from_timestamp, params.to_timestamp)).decode()

    query = f"""
        WITH t1 AS (SELECT osm_id, change_id, st_x(location) AS lat, st_y(location) AS lon, unnest(status) AS unnest_status from validation {geom_filter}),
        t2 AS (SELECT id, created_at, unnest(hashtags) AS unnest_hashtags from changesets WHERE {timestamp_filter})
        SELECT t1.osm_id,
            t1.change_id as changeset_id,
            t1.lat,
            t1.lon,
            t2.created_at,
            ARRAY_TO_STRING(ARRAY_AGG(t1.unnest_status), ',') AS issues
            FROM t1, t2 WHERE t1.change_id = t2.id
            {filter_hashtags}
            AND unnest_status in ({issue_types})
            GROUP BY t1.osm_id, t1.lat, t1.lon, t2.created_at, t1.change_id;
    """

    return query


def create_hashtagfilter_underpass(hashtags, columnname):
    """Generates hashtag filter query on the basis of list of hastags."""

    hashtag_filters = []
    for i in hashtags:
        if columnname == "username":
            hashtag_filters.append(f"""'{i}'={columnname}""")
        else:
            hashtag_filters.append(f"""'{i}'=ANY({columnname})""")

    join_query = " OR ".join(hashtag_filters)
    returnquery = f"""{join_query}"""

    return returnquery


def generate_data_quality_TM_query(params):
    '''returns data quality TM query with filters and parameteres provided'''
    # print(params)
    hashtag_add_on = "hotosm-project-"
    if "all" in params.issue_types:
        issue_types = ['badvalue', 'badgeom']
    else:
        issue_types = []
        for p in params.issue_types:
            issue_types.append(str(p))

    change_ids = []
    for p in params.project_ids:
        change_ids.append(hashtag_add_on+str(p))

    hashtagfilter = create_hashtagfilter_underpass(change_ids, "hashtags")
    status_filter = create_hashtagfilter_underpass(issue_types, "status")
    '''Geojson output query for pydantic model'''
    # query1 = """
    #     select '{ "type": "Feature","properties": {   "Osm_id": ' || osm_id ||',"Changeset_id":  ' || change_id ||',"Changeset_timestamp": "' || timestamp ||'","Issue_type": "' || cast(status as text) ||'"},"geometry": ' || ST_AsGeoJSON(location)||'}'
    #     FROM validation
    #     WHERE   status IN (%s) AND
    #             change_id IN (%s)
    # """ % (issue_types, change_ids)
    '''Normal Query to feed our OUTPUT Class '''
    query = f"""   with t1 as (
        select id
                From changesets 
                WHERE
                  {hashtagfilter}
            ),
        t2 AS (
             SELECT osm_id as Osm_id,
                change_id as Changeset_id,
                timestamp::text as Changeset_timestamp,
                status::text as Issue_type,
                ST_X(location::geometry) as lng,
                ST_Y(location::geometry) as lat

        FROM validation join t1 on change_id = t1.id
        WHERE
        {status_filter}
                )
        select *
        from t2
        """
    return query


def generate_data_quality_username_query(params, cur):
    '''returns data quality username query with filters and parameteres provided'''
    # print(params)
    if ('all' in params.issue_types) ==False :
        issue_types = ", ".join(["%s"] * len(params.issue_types))
        issue_types_str = [i for i in params.issue_types]
        issue_types = cur.mogrify(sql.SQL(issue_types), issue_types_str).decode()
        issue_type_filter=f"""and unnest_status in ({issue_types})"""   

    else:
        issue_type_filter=f""""""

    if params.hashtags is not None and len(params.hashtags) > 0:
        hashtag_filt=create_hashtagfilter_underpass(params.hashtags,"hashtags")
        filter_hashtags=f""" and {hashtag_filt}"""
    else:
        filter_hashtags = ""
    osm_usernames=[]
    for p in params.osm_usernames:
        osm_usernames.append(p)

    username_filter=create_hashtagfilter_underpass(osm_usernames,"username")
    
    query= f"""with t1 as (
        select
            id,
            username as username
        from
            users
        where
            {username_filter} ),
        t2 as (
        select
            osm_id,
            change_id,
            st_x(location) as lat,
            st_y(location) as lon,
            unnest(status) as unnest_status
        from
            validation,
            t1
        where
            user_id = t1.id),
        t3 as (
        select
            id,
            created_at
        from
            changesets
        where
            (created_at between '{params.from_timestamp}' and  '{params.to_timestamp}'){filter_hashtags} )
        select
            t2.osm_id as Osm_id ,
            t2.change_id as Changeset_id,
            t3.created_at as Changeset_timestamp,
            ARRAY_TO_STRING(ARRAY_AGG(t2.unnest_status), ',') as Issue_type,
            t1.username as username,
            t2.lat,
            t2.lon as lng
        from
            t1,
            t2,
            t3
        where
            t2.change_id = t3.id
            {issue_type_filter}
        group by
            t2.osm_id,
            t1.username,
            t2.lat,
            t2.lon,
            t3.created_at,
            t2.change_id;"""
    # print(query)
    return query


def generate_mapathon_summary_underpass_query(params, cur):
    """Generates mapathon query from underpass"""
    projectid_hashtag_add_on = "hotosm-project-"
    change_ids = []
    for p in params.project_ids:
        change_ids.append(projectid_hashtag_add_on+str(p))

    projectidfilter = create_hashtagfilter_underpass(change_ids, "hashtags")
    hashtags = []
    for p in params.hashtags:
        hashtags.append(str(p))
    hashtagfilter = create_hashtagfilter_underpass(hashtags, "hashtags")
    timestamp_filter = create_timestamp_filter_query(
        "created_at", params.from_timestamp, params.to_timestamp, cur)

    base_where_query = f"""where  ({timestamp_filter}) """
    if hashtagfilter != '' and projectidfilter != '':
        base_where_query += f"""AND ({hashtagfilter} OR {projectidfilter})"""
    elif hashtagfilter == '' and projectidfilter != '':
        base_where_query += f"""AND ({projectidfilter})"""
    else:
        base_where_query += f"""AND ({hashtagfilter})"""
    summary_query = f"""with t1 as (
        select  *
        from changesets
        {base_where_query})
        ,
        t2 as (
        select (each(added)).key as feature , (each(added)).value::Integer as count, 'create'::text as action
        from t1
        union all 
        select  (each(modified)).key as feature , (each(modified)).value::Integer as count, 'modify'::text as action
        from t1
        )
        select feature,action ,sum(count) as count
        from t2
        group by feature ,action 
        order by count desc """
    total_contributor_query = f"""select  COUNT(distinct user_id) as contributors_count
        from changesets
        {base_where_query}
        """
    # print(summary_query)
    # print("\n")

    # print(total_contributor_query)

    return summary_query, total_contributor_query


def generate_training_organisations_query():
    """Generates query for listing out all the organisations listed in training table from underpass
    """
    query = f"""select oid as id ,name
            from organizations
            order by oid """
    return query


def generate_filter_training_query(params):
    base_filter = []

    if params.oid:
        query = f"""(organization = {params.oid})"""
        base_filter.append(query)

    if params.topic_type:
        topic_type_filter = []
        for value in params.topic_type:
            query = f"""topictype = '{value}'"""
            topic_type_filter.append(query)
        join_query = " OR ".join(topic_type_filter)
        base_filter.append(f"""({join_query})""")

    if params.event_type:
        query = f"""(eventtype = '{params.event_type}')"""
        base_filter.append(query)

    if params.from_datestamp and params.to_datestamp:
        timestamp_query = f"""( date BETWEEN '{params.from_datestamp}'::date AND '{params.to_datestamp}'::date )"""
        base_filter.append(timestamp_query)

    if params.from_datestamp != None and params.to_datestamp == None:
        timestamp_query = f"""( date >= '{params.from_datestamp}'::date )"""
        base_filter.append(timestamp_query)

    if params.to_datestamp != None and params.from_datestamp == None:
        timestamp_query = f"""( date <= '{params.to_datestamp}'::date )"""
        base_filter.append(timestamp_query)

    filter_query = " AND ".join(base_filter)
    # print(filter_query)
    return filter_query


def generate_training_query(filter_query):
    base_query = f"""select * from training """
    if filter_query:
        base_query += f"""WHERE {filter_query}"""
    return base_query


def generate_organization_hashtag_reports(cur, params):
    hashtags = []
    for p in params.hashtags:
        hashtags.append("name = '"+str(p.strip()).lower()+"'")
    filter_hashtags = " or ".join(hashtags)
    # filter_hashtags = cur.mogrify(sql.SQL(filter_hashtags), params.hashtags).decode()
    t2_query= f"""select name as hashtag, type as frequency , start_date , end_date , total_new_buildings , total_uq_contributors as total_unique_contributors , total_new_road_m as total_new_road_meters,
            total_new_amenity as total_new_amenities, total_new_places as total_new_places
            from hashtag_stats join t1 on hashtag_id=t1.id
            where type='{params.frequency}'"""
    month_time = f"""0:00:00"""
    week_time = f"""12:00:00"""
    if params.end_date != None or params.start_date != None:
        timestamp = []
        time = f"""{"12" if params.frequency is Frequency.WEEKLY.value else "00" }"""
        if params.start_date:
            timestamp.append(
                f"""start_date >= '{params.start_date}T{time}:00:00.000'::timestamp""")
        if params.end_date:
            timestamp.append(
                f"""end_date <= '{params.end_date}T{time}:00:00.000'::timestamp""")
        filter_timestamp = " and ".join(timestamp)
        t2_query += f""" and {filter_timestamp}"""
    query = f"""with t1 as (
            select id, name
            from hashtag
            where {filter_hashtags}
            ),
            t2 as (
                {t2_query}
            )
            select * 
            from t2
            order by hashtag"""
    # print(query)
    return query

def generate_tm_validators_stats_query(cur, params):
    stmt = """with t0 as (
        select
            id as p_id,
            case
                when status = 0
                        then 'ARCHIVED'
                when status = 1
                        then 'PUBLISHED'
                when status = 2 then 'DRAFT'
            end status,
            total_tasks,
            tasks_mapped,
            tasks_validated,
            organisation_id,
            country
        from projects
        where date_part('year', created) = %s"""

    sub_query = cur.mogrify(sql.SQL(stmt), (params.year,)).decode()
    status_subset=""
    organisation_subset=""
    if params.status :
        status_subset=f""" and status ={params.status}""" 
    if params.organisation:
        organisation_list=[f"""organisation_id = {id}""" for id in params.organisation]
        organisation_join = " or ".join(organisation_list)
        organisation_subset=f""" and ({organisation_join})"""
    query = f"""
    {sub_query}{status_subset}{organisation_subset}
        order by p_id
            )
    ,t1 as (
        select
            user_id,
            project_id,
            count(id) as cnt
        from
            task_history,
            t0
        where
            project_id = t0.p_id
            and action_text = 'VALIDATED'
            and "action" = 'STATE_CHANGE'
        group by
            user_id,
            project_id,
            action_text
        order by
            project_id
            )
    select
        coalesce(t1.user_id, 0) as user_id,
        coalesce(u.username, 'N/A') as username,
        p.p_id as project_id,
        coalesce(t1.cnt, 0) as cnt,
        p.status as project_status,
        coalesce(o.name,'N/A') as organisation_name,
        p.total_tasks,
        p.tasks_mapped,
        p.tasks_validated,
        unnest(p.country) as country
    from
        t0 as p
    left join t1
        on
        t1.project_id = p.p_id
    left join users as u
        on
        u.id = t1.user_id
    left join organisations as o
        on
        o.id = p.organisation_id
    order by
        u.username,
        t1.project_id"""

    return query


def generate_tm_teams_list():
    query = """with vt AS (SELECT distinct team_id as id from project_teams where role = 1 order by id),
            mu AS (SELECT tm.team_id, ARRAY_AGG(users.username) AS managers from team_members AS tm, vt, users WHERE users.id = tm.user_id AND tm.team_id = vt.id AND tm.function = 1 GROUP BY tm.team_id),
            uc AS (SELECT tm.team_id, count(tm.user_id) AS members_count from team_members AS tm, vt WHERE tm.team_id = vt.id GROUP BY tm.team_id)
            SELECT t.id, t.organisation_id, orgs.name AS organisation_name, t.name AS team_name, mu.managers, uc.members_count from teams AS t, mu, uc, organisations AS orgs where orgs.id = t.organisation_id AND t.id = mu.team_id AND t.id = uc.team_id"""

    return query


def generate_list_teams_metadata():
    query = """
        with vt AS (SELECT distinct team_id as id from project_teams where role = 1 order by id),
        m AS (SELECT tm.team_id, tm.user_id, users.username, tm.function FROM team_members AS tm, vt, users WHERE users.id = tm.user_id AND tm.team_id = vt.id)
        SELECT m.team_id AS team_id,
            t.name AS team_name,
            orgs.id AS organisation_id,
            orgs.name AS organisation_name,
            m.user_id,
            m.username,
            m.function from m, teams as t, organisations as orgs
        where
            orgs.id = t.organisation_id AND
            t.id = m.team_id
        ORDER BY team_id, function, username;
    """

    return query

def raw_historical_data_extraction_query(cur,conn,params):
    geometry_dump = dumps(dict(params.geometry))
    geom_filter = f"ST_intersects(ST_GEOMFROMGEOJSON('{geometry_dump}'), geom)"
    timestamp_filter = cur.mogrify(sql.SQL(
        "created_at BETWEEN %s AND %s"), (params.from_timestamp, params.to_timestamp)).decode()
    t1 = f"""select
        id as changeset_id
    from
        osm_changeset
    where
        {geom_filter}
        and ({timestamp_filter})"""
    if params.hashtags:
        hashtag_filter = create_hashtag_filter_query(
            "", params.hashtags, cur, conn)
        t1 += f"""and ({hashtag_filter})"""
    query = f"""with t1 as(
            {t1}
        ),
        t2 as (
        select
            *,
            case
                when oeh.nds is not null then ST_AsGeoJSON(public.construct_geometry(oeh.nds,
                oeh.id,
                oeh."timestamp"))
                else ST_AsGeoJSON(ST_MakePoint(oeh.lon,oeh.lat))
            end as geometry
        from
            osm_element_history oeh,
            t1
        where
            oeh.changeset = t1.changeset_id
	        and oeh."action" != 'delete'
            and oeh."type" != 'relation'
         	and oeh.version = (
                select
                    max("version")
                from
                    public.osm_element_history i
                where
                    i.id = oeh.id and i.type = oeh.type
                    and i."timestamp"< '{params.to_timestamp}'::timestamptz )  
            )
        select
            t2.id,
            t2."type",
            t2.tags::text as tags,
            t2.changeset as changeset_id,
            t2."timestamp"::text as created_at,
            t2.uid as user_id,
            t2."version" ,
            t2."action" ,
            t2.grid ,
            t2.geometry
        from
            t2"""
    if params.geometry_type:
        geometry_type = []
        for p in params.geometry_type:
            geometry_type.append(f"""t2.tags?'{p}'""")
        filter_geometry_type = " or ".join(geometry_type)
        query += f"""
        where
            {filter_geometry_type}"""
    # print(query)
    return query


# Rawdata extraction Block

def get_grid_id_query(geometry_dump):

    base_query = f"""select
                        b.poly_id
                    from
                        grid b
                    where
                        ST_Intersects(ST_GEOMFROMGEOJSON('{geometry_dump}') ,
                        b.geom)"""
    return base_query


def get_query_as_geojson(query_list,ogr_export=None):
    table_base_query = []
    if ogr_export:
        table_base_query=query_list
    else:
        for i in range(len(query_list)):
            table_base_query.append(
                f"""select ST_AsGeoJSON(t{i}.*) from ({query_list[i]}) t{i}""")
    final_query = " UNION ALL ".join(table_base_query)
    return final_query


def create_geom_filter(geom):
    """generates geometry intersection filter - Rawdata extraction"""
    geometry_dump = dumps(dict(geom))
    return f"""ST_intersects(ST_GEOMFROMGEOJSON('{geometry_dump}'), geom)"""

def format_file_name_str(input_str):
    # Fixme I need to check every possible special character that can comeup on osm tags
    input_str=re.sub("\s+", "-", input_str) # putting - in every space
    input_str=re.sub(":", "-", input_str) # putting - in every : value
    input_str=re.sub("_", "-", input_str) # putting - in every _ value

    return input_str

def remove_spaces(input_str):
    # Fixme I need to check every possible special character that can comeup on osm tags
    input_str=re.sub("\s+", "_", input_str) # putting _ in every space
    input_str=re.sub(":", "_", input_str) # putting _ in every : value
    return input_str


def create_column_filter(columns, create_schema=False):
    """generates column filter , which will be used to filter column in output will be used on select query - Rawdata extraction"""
    if len(columns) > 0:
        filter_col = []
        filter_col.append('osm_id')
        if create_schema:
            schema = {}
            schema['osm_id'] = 'int64'
        for cl in columns:
            if cl != '':
                filter_col.append(
                    f"""tags ->> '{cl.strip()}' as {remove_spaces(cl.strip())}""")
                if create_schema:
                    schema[remove_spaces(cl.strip())] = 'str'
        filter_col.append('geom')
        select_condition = " , ".join(filter_col)
        if create_schema:
            return select_condition, schema
        return select_condition
    else:
        return f"""osm_id ,tags::text as tags,changeset,timestamp::text,geom"""  # this is default attribute that we will deliver to user if user defines his own attribute column then those will be appended with osm_id only


def generate_tag_filter_query(filter):
        incoming_filter = []
        for key, value in filter.items():

            if len(value) > 1:
                v_l = []
                for l in value:
                    v_l.append(f""" '{l.strip()}' """)
                v_l_join = " , ".join(v_l)
                value_tuple = f"""({v_l_join})"""

                k = f""" '{key.strip()}' """
                incoming_filter.append(
                    """tags ->> """+k+"""IN """+value_tuple+"""""")
            elif len(value) == 1:
                incoming_filter.append(
                    f"""tags ->> '{key.strip()}' = '{value[0].strip()}'""")
            else:
                incoming_filter.append(f"""tags ? '{key.strip()}'""")
        tag_filter = " OR ".join(incoming_filter)
        return tag_filter


def extract_geometry_type_query(params,ogr_export=False):
    """used for specifically focused on export tool , this will generate separate queries for line point and polygon can be used on other datatype support - Rawdata extraction"""

    geom_filter = create_geom_filter(params.geometry)
    select_condition = f"""osm_id ,tags::text as tags,changeset,timestamp::text,geom"""  # this is default attribute that we will deliver to user if user defines his own attribute column then those will be appended with osm_id only
    schema = {'osm_id': 'int64', 'tags': 'str',
              'changeset': 'int64', 'timestamp': 'str'}
    query_point, query_line, query_poly = None, None, None
    attribute_filter,master_attribute_filter,master_tag_filter,poly_attribute_filter,poly_tag_filter = None,None,None,None,None 
    point_schema, line_schema, poly_schema = None, None, None
    tags,attributes,point_attribute_filter,line_attribute_filter,poly_attribute_filter,master_attribute_filter,point_tag_filter,line_tag_filter,poly_tag_filter,master_tag_filter=None,None,None,None,None,None,None,None,None,None
    if params.filters:
        tags,attributes,point_attribute_filter,line_attribute_filter,poly_attribute_filter,master_attribute_filter,point_tag_filter,line_tag_filter,poly_tag_filter,master_tag_filter=extract_attributes_tags(params.filters)

    if master_attribute_filter:  # if no specific point , line or poly filter is not passed master columns filter will be used , if master columns is also empty then above default select statement will be used
        select_condition, schema = create_column_filter(
            master_attribute_filter, create_schema=True)
    if master_tag_filter :
        attribute_filter = generate_tag_filter_query(master_tag_filter)
    if params.geometry_type is None : # fix me 
        params.geometry_type=['point', 'line', 'polygon']

    for type in params.geometry_type:
        if type == SupportedGeometryFilters.POINT.value:
            if point_attribute_filter:
                select_condition, schema = create_column_filter(
                    point_attribute_filter, create_schema=True)
            query_point = f"""select
                        {select_condition}
                        from
                            nodes
                        where
                            {geom_filter}"""
            if point_tag_filter:
                attribute_filter = generate_tag_filter_query(point_tag_filter)
            if attribute_filter:
                query_point += f""" and ({attribute_filter})"""
            point_schema = schema

            query_point = get_query_as_geojson([query_point],ogr_export=ogr_export)

        if type == SupportedGeometryFilters.LINE.value:
            query_line_list = []
            if line_attribute_filter:
                select_condition, schema = create_column_filter(
                    line_attribute_filter, create_schema=True)
            query_ways_line = f"""select
                {select_condition}
                from
                    ways_line
                where
                    {geom_filter}"""
            query_relations_line = f"""select
                {select_condition}
                from
                    relations
                where
                    {geom_filter}"""
            if line_tag_filter:
                attribute_filter = generate_tag_filter_query(line_tag_filter)
            if attribute_filter:
                query_ways_line += f""" and ({attribute_filter})"""
                query_relations_line += f""" and ({attribute_filter})"""
            query_relations_line += f""" and (geometrytype(geom)='MULTILINESTRING')"""
            query_line_list.append(query_ways_line)
            query_line_list.append(query_relations_line)
            query_line = get_query_as_geojson(query_line_list,ogr_export=ogr_export)
            line_schema = schema

        if type == SupportedGeometryFilters.POLYGON.value:
            query_poly_list = []
            if poly_attribute_filter:
                select_condition, schema = create_column_filter(
                    poly_attribute_filter, create_schema=True)
            query_ways_poly = f"""select
                {select_condition}
                from
                    ways_poly
                where
                    {geom_filter}"""
            query_relations_poly = f"""select
                {select_condition}
                from
                    relations
                where
                    {geom_filter}"""
            if poly_tag_filter:
                attribute_filter = generate_tag_filter_query(poly_tag_filter)
            if attribute_filter:
                query_ways_poly += f""" and ({attribute_filter})"""
                query_relations_poly += f""" and ({attribute_filter})"""
            query_relations_poly += f""" and (geometrytype(geom)='POLYGON' or geometrytype(geom)='MULTIPOLYGON')"""
            query_poly_list.append(query_ways_poly)
            query_poly_list.append(query_relations_poly)
            query_poly = get_query_as_geojson(query_poly_list,ogr_export=ogr_export)
            poly_schema = schema
    return query_point, query_line, query_poly, point_schema, line_schema, poly_schema

def extract_attributes_tags(filters):
    tags = None
    attributes = None 
    point_tag_filter = None
    poly_tag_filter= None
    line_tag_filter = None
    master_tag_filter= None
    point_attribute_filter=None
    poly_attribute_filter= None
    line_attribute_filter=None
    master_attribute_filter=None
    if filters :
        for key,value in filters.items():
            if key == SupportedFilters.TAGS.value:
                if value :
                    tags=value
                    for k,v in value.items() :
                        if k ==SupportedGeometryFilters.POINT.value:
                            point_tag_filter=v
                        if k == SupportedGeometryFilters.LINE.value:
                            line_tag_filter=v
                        if k == SupportedGeometryFilters.POLYGON.value:
                            poly_tag_filter = v
                        if k == SupportedGeometryFilters.ALLGEOM.value:
                            master_tag_filter=v
            if key == SupportedFilters.ATTRIBUTES.value:
                if value :
                    attributes=value
                    for k,v in value.items():
                        if k ==SupportedGeometryFilters.POINT.value:
                            point_attribute_filter=v
                        if k == SupportedGeometryFilters.LINE.value:
                            line_attribute_filter=v
                        if k == SupportedGeometryFilters.POLYGON.value:
                            poly_attribute_filter = v
                        if k == SupportedGeometryFilters.ALLGEOM.value:
                            master_attribute_filter=v
        
    return tags,attributes,point_attribute_filter,line_attribute_filter,poly_attribute_filter,master_attribute_filter,point_tag_filter,line_tag_filter,poly_tag_filter,master_tag_filter


def raw_currentdata_extraction_query(params, g_id, geometry_dump, ogr_export=False,select_all=False):
    """Default function to support current snapshot extraction with all of the feature that galaxy has"""
    geom_filter = f"""ST_intersects(ST_GEOMFROMGEOJSON('{geometry_dump}'), geom)"""
    base_query = []
    
    tags,attributes,point_attribute_filter,line_attribute_filter,poly_attribute_filter,master_attribute_filter,point_tag_filter,line_tag_filter,poly_tag_filter,master_tag_filter=None,None,None,None,None,None,None,None,None,None

    point_select_condition=None
    line_select_condition=None
    poly_select_condition=None 

    point_tag=None
    line_tag=None
    poly_tag=None
    master_tag=None
    use_geomtype_in_relation=True


    query_table=[]
    if select_all:
        select_condition = """osm_id,version,tags::text as tags,changeset,timestamp::text,geom""" #FIXme have condition for displaying userinfo after user authentication 
    else:    
        select_condition = """osm_id ,version,tags::text as tags,changeset,timestamp::text,geom"""  # this is default attribute that we will deliver to user if user defines his own attribute column then those will be appended with osm_id only
    point_select_condition=select_condition #initializing default
    line_select_condition=select_condition
    poly_select_condition=select_condition

    if params.filters :
        tags,attributes,point_attribute_filter,line_attribute_filter,poly_attribute_filter,master_attribute_filter,point_tag_filter,line_tag_filter,poly_tag_filter,master_tag_filter=extract_attributes_tags(params.filters)
    if attributes:
        if master_attribute_filter :
            if len(master_attribute_filter) > 0:
                select_condition=create_column_filter(master_attribute_filter)
                point_select_condition=select_condition # if master attribute is supplied it will be applied to other geom type as well even though value is supplied they will be ignored
                line_select_condition=select_condition
                poly_select_condition=select_condition
        else :
            if point_attribute_filter:
                if len(point_attribute_filter)>0:
                    point_select_condition=create_column_filter(point_attribute_filter)           
            if line_attribute_filter:
                if len(line_attribute_filter)>0:
                    line_select_condition=create_column_filter(line_attribute_filter)
            if poly_attribute_filter:
                if len(line_attribute_filter)>0:
                    poly_select_condition=create_column_filter(point_attribute_filter)
    if tags:
        if master_tag_filter: # if master tag is supplied then other tags should be ignored and master tag will be used
            master_tag=generate_tag_filter_query(master_tag_filter)
            point_tag=master_tag
            line_tag=master_tag
            poly_tag=master_tag
        else:
            if point_tag_filter:
                point_tag=generate_tag_filter_query(point_tag_filter)
            if line_tag_filter:
                line_tag=generate_tag_filter_query(line_tag_filter)
            if poly_tag_filter:
                poly_tag=generate_tag_filter_query(poly_tag_filter)

# condition for geometry types 
    if params.geometry_type is None : 
        params.geometry_type=["point","line","polygon"]
    if SupportedGeometryFilters.ALLGEOM.value in params.geometry_type:
        params.geometry_type=["point","line","polygon"]
    if SupportedGeometryFilters.POINT.value in params.geometry_type :
        query_point = f"""select
                    {point_select_condition}
                    from
                        nodes
                    where
                        {geom_filter}"""
        if point_tag:
            query_point += f""" and ({point_tag})"""
        base_query.append(query_point)

    if SupportedGeometryFilters.LINE.value in params.geometry_type:
        query_ways_line = f"""select
            {line_select_condition}
            from
                ways_line
            where
                {geom_filter}"""
        if line_tag:
            query_ways_line += f""" and ({line_tag})"""
        base_query.append(query_ways_line)

        if SupportedGeometryFilters.POLYGON.value in params.geometry_type:
            if poly_select_condition == line_select_condition and poly_tag == line_tag :
                use_geomtype_in_relation=False
                    
        if use_geomtype_in_relation:
            query_relations_line = f"""select
                {line_select_condition}
                from
                    relations
                where
                    {geom_filter}"""
            if line_tag:
                query_relations_line += f""" and ({line_tag})"""
            query_relations_line += f""" and (geometrytype(geom)='MULTILINESTRING')""" 
            base_query.append(query_relations_line)
    
    if SupportedGeometryFilters.POLYGON.value in params.geometry_type:
        if g_id:
            grid_filter_base = [
                f"""grid = {ind[0]}""" for ind in g_id]
            grid_filter = " OR ".join(grid_filter_base)
            where_clause = f"""({grid_filter}) and {geom_filter}"""
        else:
            where_clause = f"""{geom_filter}"""
        query_ways_poly = f"""select
            {poly_select_condition}
            from
                ways_poly
            where
                {where_clause}"""
        if poly_tag :
            query_ways_poly += f""" and ({poly_tag})"""
        base_query.append(query_ways_poly)
        
        
        query_relations_poly = f"""select
            {select_condition}
            from
                relations
            where
                {geom_filter}"""
        if poly_tag:
            query_relations_poly += f""" and ({poly_tag})"""
        if use_geomtype_in_relation:
            query_relations_poly += f""" and (geometrytype(geom)='POLYGON' or geometrytype(geom)='MULTIPOLYGON')"""
        base_query.append(query_relations_poly)

    if ogr_export:
        # since query will be different for ogr exports and geojson exports because for ogr exports we don't need to grab each row in geojson
        table_base_query = base_query
    else:
        table_base_query = []
        for i in range(len(base_query)):
            table_base_query.append(
                f"""select ST_AsGeoJSON(t{i}.*) from ({base_query[i]}) t{i}""")
    final_query = " UNION ALL ".join(table_base_query)
    return final_query         

def check_last_updated_rawdata():
    query = f"""select NOW()-importdate as last_updated from planet_osm_replication_status"""
    return query
    
