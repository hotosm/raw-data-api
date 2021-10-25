from psycopg2 import sql

HSTORE_COLUMN = "tags"


def create_hashtag_filter_query(project_ids, hashtags, cur, conn):
    merged_items = [*project_ids, *hashtags]

    filter_query = "({hstore_column} -> %s) ~~ %s"

    hashtag_filter_values = [
        *[f"%hotosm-project-{i} %" for i in project_ids],
        *[f"%{i} %" for i in hashtags],
    ]
    hashtag_tags_filters = [
        cur.mogrify(filter_query, ("hashtags", i)).decode()
        for i in hashtag_filter_values
    ]

    comment_filter_values = [
        *[f"%hotosm-project-{i};%" for i in project_ids],
        *[f"%{i};%" for i in hashtags],
    ]
    comment_tags_filters = [
        cur.mogrify(filter_query, ("comment", i)).decode()
        for i in comment_filter_values
    ]

    hashtag_filter = [*hashtag_tags_filters, *comment_tags_filters]

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
