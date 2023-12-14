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
"""Page Contains Query logic required for application"""
import re
from json import dumps

from src.config import logger as logging
from src.validation.models import SupportedFilters, SupportedGeometryFilters


def get_grid_id_query(geometry_dump):
    base_query = f"""select
                        b.poly_id
                    from
                        grid b
                    where
                        ST_Intersects(ST_GEOMFROMGEOJSON('{geometry_dump}') ,
                        b.geom)"""
    return base_query


def get_country_id_query(geom_dump):
    base_query = f"""select
                        b.cid::int as fid
                    from
                        countries b
                    where
                        ST_Intersects(ST_GEOMFROMGEOJSON('{geom_dump}') ,
                        b.geometry)
                    order by ST_Area(ST_Intersection(b.geometry,ST_MakeValid(ST_GEOMFROMGEOJSON('{geom_dump}')))) desc

                    """
    return base_query


def check_exisiting_country(geom):
    query = f"""select
                        b.cid::int as fid
                    from
                        countries b
                    where
                        ST_Equals(ST_SnapToGrid(ST_GEOMFROMGEOJSON('{geom}'),0.00001) ,
                        ST_SnapToGrid(b.geometry,0.00001))
                    """
    return query


def get_query_as_geojson(query_list, ogr_export=None):
    table_base_query = []
    if ogr_export:
        table_base_query = query_list
    else:
        for i in range(len(query_list)):
            table_base_query.append(
                f"""select ST_AsGeoJSON(t{i}.*) from ({query_list[i]}) t{i}"""
            )
    final_query = " UNION ALL ".join(table_base_query)
    return final_query


def create_geom_filter(geom, geom_lookup_by="ST_intersects"):
    """generates geometry intersection filter - Rawdata extraction"""
    geometry_dump = dumps(dict(geom))
    return f"""{geom_lookup_by}(geom,ST_GEOMFROMGEOJSON('{geometry_dump}'))"""


def format_file_name_str(input_str):
    # Fixme I need to check every possible special character that can comeup on osm tags
    input_str = re.sub("\s+", "_", input_str)  # putting _ in every space  # noqa
    input_str = re.sub(":", "_", input_str)  # putting _ in every : value
    input_str = re.sub("-", "_", input_str)  # putting _ in every - value

    return input_str


def remove_spaces(input_str):
    # Fixme I need to check every possible special character that can comeup on osm tags
    input_str = re.sub("\s+", "_", input_str)  # putting _ in every space # noqa
    input_str = re.sub(":", "_", input_str)  # putting _ in every : value
    return input_str


def create_column_filter(
    columns, create_schema=False, output_type="geojson", use_centroid=False
):
    """generates column filter , which will be used to filter column in output will be used on select query - Rawdata extraction"""

    if len(columns) > 0:
        filter_col = []
        filter_col.append("osm_id")
        if create_schema:
            schema = {}
            schema["osm_id"] = "int64"
        for cl in columns:
            splitted_cl = [cl]
            if "," in cl:
                splitted_cl = cl.split(",")
            for cl in splitted_cl:
                if cl != "":
                    filter_col.append(
                        f"""tags ->> '{cl.strip()}' as {remove_spaces(cl.strip())}"""
                    )
                    if create_schema:
                        schema[remove_spaces(cl.strip())] = "str"
        if output_type == "csv":  # if it is csv geom logic is different
            filter_col.append("ST_X(ST_Centroid(geom)) as longitude")
            filter_col.append("ST_Y(ST_Centroid(geom)) as latitude")
            filter_col.append("GeometryType(geom) as geom_type")

        else:
            filter_col.append("ST_Centroid(geom) as geom" if use_centroid else "geom")
        select_condition = " , ".join(filter_col)
        if create_schema:
            return select_condition, schema
        return select_condition
    else:
        return f"osm_id ,tags,changeset,timestamp,{'ST_Centroid(geom) as geom' if use_centroid else 'geom'}"  # this is default attribute that we will deliver to user if user defines his own attribute column then those will be appended with osm_id only


