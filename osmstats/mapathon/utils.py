from psycopg2 import sql


HSTORE_COLUMN = "tags"


def create_hashtag_filter_query(project_ids, hashtags, cur, conn):
    hstore_keys = ["hashtags", "comment"]
    hashtag_filter_values = [
        *[f"%hotosm-project-{i}%" for i in project_ids],
        *[f"%{h}%" for h in hashtags],
    ]

    hashtag_filter_query = "({hstore_column} -> %s) ~~ %s"
    hashtag_filter = [
        [
            cur.mogrify(hashtag_filter_query, (h, i)).decode()
            for h in hstore_keys
        ]
        for i in hashtag_filter_values
    ]

    # Flatten.
    hashtag_filter = [item for sublist in hashtag_filter for item in sublist]

    hashtag_filter = [
        sql.SQL(f).format(hstore_column=sql.Identifier(HSTORE_COLUMN))
        for f in hashtag_filter
    ]

    hashtag_filter = sql.SQL(" OR ").join(hashtag_filter).as_string(conn)

    return hashtag_filter


def create_timestamp_filter_query(from_timestamp, to_timestamp, cur):
    timestamp_column = "created_at"
    # Subquery to filter changesets matching hashtag and dates.
    timestamp_filter = sql.SQL("{timestamp_column} between %s AND %s").format(
        timestamp_column=sql.Identifier(timestamp_column)
    )
    timestamp_filter = cur.mogrify(
        timestamp_filter, (from_timestamp, to_timestamp)
    ).decode()

    return timestamp_filter


def create_changeset_query(params, conn, cur):
    hashtag_filter = create_hashtag_filter_query(
        params.project_ids, params.hashtags, cur, conn
    )
    timestamp_filter = create_timestamp_filter_query(
        params.from_timestamp, params.to_timestamp, cur
    )

    changeset_query = f"""
    SELECT user_id, id as changeset_id, user_name as username
    FROM osm_changeset
    WHERE {timestamp_filter} AND ({hashtag_filter})
    """

    return changeset_query, hashtag_filter, timestamp_filter


def create_osm_history_query(changeset_query, with_username):
    column_names = [
        f"(each({HSTORE_COLUMN})).key AS feature",
        "action",
        "count(distinct id) AS count",
    ]
    group_by_names = ["feature", "action"]

    if with_username is True:
        column_names.append("username")
        group_by_names.extend(["user_id", "username"])

    order_by = (
        ["count DESC"]
        if with_username is False
        else ["user_id", "action", "count"]
    )
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


def create_users_contributions_query(params, changeset_query):
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
        public.tasks_per_user(user_id,
            '{project_ids}',
            '{from_timestamp}',
            '{to_timestamp}',
            'MAPPED') AS mapped_tasks,
        public.tasks_per_user(user_id,
            '{project_ids}',
            '{from_timestamp}',
            '{to_timestamp}',
            'VALIDATED') AS validated_tasks,
        public.editors_per_user(user_id,
            '{from_timestamp}',
            '{to_timestamp}') AS editors
    FROM T3;
    """
    return query
