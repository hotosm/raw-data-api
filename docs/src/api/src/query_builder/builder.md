Module src.query_builder.builder
================================
Page Contains Query logic required for application

Functions
---------

    
#### check_last_updated_rawdata

```python3
def check_last_updated_rawdata(
    
)
```

    
#### create_column_filter

```python3
def create_column_filter(
    columns,
    create_schema=False,
    output_type='geojson'
)
```
generates column filter , which will be used to filter column in output will be used on select query - Rawdata extraction

    
#### create_geom_filter

```python3
def create_geom_filter(
    geom
)
```
generates geometry intersection filter - Rawdata extraction

    
#### extract_attributes_tags

```python3
def extract_attributes_tags(
    filters
)
```

    
#### extract_geometry_type_query

```python3
def extract_geometry_type_query(
    params,
    ogr_export=False,
    g_id=None,
    c_id=None
)
```
used for specifically focused on export tool , this will generate separate queries for line point and polygon can be used on other datatype support - Rawdata extraction

    
#### format_file_name_str

```python3
def format_file_name_str(
    input_str
)
```

    
#### generate_tag_filter_query

```python3
def generate_tag_filter_query(
    filter,
    join_by='OR',
    user_for_geojson=False
)
```

    
#### generate_where_clause_indexes_case

```python3
def generate_where_clause_indexes_case(
    geom_filter,
    g_id,
    c_id,
    country_export,
    table_name='ways_poly'
)
```

    
#### get_country_id_query

```python3
def get_country_id_query(
    geom_dump
)
```

    
#### get_grid_id_query

```python3
def get_grid_id_query(
    geometry_dump
)
```

    
#### get_query_as_geojson

```python3
def get_query_as_geojson(
    query_list,
    ogr_export=None
)
```

    
#### raw_currentdata_extraction_query

```python3
def raw_currentdata_extraction_query(
    params,
    g_id,
    c_id,
    geometry_dump,
    ogr_export=False,
    select_all=False
)
```
Default function to support current snapshot extraction with all of the feature that export_tool_api has

    
#### raw_extract_plain_geojson

```python3
def raw_extract_plain_geojson(
    params,
    inspect_only=False
)
```

    
#### remove_spaces

```python3
def remove_spaces(
    input_str
)
```