def create_tag_sql_logic(key, value, filter_list):
    if len(value) > 1:
        v_l = []
        for lil in value:
            v_l.append(f""" '{lil.strip()}' """)
        v_l_join = ", ".join(v_l)
        value_tuple = f"""({v_l_join})"""

        k = f""" '{key.strip()}' """
        filter_list.append("""tags ->> """ + k + """IN """ + value_tuple + """""")
    elif len(value) == 1:
        filter_list.append(f"""tags ->> '{key.strip()}' = '{value[0].strip()}'""")
    else:
        filter_list.append(f"""tags ? '{key.strip()}'""")
    return filter_list


def generate_tag_filter_query(filter, join_by=" OR ", plain_query_filter=False):
    final_filter = []
    if plain_query_filter:
        for item in filter:
            key = item["key"]
            value = item["value"]
            if len(value) == 1 and value[0] == "*":
                value = []
            if len(value) >= 1:
                sub_append = []
                pre = """ tags @> '{"""
                post = """ }'"""
                for v in value:
                    sub_append.append(
                        f"""{pre} "{key.strip()}" : "{v.strip()}" {post}"""
                    )
                sub_append_join = " OR ".join(sub_append)

                final_filter.append(f"({sub_append_join})")
            else:
                final_filter.append(f"""tags ? '{key.strip()}'""")
        tag_filter = join_by.join(final_filter)
        return tag_filter

    else:
        for key, value in filter.items():
            if key == "join_or":
                temp_logic = []
                if value:
                    for k, v in value.items():
                        temp_logic = create_tag_sql_logic(k, v, temp_logic)
                    final_filter.append(f"""{" OR ".join(temp_logic)}""")

            if key == "join_and":
                temp_logic = []
                if value:
                    for k, v in value.items():
                        temp_logic = create_tag_sql_logic(k, v, temp_logic)
                    if len(temp_logic) == 1:
                        join_by = " AND "
                    final_filter.append(f"""{" AND ".join(temp_logic)}""")

        tag_filter = join_by.join(final_filter)
        return tag_filter


