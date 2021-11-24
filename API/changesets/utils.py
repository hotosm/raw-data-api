from json import dumps


def geom_filter_subquery(params):
    filter_type = params.get("type").value
    value = params.get("value")

    if filter_type == "geojson":
        select_query = f"SELECT 'custom' AS name, ST_GEOMFROMGEOJSON('{dumps(value)}') as boundary"

    if filter_type == "iso3":
        select_query = f"SELECT name, ST_GEOMFROMTEXT(ST_ASText(boundary), 4326) AS boundary from geoboundaries where tags -> 'name:iso_w3' = '{value}' OR tags -> 'name:iso_a3' = '{value}'"

    return select_query