def extract_geometry_type_query(
    params, ogr_export=False, g_id=None, c_id=None, country_export=False
):
    """used for specifically focused on export tool , this will generate separate queries for line point and polygon can be used on other datatype support - Rawdata extraction"""

    geom_filter = create_geom_filter(
        params.geometry,
        "ST_within" if params.use_st_within is True else "ST_intersects",
    )
    select_condition = f"""osm_id ,tags,changeset,timestamp , {'ST_Centroid(geom) as geom' if params.centroid else 'geom'}"""  # this is default attribute that we will deliver to user if user defines his own attribute column then those will be appended with osm_id only
    schema = {
        "osm_id": "int64",
        "tags": "str",
        "changeset": "int64",
        "timestamp": "str",
    }
    query_point, query_line, query_poly = None, None, None
    (
        attribute_filter,
        master_attribute_filter,
        master_tag_filter,
        poly_attribute_filter,
        poly_tag_filter,
    ) = (None, None, None, None, None)
    point_schema, line_schema, poly_schema = None, None, None
    (
        tags,
        attributes,
        point_attribute_filter,
        line_attribute_filter,
        poly_attribute_filter,
        master_attribute_filter,
        point_tag_filter,
        line_tag_filter,
        poly_tag_filter,
        master_tag_filter,
    ) = (None, None, None, None, None, None, None, None, None, None)
    if params.filters:
        params.filters = (
            params.filters.dict()
        )  # FIXME: temp fix , since validation model got changed
        (
            tags,
            attributes,
            point_attribute_filter,
            line_attribute_filter,
            poly_attribute_filter,
            master_attribute_filter,
            point_tag_filter,
            line_tag_filter,
            poly_tag_filter,
            master_tag_filter,
        ) = extract_attributes_tags(params.filters)

    if (
        master_attribute_filter
    ):  # if no specific point , line or poly filter is not passed master columns filter will be used , if master columns is also empty then above default select statement will be used
        select_condition, schema = create_column_filter(
            use_centroid=params.centroid,
            output_type=params.output_type,
            columns=master_attribute_filter,
            create_schema=True,
        )
    if master_tag_filter:
        attribute_filter = generate_tag_filter_query(master_tag_filter)
    if params.geometry_type is None:  # fix me
        params.geometry_type = ["point", "line", "polygon"]

    for type in params.geometry_type:
        if type == SupportedGeometryFilters.POINT.value:
            if point_attribute_filter:
                select_condition, schema = create_column_filter(
                    use_centroid=params.centroid,
                    output_type=params.output_type,
                    columns=point_attribute_filter,
                    create_schema=True,
                )
            where_clause_for_nodes = generate_where_clause_indexes_case(
                geom_filter, g_id, c_id, country_export, "nodes"
            )

            query_point = f"""select
                        {select_condition}
                        from
                            nodes
                        where
                            {where_clause_for_nodes}"""
            if point_tag_filter:
                attribute_filter = generate_tag_filter_query(point_tag_filter)
            if attribute_filter:
                query_point += f""" and ({attribute_filter})"""
            point_schema = schema

            query_point = get_query_as_geojson([query_point], ogr_export=ogr_export)

        if type == SupportedGeometryFilters.LINE.value:
            query_line_list = []
            if line_attribute_filter:
                select_condition, schema = create_column_filter(
                    use_centroid=params.centroid,
                    output_type=params.output_type,
                    columns=line_attribute_filter,
                    create_schema=True,
                )
            where_clause_for_line = generate_where_clause_indexes_case(
                geom_filter, g_id, c_id, country_export, "ways_line"
            )

            query_ways_line = f"""select
                {select_condition}
                from
                    ways_line
                where
                    {where_clause_for_line}"""
            where_clause_for_rel = generate_where_clause_indexes_case(
                geom_filter, g_id, c_id, country_export, "relations"
            )

            query_relations_line = f"""select
                {select_condition}
                from
                    relations
                where
                    {where_clause_for_rel}"""
            if line_tag_filter:
                attribute_filter = generate_tag_filter_query(line_tag_filter)
            if attribute_filter:
                query_ways_line += f""" and ({attribute_filter})"""
                query_relations_line += f""" and ({attribute_filter})"""
            query_relations_line += """ and (geometrytype(geom)='MULTILINESTRING')"""
            query_line_list.append(query_ways_line)
            query_line_list.append(query_relations_line)
            query_line = get_query_as_geojson(query_line_list, ogr_export=ogr_export)
            line_schema = schema

        if type == SupportedGeometryFilters.POLYGON.value:
            query_poly_list = []
            if poly_attribute_filter:
                select_condition, schema = create_column_filter(
                    use_centroid=params.centroid,
                    output_type=params.output_type,
                    columns=poly_attribute_filter,
                    create_schema=True,
                )

            where_clause_for_poly = generate_where_clause_indexes_case(
                geom_filter, g_id, c_id, country_export, "ways_poly"
            )

            query_ways_poly = f"""select
                {select_condition}
                from
                    ways_poly
                where
                    {where_clause_for_poly}"""
            where_clause_for_relations = generate_where_clause_indexes_case(
                geom_filter, g_id, c_id, country_export, "relations"
            )

            query_relations_poly = f"""select
                {select_condition}
                from
                    relations
                where
                    {where_clause_for_relations}"""
            if poly_tag_filter:
                attribute_filter = generate_tag_filter_query(poly_tag_filter)
            if attribute_filter:
                query_ways_poly += f""" and ({attribute_filter})"""
                query_relations_poly += f""" and ({attribute_filter})"""
            query_relations_poly += """ and (geometrytype(geom)='POLYGON' or geometrytype(geom)='MULTIPOLYGON')"""
            query_poly_list.append(query_ways_poly)
            query_poly_list.append(query_relations_poly)
            query_poly = get_query_as_geojson(query_poly_list, ogr_export=ogr_export)
            poly_schema = schema
    return query_point, query_line, query_poly, point_schema, line_schema, poly_schema


def extract_attributes_tags(filters):
    tags = None
    attributes = None
    point_tag_filter = None
    poly_tag_filter = None
    line_tag_filter = None
    master_tag_filter = None
    point_attribute_filter = None
    poly_attribute_filter = None
    line_attribute_filter = None
    master_attribute_filter = None
    if filters:
        for key, value in filters.items():
            if key == SupportedFilters.TAGS.value:
                if value:
                    tags = value
                    for k, v in value.items():
                        if k == SupportedGeometryFilters.POINT.value:
                            point_tag_filter = v
                        if k == SupportedGeometryFilters.LINE.value:
                            line_tag_filter = v
                        if k == SupportedGeometryFilters.POLYGON.value:
                            poly_tag_filter = v
                        if k == SupportedGeometryFilters.ALLGEOM.value:
                            master_tag_filter = v
            if key == SupportedFilters.ATTRIBUTES.value:
                if value:
                    attributes = value
                    for k, v in value.items():
                        if k == SupportedGeometryFilters.POINT.value:
                            point_attribute_filter = v
                        if k == SupportedGeometryFilters.LINE.value:
                            line_attribute_filter = v
                        if k == SupportedGeometryFilters.POLYGON.value:
                            poly_attribute_filter = v
                        if k == SupportedGeometryFilters.ALLGEOM.value:
                            master_attribute_filter = v
    return (
        tags,
        attributes,
        point_attribute_filter,
        line_attribute_filter,
        poly_attribute_filter,
        master_attribute_filter,
        point_tag_filter,
        line_tag_filter,
        poly_tag_filter,
        master_tag_filter,
    )


def generate_where_clause_indexes_case(
    geom_filter, g_id, c_id, country_export, table_name="ways_poly"
):
    where_clause = geom_filter
    if g_id:
        if (
            table_name == "ways_poly"
        ):  # currently grid index is only available for ways_poly
            column_name = "grid"
            grid_filter_base = [f"""{column_name} = {ind[0]}""" for ind in g_id]
            grid_filter = " OR ".join(grid_filter_base)
            where_clause = f"({grid_filter}) and ({geom_filter})"
    if c_id:
        c_id = ",".join(str(num) for num in c_id)
        # if table_name == "ways_poly" or table_name == "nodes":
        #     where_clause += f" and (country IN ({c_id}))"
        # else:
        where_clause += f" and (country <@ ARRAY[{c_id}])"
    if (
        country_export
    ):  # ignore the geometry take geom from the db itself by using precalculated field
        if c_id:
            # if table_name == "ways_poly" or table_name == "nodes":
            #     where_clause = f"country IN ({c_id})"
            # else:
            where_clause = f"country <@ ARRAY[{c_id}]"
    return where_clause


def get_country_geojson(c_id):
    query = f"SELECT ST_AsGeoJSON(geometry) as geom from countries where id={c_id}"
    return query


def raw_currentdata_extraction_query(
    params,
    g_id=None,
    c_id=None,
    ogr_export=False,
    select_all=False,
    country_export=False,
):
    """Default function to support current snapshot extraction with all of the feature that export_tool_api has"""

    geom_lookup_by = "ST_within" if params.use_st_within is True else "ST_intersects"
    geom_filter = create_geom_filter(params.geometry, geom_lookup_by)

    base_query = []

    (
        tags,
        attributes,
        point_attribute_filter,
        line_attribute_filter,
        poly_attribute_filter,
        master_attribute_filter,
        point_tag_filter,
        line_tag_filter,
        poly_tag_filter,
        master_tag_filter,
    ) = (None, None, None, None, None, None, None, None, None, None)

    point_select_condition = None
    line_select_condition = None
    poly_select_condition = None

    point_tag = None
    line_tag = None
    poly_tag = None
    master_tag = None
    use_geomtype_in_relation = True

    # query_table = []
    if select_all:
        select_condition = f"""osm_id,version,tags,changeset,timestamp,{'ST_Centroid(geom) as geom' if params.centroid else 'geom'}"""  # FIXme have condition for displaying userinfo after user authentication
    else:
        select_condition = f"""osm_id ,version,tags,changeset,timestamp,{'ST_Centroid(geom) as geom' if params.centroid else 'geom'}"""  # this is default attribute that we will deliver to user if user defines his own attribute column then those will be appended with osm_id only

    point_select_condition = select_condition  # initializing default
    line_select_condition = select_condition
    poly_select_condition = select_condition

    if params.filters:
        params.filters = (
            params.filters.dict()
        )  # FIXME: temp fix , since validation model got changed
        (
            tags,
            attributes,
            point_attribute_filter,
            line_attribute_filter,
            poly_attribute_filter,
            master_attribute_filter,
            point_tag_filter,
            line_tag_filter,
            poly_tag_filter,
            master_tag_filter,
        ) = extract_attributes_tags(params.filters)
    attribute_customization_full_support = ["geojson", "shp"]

    if params.output_type not in attribute_customization_full_support:
        logging.debug(
            "Merging filters since they don't have same no of filters for features"
        )
        merged_array = [
            i if i else []
            for i in [
                point_attribute_filter,
                line_attribute_filter,
                poly_attribute_filter,
            ]
        ]
        merged_result = list({x for l in merged_array for x in l})
        logging.debug(merged_result)
        if point_attribute_filter:
            point_attribute_filter = merged_result
        if line_attribute_filter:
            line_attribute_filter = merged_result
        if poly_attribute_filter:
            poly_attribute_filter = merged_result

    if attributes:
        if master_attribute_filter:
            if len(master_attribute_filter) > 0:
                select_condition = create_column_filter(
                    use_centroid=params.centroid,
                    output_type=params.output_type,
                    columns=master_attribute_filter,
                )
                # if master attribute is supplied it will be applied to other geom type as well even though value is supplied they will be ignored
                point_select_condition = select_condition
                line_select_condition = select_condition
                poly_select_condition = select_condition
        else:
            if point_attribute_filter:
                if len(point_attribute_filter) > 0:
                    point_select_condition = create_column_filter(
                        use_centroid=params.centroid,
                        output_type=params.output_type,
                        columns=point_attribute_filter,
                    )
            if line_attribute_filter:
                if len(line_attribute_filter) > 0:
                    line_select_condition = create_column_filter(
                        use_centroid=params.centroid,
                        output_type=params.output_type,
                        columns=line_attribute_filter,
                    )
            if poly_attribute_filter:
                if len(poly_attribute_filter) > 0:
                    poly_select_condition = create_column_filter(
                        use_centroid=params.centroid,
                        output_type=params.output_type,
                        columns=poly_attribute_filter,
                    )

    if tags:
        if (
            master_tag_filter
        ):  # if master tag is supplied then other tags should be ignored and master tag will be used
            master_tag = generate_tag_filter_query(master_tag_filter)
            point_tag = master_tag
            line_tag = master_tag
            poly_tag = master_tag
        else:
            if point_tag_filter:
                point_tag = generate_tag_filter_query(point_tag_filter)
            if line_tag_filter:
                line_tag = generate_tag_filter_query(line_tag_filter)
            if poly_tag_filter:
                poly_tag = generate_tag_filter_query(poly_tag_filter)

    # condition for geometry types
    if params.geometry_type is None:
        params.geometry_type = ["point", "line", "polygon"]
    if SupportedGeometryFilters.ALLGEOM.value in params.geometry_type:
        params.geometry_type = ["point", "line", "polygon"]
    if SupportedGeometryFilters.POINT.value in params.geometry_type:
        where_clause_for_nodes = generate_where_clause_indexes_case(
            geom_filter, g_id, c_id, country_export, "nodes"
        )

        query_point = f"""select
                    {point_select_condition}
                    from
                        nodes
                    where
                        {where_clause_for_nodes}"""
        if point_tag:
            query_point += f""" and ({point_tag})"""
        base_query.append(query_point)

    if SupportedGeometryFilters.LINE.value in params.geometry_type:
        where_clause_for_line = generate_where_clause_indexes_case(
            geom_filter, g_id, c_id, country_export, "ways_line"
        )

        query_ways_line = f"""select
            {line_select_condition}
            from
                ways_line
            where
                {where_clause_for_line}"""
        if line_tag:
            query_ways_line += f""" and ({line_tag})"""
        base_query.append(query_ways_line)

        if SupportedGeometryFilters.POLYGON.value in params.geometry_type:
            if poly_select_condition == line_select_condition and poly_tag == line_tag:
                use_geomtype_in_relation = False

        if use_geomtype_in_relation:
            where_clause_for_rel = generate_where_clause_indexes_case(
                geom_filter, g_id, c_id, country_export, "relations"
            )

            query_relations_line = f"""select
                {line_select_condition}
                from
                    relations
                where
                    {where_clause_for_rel}"""
            if line_tag:
                query_relations_line += f""" and ({line_tag})"""
            query_relations_line += """ and (geometrytype(geom)='MULTILINESTRING')"""
            base_query.append(query_relations_line)

    if SupportedGeometryFilters.POLYGON.value in params.geometry_type:
        where_clause_for_poly = generate_where_clause_indexes_case(
            geom_filter, g_id, c_id, country_export, "ways_poly"
        )

        query_ways_poly = f"""select
            {poly_select_condition}
            from
                ways_poly
            where
                {where_clause_for_poly}"""
        if poly_tag:
            query_ways_poly += f""" and ({poly_tag})"""
        base_query.append(query_ways_poly)
        where_clause_for_relations = generate_where_clause_indexes_case(
            geom_filter, g_id, c_id, country_export, "relations"
        )
        query_relations_poly = f"""select
            {poly_select_condition}
            from
                relations
            where
                {where_clause_for_relations}"""
        if poly_tag:
            query_relations_poly += f""" and ({poly_tag})"""
        if use_geomtype_in_relation:
            query_relations_poly += """ and (geometrytype(geom)='POLYGON' or geometrytype(geom)='MULTIPOLYGON')"""
        base_query.append(query_relations_poly)

    if ogr_export:
        # since query will be different for ogr exports and geojson exports because for ogr exports we don't need to grab each row in geojson
        table_base_query = base_query
    else:
        table_base_query = []
        for i in range(len(base_query)):
            table_base_query.append(
                f"""select ST_AsGeoJSON(t{i}.*) from ({base_query[i]}) t{i}"""
            )
    final_query = " UNION ALL ".join(table_base_query)
    if params.output_type == "csv":
        logging.debug(final_query)
    return final_query


def check_last_updated_rawdata():
    query = """select importdate as last_updated from planet_osm_replication_status"""
    return query


def raw_extract_plain_geojson(params, inspect_only=False):
    geom_filter_cond = None
    if params.geometry_type == "polygon":
        geom_filter_cond = """ and (geometrytype(geom)='POLYGON' or geometrytype(geom)='MULTIPOLYGON')"""
    select_condition = create_column_filter(columns=params.select)
    where_condition = generate_tag_filter_query(
        params.where, params.join_by, user_for_geojson=True
    )
    if params.bbox:
        xmin, ymin, xmax, ymax = (
            params.bbox[0],
            params.bbox[1],
            params.bbox[2],
            params.bbox[3],
        )
        geom_condition = f"""ST_intersects(ST_MakeEnvelope({xmin}, {ymin}, {xmax}, {ymax},4326), geom)"""

    query_list = []
    for table_name in params.look_in:
        sub_query = f"""select {select_condition} from {table_name} where ({where_condition}) """
        if params.bbox:
            sub_query += f""" and {geom_condition}"""
        if geom_filter_cond:
            sub_query += geom_filter_cond
        query_list.append(sub_query)
    table_base_query = []
    for i in range(len(query_list)):
        table_base_query.append(
            f"""select ST_AsGeoJSON(t{i}.*) from ({query_list[i]}) t{i}"""
        )
    final_query = " UNION ALL ".join(table_base_query)
    if inspect_only:
        final_query = f"""EXPLAIN
        {final_query}"""
    return final_query


def get_countries_query(q):
    query = "Select ST_AsGeoJSON(cf.*) FROM countries cf"
    if q:
        query += f" WHERE description ILIKE '%{q}%'"
    return query


def get_osm_feature_query(osm_id):
    select_condition = "osm_id ,tags,changeset,timestamp,geom"
    query = f"""SELECT ST_AsGeoJSON(n.*)
        FROM (select {select_condition} from nodes) n 
        WHERE osm_id = {osm_id}
        UNION
        SELECT ST_AsGeoJSON(wl.*)
        FROM (select {select_condition} from ways_line) wl 
        WHERE osm_id = {osm_id}
        UNION
        SELECT ST_AsGeoJSON(wp.*)
        FROM (select {select_condition} from ways_poly) wp 
        WHERE osm_id = {osm_id}
        UNION
        SELECT ST_AsGeoJSON(r.*)
        FROM (select {select_condition} from relations) r 
        WHERE osm_id = {osm_id}"""
    return query


def generate_polygon_stats_graphql_query(geojson_feature):
    """
    Gernerates the graphql query for the statistics
    """
    query = """
    {
        polygonStatistic (
        polygonStatisticRequest: {
            polygon: %s
        }
        )
        {
        analytics {
            functions(args:[
            {name:"sumX", id:"population", x:"population"},
            {name:"sumX", id:"populatedAreaKm2", x:"populated_area_km2"},
            {name:"percentageXWhereNoY", id:"osmBuildingGapsPercentage", x:"populated_area_km2", y:"building_count"},
            {name:"percentageXWhereNoY", id:"osmRoadGapsPercentage", x:"populated_area_km2", y:"highway_length"},
            {name:"percentageXWhereNoY", id:"antiqueOsmBuildingsPercentage", x:"populated_area_km2", y:"building_count_6_months"},
            {name:"percentageXWhereNoY", id:"antiqueOsmRoadsPercentage", x:"populated_area_km2", y:"highway_length_6_months"},
            {name:"avgX", id:"averageEditTime", x:"avgmax_ts"},
            {name:"maxX", id:"lastEditTime", x:"avgmax_ts"},
            {name:"sumX", id:"osmBuildingsCount", x:"building_count"},
            {name:"sumX", id:"highway_length", x:"highway_length"},
            {name:"sumX", id:"osmUsersCount", x:"osm_users"},
            {name:"sumX", id:"building_count_6_months" , x:"building_count_6_months"},
            {name:"sumX", id:"highway_length_6_months", x:"highway_length_6_months"},
            {name:"sumX", id:"aiBuildingsCountEstimation", x:"total_building_count"}
            {name:"sumX", id:"aiRoadCountEstimation", x:"total_road_length"}

            ]) {
            id,
            result
            }
        }
        }
    }
  """
    query = query % dumps(geojson_feature)

    return query
