Module src.validation.models
============================
Page contains validation models for application

Variables
---------

```python3
allow_bind_zip_filter
```

Functions
---------

    
#### to_camel

```python3
def to_camel(
    string: str
) -> str
```

Classes
-------

### AttributeFilter

```python3
class AttributeFilter(
    __pydantic_self__,
    **data: Any
)
```

#### Ancestors (in MRO)

* src.validation.models.BaseModel
* pydantic.main.BaseModel
* pydantic.utils.Representation

#### Class variables

```python3
Config
```

#### Static methods

    
#### construct

```python3
def construct(
    _fields_set: Optional[ForwardRef('SetStr')] = None,
    **values: Any
) -> 'Model'
```
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values

    
#### from_orm

```python3
def from_orm(
    obj: Any
) -> 'Model'
```

    
#### parse_file

```python3
def parse_file(
    path: Union[str, pathlib.Path],
    *,
    content_type: 'unicode' = None,
    encoding: 'unicode' = 'utf8',
    proto: pydantic.parse.Protocol = None,
    allow_pickle: bool = False
) -> 'Model'
```

    
#### parse_obj

```python3
def parse_obj(
    obj: Any
) -> 'Model'
```

    
#### parse_raw

```python3
def parse_raw(
    b: Union[str, bytes],
    *,
    content_type: 'unicode' = None,
    encoding: 'unicode' = 'utf8',
    proto: pydantic.parse.Protocol = None,
    allow_pickle: bool = False
) -> 'Model'
```

    
#### schema

```python3
def schema(
    by_alias: bool = True,
    ref_template: 'unicode' = '#/definitions/{model}'
) -> 'DictStrAny'
```

    
#### schema_json

```python3
def schema_json(
    *,
    by_alias: bool = True,
    ref_template: 'unicode' = '#/definitions/{model}',
    **dumps_kwargs: Any
) -> 'unicode'
```

    
#### update_forward_refs

```python3
def update_forward_refs(
    **localns: Any
) -> None
```
Try to update ForwardRefs on fields based on this Model, globalns and localns.

    
#### validate

```python3
def validate(
    value: Any
) -> 'Model'
```

#### Methods

    
#### copy

```python3
def copy(
    self: 'Model',
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    update: Optional[ForwardRef('DictStrAny')] = None,
    deep: bool = False
) -> 'Model'
```
Duplicate a model, optionally choose which fields to include, exclude and change.

:param include: fields to include in new model
:param exclude: fields to exclude from new model, as with values this takes precedence over include
:param update: values to change/add in the new model. Note: the data is not validated before creating
    the new model: you should trust this data
:param deep: set to `True` to make a deep copy of the model
:return: new model instance

    
#### dict

```python3
def dict(
    self,
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False
) -> 'DictStrAny'
```
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

    
#### json

```python3
def json(
    self,
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    encoder: Optional[Callable[[Any], Any]] = None,
    models_as_dict: bool = True,
    **dumps_kwargs: Any
) -> 'unicode'
```
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.

### BaseModel

```python3
class BaseModel(
    __pydantic_self__,
    **data: Any
)
```

#### Ancestors (in MRO)

* pydantic.main.BaseModel
* pydantic.utils.Representation

#### Descendants

* src.validation.models.TagsFilter
* src.validation.models.AttributeFilter
* src.validation.models.Filters
* src.validation.models.RawDataCurrentParams
* src.validation.models.SnapshotParamsPlain
* src.validation.models.SnapshotResponse
* src.validation.models.SnapshotTaskResult
* src.validation.models.SnapshotTaskResponse
* src.validation.models.StatusResponse

#### Class variables

```python3
Config
```

#### Static methods

    
#### construct

```python3
def construct(
    _fields_set: Optional[ForwardRef('SetStr')] = None,
    **values: Any
) -> 'Model'
```
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values

    
#### from_orm

```python3
def from_orm(
    obj: Any
) -> 'Model'
```

    
#### parse_file

```python3
def parse_file(
    path: Union[str, pathlib.Path],
    *,
    content_type: 'unicode' = None,
    encoding: 'unicode' = 'utf8',
    proto: pydantic.parse.Protocol = None,
    allow_pickle: bool = False
) -> 'Model'
```

    
#### parse_obj

```python3
def parse_obj(
    obj: Any
) -> 'Model'
```

    
#### parse_raw

```python3
def parse_raw(
    b: Union[str, bytes],
    *,
    content_type: 'unicode' = None,
    encoding: 'unicode' = 'utf8',
    proto: pydantic.parse.Protocol = None,
    allow_pickle: bool = False
) -> 'Model'
```

    
#### schema

```python3
def schema(
    by_alias: bool = True,
    ref_template: 'unicode' = '#/definitions/{model}'
) -> 'DictStrAny'
```

    
#### schema_json

```python3
def schema_json(
    *,
    by_alias: bool = True,
    ref_template: 'unicode' = '#/definitions/{model}',
    **dumps_kwargs: Any
) -> 'unicode'
```

    
#### update_forward_refs

```python3
def update_forward_refs(
    **localns: Any
) -> None
```
Try to update ForwardRefs on fields based on this Model, globalns and localns.

    
#### validate

```python3
def validate(
    value: Any
) -> 'Model'
```

#### Methods

    
#### copy

```python3
def copy(
    self: 'Model',
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    update: Optional[ForwardRef('DictStrAny')] = None,
    deep: bool = False
) -> 'Model'
```
Duplicate a model, optionally choose which fields to include, exclude and change.

:param include: fields to include in new model
:param exclude: fields to exclude from new model, as with values this takes precedence over include
:param update: values to change/add in the new model. Note: the data is not validated before creating
    the new model: you should trust this data
:param deep: set to `True` to make a deep copy of the model
:return: new model instance

    
#### dict

```python3
def dict(
    self,
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False
) -> 'DictStrAny'
```
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

    
#### json

```python3
def json(
    self,
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    encoder: Optional[Callable[[Any], Any]] = None,
    models_as_dict: bool = True,
    **dumps_kwargs: Any
) -> 'unicode'
```
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.

### Filters

```python3
class Filters(
    __pydantic_self__,
    **data: Any
)
```

#### Ancestors (in MRO)

* src.validation.models.BaseModel
* pydantic.main.BaseModel
* pydantic.utils.Representation

#### Class variables

```python3
Config
```

#### Static methods

    
#### construct

```python3
def construct(
    _fields_set: Optional[ForwardRef('SetStr')] = None,
    **values: Any
) -> 'Model'
```
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values

    
#### from_orm

```python3
def from_orm(
    obj: Any
) -> 'Model'
```

    
#### parse_file

```python3
def parse_file(
    path: Union[str, pathlib.Path],
    *,
    content_type: 'unicode' = None,
    encoding: 'unicode' = 'utf8',
    proto: pydantic.parse.Protocol = None,
    allow_pickle: bool = False
) -> 'Model'
```

    
#### parse_obj

```python3
def parse_obj(
    obj: Any
) -> 'Model'
```

    
#### parse_raw

```python3
def parse_raw(
    b: Union[str, bytes],
    *,
    content_type: 'unicode' = None,
    encoding: 'unicode' = 'utf8',
    proto: pydantic.parse.Protocol = None,
    allow_pickle: bool = False
) -> 'Model'
```

    
#### schema

```python3
def schema(
    by_alias: bool = True,
    ref_template: 'unicode' = '#/definitions/{model}'
) -> 'DictStrAny'
```

    
#### schema_json

```python3
def schema_json(
    *,
    by_alias: bool = True,
    ref_template: 'unicode' = '#/definitions/{model}',
    **dumps_kwargs: Any
) -> 'unicode'
```

    
#### update_forward_refs

```python3
def update_forward_refs(
    **localns: Any
) -> None
```
Try to update ForwardRefs on fields based on this Model, globalns and localns.

    
#### validate

```python3
def validate(
    value: Any
) -> 'Model'
```

#### Methods

    
#### copy

```python3
def copy(
    self: 'Model',
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    update: Optional[ForwardRef('DictStrAny')] = None,
    deep: bool = False
) -> 'Model'
```
Duplicate a model, optionally choose which fields to include, exclude and change.

:param include: fields to include in new model
:param exclude: fields to exclude from new model, as with values this takes precedence over include
:param update: values to change/add in the new model. Note: the data is not validated before creating
    the new model: you should trust this data
:param deep: set to `True` to make a deep copy of the model
:return: new model instance

    
#### dict

```python3
def dict(
    self,
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False
) -> 'DictStrAny'
```
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

    
#### json

```python3
def json(
    self,
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    encoder: Optional[Callable[[Any], Any]] = None,
    models_as_dict: bool = True,
    **dumps_kwargs: Any
) -> 'unicode'
```
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.

### JoinFilterType

```python3
class JoinFilterType(
    /,
    *args,
    **kwargs
)
```

An enumeration.

#### Ancestors (in MRO)

* enum.Enum

#### Class variables

```python3
AND
```

```python3
OR
```

```python3
name
```

```python3
value
```

### OsmFeatureType

```python3
class OsmFeatureType(
    /,
    *args,
    **kwargs
)
```

An enumeration.

#### Ancestors (in MRO)

* enum.Enum

#### Class variables

```python3
NODES
```

```python3
RELATIONS
```

```python3
WAYS_LINE
```

```python3
WAYS_POLY
```

```python3
name
```

```python3
value
```

### RawDataCurrentParams

```python3
class RawDataCurrentParams(
    __pydantic_self__,
    **data: Any
)
```

#### Ancestors (in MRO)

* src.validation.models.BaseModel
* pydantic.main.BaseModel
* pydantic.utils.Representation

#### Class variables

```python3
Config
```

#### Static methods

    
#### check_geometry_area

```python3
def check_geometry_area(
    value,
    values
)
```
Validates geom area_m2

    
#### check_output_type

```python3
def check_output_type(
    value,
    values
)
```
Checks mbtiles required field

    
#### construct

```python3
def construct(
    _fields_set: Optional[ForwardRef('SetStr')] = None,
    **values: Any
) -> 'Model'
```
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values

    
#### from_orm

```python3
def from_orm(
    obj: Any
) -> 'Model'
```

    
#### parse_file

```python3
def parse_file(
    path: Union[str, pathlib.Path],
    *,
    content_type: 'unicode' = None,
    encoding: 'unicode' = 'utf8',
    proto: pydantic.parse.Protocol = None,
    allow_pickle: bool = False
) -> 'Model'
```

    
#### parse_obj

```python3
def parse_obj(
    obj: Any
) -> 'Model'
```

    
#### parse_raw

```python3
def parse_raw(
    b: Union[str, bytes],
    *,
    content_type: 'unicode' = None,
    encoding: 'unicode' = 'utf8',
    proto: pydantic.parse.Protocol = None,
    allow_pickle: bool = False
) -> 'Model'
```

    
#### return_unique_value

```python3
def return_unique_value(
    value
)
```
return unique list

    
#### schema

```python3
def schema(
    by_alias: bool = True,
    ref_template: 'unicode' = '#/definitions/{model}'
) -> 'DictStrAny'
```

    
#### schema_json

```python3
def schema_json(
    *,
    by_alias: bool = True,
    ref_template: 'unicode' = '#/definitions/{model}',
    **dumps_kwargs: Any
) -> 'unicode'
```

    
#### update_forward_refs

```python3
def update_forward_refs(
    **localns: Any
) -> None
```
Try to update ForwardRefs on fields based on this Model, globalns and localns.

    
#### validate

```python3
def validate(
    value: Any
) -> 'Model'
```

#### Methods

    
#### copy

```python3
def copy(
    self: 'Model',
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    update: Optional[ForwardRef('DictStrAny')] = None,
    deep: bool = False
) -> 'Model'
```
Duplicate a model, optionally choose which fields to include, exclude and change.

:param include: fields to include in new model
:param exclude: fields to exclude from new model, as with values this takes precedence over include
:param update: values to change/add in the new model. Note: the data is not validated before creating
    the new model: you should trust this data
:param deep: set to `True` to make a deep copy of the model
:return: new model instance

    
#### dict

```python3
def dict(
    self,
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False
) -> 'DictStrAny'
```
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

    
#### json

```python3
def json(
    self,
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    encoder: Optional[Callable[[Any], Any]] = None,
    models_as_dict: bool = True,
    **dumps_kwargs: Any
) -> 'unicode'
```
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.

### RawDataOutputType

```python3
class RawDataOutputType(
    /,
    *args,
    **kwargs
)
```

An enumeration.

#### Ancestors (in MRO)

* enum.Enum

#### Class variables

```python3
CSV
```

```python3
FLATGEOBUF
```

```python3
GEOJSON
```

```python3
GEOPACKAGE
```

```python3
KML
```

```python3
MBTILES
```

```python3
PGDUMP
```

```python3
SHAPEFILE
```

```python3
name
```

```python3
value
```

### SnapshotParamsPlain

```python3
class SnapshotParamsPlain(
    __pydantic_self__,
    **data: Any
)
```

#### Ancestors (in MRO)

* src.validation.models.BaseModel
* pydantic.main.BaseModel
* pydantic.utils.Representation

#### Class variables

```python3
Config
```

#### Static methods

    
#### construct

```python3
def construct(
    _fields_set: Optional[ForwardRef('SetStr')] = None,
    **values: Any
) -> 'Model'
```
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values

    
#### from_orm

```python3
def from_orm(
    obj: Any
) -> 'Model'
```

    
#### parse_file

```python3
def parse_file(
    path: Union[str, pathlib.Path],
    *,
    content_type: 'unicode' = None,
    encoding: 'unicode' = 'utf8',
    proto: pydantic.parse.Protocol = None,
    allow_pickle: bool = False
) -> 'Model'
```

    
#### parse_obj

```python3
def parse_obj(
    obj: Any
) -> 'Model'
```

    
#### parse_raw

```python3
def parse_raw(
    b: Union[str, bytes],
    *,
    content_type: 'unicode' = None,
    encoding: 'unicode' = 'utf8',
    proto: pydantic.parse.Protocol = None,
    allow_pickle: bool = False
) -> 'Model'
```

    
#### schema

```python3
def schema(
    by_alias: bool = True,
    ref_template: 'unicode' = '#/definitions/{model}'
) -> 'DictStrAny'
```

    
#### schema_json

```python3
def schema_json(
    *,
    by_alias: bool = True,
    ref_template: 'unicode' = '#/definitions/{model}',
    **dumps_kwargs: Any
) -> 'unicode'
```

    
#### update_forward_refs

```python3
def update_forward_refs(
    **localns: Any
) -> None
```
Try to update ForwardRefs on fields based on this Model, globalns and localns.

    
#### validate

```python3
def validate(
    value: Any
) -> 'Model'
```

    
#### validate_select_statement

```python3
def validate_select_statement(
    value,
    values
)
```
Validates geom area_m2

#### Methods

    
#### copy

```python3
def copy(
    self: 'Model',
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    update: Optional[ForwardRef('DictStrAny')] = None,
    deep: bool = False
) -> 'Model'
```
Duplicate a model, optionally choose which fields to include, exclude and change.

:param include: fields to include in new model
:param exclude: fields to exclude from new model, as with values this takes precedence over include
:param update: values to change/add in the new model. Note: the data is not validated before creating
    the new model: you should trust this data
:param deep: set to `True` to make a deep copy of the model
:return: new model instance

    
#### dict

```python3
def dict(
    self,
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False
) -> 'DictStrAny'
```
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

    
#### json

```python3
def json(
    self,
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    encoder: Optional[Callable[[Any], Any]] = None,
    models_as_dict: bool = True,
    **dumps_kwargs: Any
) -> 'unicode'
```
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.

### SnapshotResponse

```python3
class SnapshotResponse(
    __pydantic_self__,
    **data: Any
)
```

#### Ancestors (in MRO)

* src.validation.models.BaseModel
* pydantic.main.BaseModel
* pydantic.utils.Representation

#### Descendants

* pydantic.main.SnapshotResponse
* pydantic.main.SnapshotResponse

#### Class variables

```python3
Config
```

#### Static methods

    
#### construct

```python3
def construct(
    _fields_set: Optional[ForwardRef('SetStr')] = None,
    **values: Any
) -> 'Model'
```
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values

    
#### from_orm

```python3
def from_orm(
    obj: Any
) -> 'Model'
```

    
#### parse_file

```python3
def parse_file(
    path: Union[str, pathlib.Path],
    *,
    content_type: 'unicode' = None,
    encoding: 'unicode' = 'utf8',
    proto: pydantic.parse.Protocol = None,
    allow_pickle: bool = False
) -> 'Model'
```

    
#### parse_obj

```python3
def parse_obj(
    obj: Any
) -> 'Model'
```

    
#### parse_raw

```python3
def parse_raw(
    b: Union[str, bytes],
    *,
    content_type: 'unicode' = None,
    encoding: 'unicode' = 'utf8',
    proto: pydantic.parse.Protocol = None,
    allow_pickle: bool = False
) -> 'Model'
```

    
#### schema

```python3
def schema(
    by_alias: bool = True,
    ref_template: 'unicode' = '#/definitions/{model}'
) -> 'DictStrAny'
```

    
#### schema_json

```python3
def schema_json(
    *,
    by_alias: bool = True,
    ref_template: 'unicode' = '#/definitions/{model}',
    **dumps_kwargs: Any
) -> 'unicode'
```

    
#### update_forward_refs

```python3
def update_forward_refs(
    **localns: Any
) -> None
```
Try to update ForwardRefs on fields based on this Model, globalns and localns.

    
#### validate

```python3
def validate(
    value: Any
) -> 'Model'
```

#### Methods

    
#### copy

```python3
def copy(
    self: 'Model',
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    update: Optional[ForwardRef('DictStrAny')] = None,
    deep: bool = False
) -> 'Model'
```
Duplicate a model, optionally choose which fields to include, exclude and change.

:param include: fields to include in new model
:param exclude: fields to exclude from new model, as with values this takes precedence over include
:param update: values to change/add in the new model. Note: the data is not validated before creating
    the new model: you should trust this data
:param deep: set to `True` to make a deep copy of the model
:return: new model instance

    
#### dict

```python3
def dict(
    self,
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False
) -> 'DictStrAny'
```
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

    
#### json

```python3
def json(
    self,
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    encoder: Optional[Callable[[Any], Any]] = None,
    models_as_dict: bool = True,
    **dumps_kwargs: Any
) -> 'unicode'
```
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.

### SnapshotTaskResponse

```python3
class SnapshotTaskResponse(
    __pydantic_self__,
    **data: Any
)
```

#### Ancestors (in MRO)

* src.validation.models.BaseModel
* pydantic.main.BaseModel
* pydantic.utils.Representation

#### Descendants

* pydantic.main.SnapshotTaskResponse
* pydantic.main.SnapshotTaskResponse

#### Class variables

```python3
Config
```

#### Static methods

    
#### construct

```python3
def construct(
    _fields_set: Optional[ForwardRef('SetStr')] = None,
    **values: Any
) -> 'Model'
```
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values

    
#### from_orm

```python3
def from_orm(
    obj: Any
) -> 'Model'
```

    
#### parse_file

```python3
def parse_file(
    path: Union[str, pathlib.Path],
    *,
    content_type: 'unicode' = None,
    encoding: 'unicode' = 'utf8',
    proto: pydantic.parse.Protocol = None,
    allow_pickle: bool = False
) -> 'Model'
```

    
#### parse_obj

```python3
def parse_obj(
    obj: Any
) -> 'Model'
```

    
#### parse_raw

```python3
def parse_raw(
    b: Union[str, bytes],
    *,
    content_type: 'unicode' = None,
    encoding: 'unicode' = 'utf8',
    proto: pydantic.parse.Protocol = None,
    allow_pickle: bool = False
) -> 'Model'
```

    
#### schema

```python3
def schema(
    by_alias: bool = True,
    ref_template: 'unicode' = '#/definitions/{model}'
) -> 'DictStrAny'
```

    
#### schema_json

```python3
def schema_json(
    *,
    by_alias: bool = True,
    ref_template: 'unicode' = '#/definitions/{model}',
    **dumps_kwargs: Any
) -> 'unicode'
```

    
#### update_forward_refs

```python3
def update_forward_refs(
    **localns: Any
) -> None
```
Try to update ForwardRefs on fields based on this Model, globalns and localns.

    
#### validate

```python3
def validate(
    value: Any
) -> 'Model'
```

#### Methods

    
#### copy

```python3
def copy(
    self: 'Model',
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    update: Optional[ForwardRef('DictStrAny')] = None,
    deep: bool = False
) -> 'Model'
```
Duplicate a model, optionally choose which fields to include, exclude and change.

:param include: fields to include in new model
:param exclude: fields to exclude from new model, as with values this takes precedence over include
:param update: values to change/add in the new model. Note: the data is not validated before creating
    the new model: you should trust this data
:param deep: set to `True` to make a deep copy of the model
:return: new model instance

    
#### dict

```python3
def dict(
    self,
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False
) -> 'DictStrAny'
```
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

    
#### json

```python3
def json(
    self,
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    encoder: Optional[Callable[[Any], Any]] = None,
    models_as_dict: bool = True,
    **dumps_kwargs: Any
) -> 'unicode'
```
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.

### SnapshotTaskResult

```python3
class SnapshotTaskResult(
    __pydantic_self__,
    **data: Any
)
```

#### Ancestors (in MRO)

* src.validation.models.BaseModel
* pydantic.main.BaseModel
* pydantic.utils.Representation

#### Descendants

* pydantic.main.SnapshotTaskResult
* pydantic.main.SnapshotTaskResult

#### Class variables

```python3
Config
```

#### Static methods

    
#### construct

```python3
def construct(
    _fields_set: Optional[ForwardRef('SetStr')] = None,
    **values: Any
) -> 'Model'
```
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values

    
#### from_orm

```python3
def from_orm(
    obj: Any
) -> 'Model'
```

    
#### parse_file

```python3
def parse_file(
    path: Union[str, pathlib.Path],
    *,
    content_type: 'unicode' = None,
    encoding: 'unicode' = 'utf8',
    proto: pydantic.parse.Protocol = None,
    allow_pickle: bool = False
) -> 'Model'
```

    
#### parse_obj

```python3
def parse_obj(
    obj: Any
) -> 'Model'
```

    
#### parse_raw

```python3
def parse_raw(
    b: Union[str, bytes],
    *,
    content_type: 'unicode' = None,
    encoding: 'unicode' = 'utf8',
    proto: pydantic.parse.Protocol = None,
    allow_pickle: bool = False
) -> 'Model'
```

    
#### schema

```python3
def schema(
    by_alias: bool = True,
    ref_template: 'unicode' = '#/definitions/{model}'
) -> 'DictStrAny'
```

    
#### schema_json

```python3
def schema_json(
    *,
    by_alias: bool = True,
    ref_template: 'unicode' = '#/definitions/{model}',
    **dumps_kwargs: Any
) -> 'unicode'
```

    
#### update_forward_refs

```python3
def update_forward_refs(
    **localns: Any
) -> None
```
Try to update ForwardRefs on fields based on this Model, globalns and localns.

    
#### validate

```python3
def validate(
    value: Any
) -> 'Model'
```

#### Methods

    
#### copy

```python3
def copy(
    self: 'Model',
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    update: Optional[ForwardRef('DictStrAny')] = None,
    deep: bool = False
) -> 'Model'
```
Duplicate a model, optionally choose which fields to include, exclude and change.

:param include: fields to include in new model
:param exclude: fields to exclude from new model, as with values this takes precedence over include
:param update: values to change/add in the new model. Note: the data is not validated before creating
    the new model: you should trust this data
:param deep: set to `True` to make a deep copy of the model
:return: new model instance

    
#### dict

```python3
def dict(
    self,
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False
) -> 'DictStrAny'
```
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

    
#### json

```python3
def json(
    self,
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    encoder: Optional[Callable[[Any], Any]] = None,
    models_as_dict: bool = True,
    **dumps_kwargs: Any
) -> 'unicode'
```
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.

### StatusResponse

```python3
class StatusResponse(
    __pydantic_self__,
    **data: Any
)
```

#### Ancestors (in MRO)

* src.validation.models.BaseModel
* pydantic.main.BaseModel
* pydantic.utils.Representation

#### Descendants

* pydantic.main.StatusResponse
* pydantic.main.StatusResponse

#### Class variables

```python3
Config
```

#### Static methods

    
#### construct

```python3
def construct(
    _fields_set: Optional[ForwardRef('SetStr')] = None,
    **values: Any
) -> 'Model'
```
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values

    
#### from_orm

```python3
def from_orm(
    obj: Any
) -> 'Model'
```

    
#### parse_file

```python3
def parse_file(
    path: Union[str, pathlib.Path],
    *,
    content_type: 'unicode' = None,
    encoding: 'unicode' = 'utf8',
    proto: pydantic.parse.Protocol = None,
    allow_pickle: bool = False
) -> 'Model'
```

    
#### parse_obj

```python3
def parse_obj(
    obj: Any
) -> 'Model'
```

    
#### parse_raw

```python3
def parse_raw(
    b: Union[str, bytes],
    *,
    content_type: 'unicode' = None,
    encoding: 'unicode' = 'utf8',
    proto: pydantic.parse.Protocol = None,
    allow_pickle: bool = False
) -> 'Model'
```

    
#### schema

```python3
def schema(
    by_alias: bool = True,
    ref_template: 'unicode' = '#/definitions/{model}'
) -> 'DictStrAny'
```

    
#### schema_json

```python3
def schema_json(
    *,
    by_alias: bool = True,
    ref_template: 'unicode' = '#/definitions/{model}',
    **dumps_kwargs: Any
) -> 'unicode'
```

    
#### update_forward_refs

```python3
def update_forward_refs(
    **localns: Any
) -> None
```
Try to update ForwardRefs on fields based on this Model, globalns and localns.

    
#### validate

```python3
def validate(
    value: Any
) -> 'Model'
```

#### Methods

    
#### copy

```python3
def copy(
    self: 'Model',
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    update: Optional[ForwardRef('DictStrAny')] = None,
    deep: bool = False
) -> 'Model'
```
Duplicate a model, optionally choose which fields to include, exclude and change.

:param include: fields to include in new model
:param exclude: fields to exclude from new model, as with values this takes precedence over include
:param update: values to change/add in the new model. Note: the data is not validated before creating
    the new model: you should trust this data
:param deep: set to `True` to make a deep copy of the model
:return: new model instance

    
#### dict

```python3
def dict(
    self,
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False
) -> 'DictStrAny'
```
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

    
#### json

```python3
def json(
    self,
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    encoder: Optional[Callable[[Any], Any]] = None,
    models_as_dict: bool = True,
    **dumps_kwargs: Any
) -> 'unicode'
```
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.

### SupportedFilters

```python3
class SupportedFilters(
    /,
    *args,
    **kwargs
)
```

An enumeration.

#### Ancestors (in MRO)

* enum.Enum

#### Class variables

```python3
ATTRIBUTES
```

```python3
TAGS
```

```python3
name
```

```python3
value
```

### SupportedGeometryFilters

```python3
class SupportedGeometryFilters(
    /,
    *args,
    **kwargs
)
```

An enumeration.

#### Ancestors (in MRO)

* enum.Enum

#### Class variables

```python3
ALLGEOM
```

```python3
LINE
```

```python3
POINT
```

```python3
POLYGON
```

```python3
name
```

```python3
value
```

### TagsFilter

```python3
class TagsFilter(
    __pydantic_self__,
    **data: Any
)
```

#### Ancestors (in MRO)

* src.validation.models.BaseModel
* pydantic.main.BaseModel
* pydantic.utils.Representation

#### Class variables

```python3
Config
```

#### Static methods

    
#### construct

```python3
def construct(
    _fields_set: Optional[ForwardRef('SetStr')] = None,
    **values: Any
) -> 'Model'
```
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values

    
#### from_orm

```python3
def from_orm(
    obj: Any
) -> 'Model'
```

    
#### parse_file

```python3
def parse_file(
    path: Union[str, pathlib.Path],
    *,
    content_type: 'unicode' = None,
    encoding: 'unicode' = 'utf8',
    proto: pydantic.parse.Protocol = None,
    allow_pickle: bool = False
) -> 'Model'
```

    
#### parse_obj

```python3
def parse_obj(
    obj: Any
) -> 'Model'
```

    
#### parse_raw

```python3
def parse_raw(
    b: Union[str, bytes],
    *,
    content_type: 'unicode' = None,
    encoding: 'unicode' = 'utf8',
    proto: pydantic.parse.Protocol = None,
    allow_pickle: bool = False
) -> 'Model'
```

    
#### schema

```python3
def schema(
    by_alias: bool = True,
    ref_template: 'unicode' = '#/definitions/{model}'
) -> 'DictStrAny'
```

    
#### schema_json

```python3
def schema_json(
    *,
    by_alias: bool = True,
    ref_template: 'unicode' = '#/definitions/{model}',
    **dumps_kwargs: Any
) -> 'unicode'
```

    
#### update_forward_refs

```python3
def update_forward_refs(
    **localns: Any
) -> None
```
Try to update ForwardRefs on fields based on this Model, globalns and localns.

    
#### validate

```python3
def validate(
    value: Any
) -> 'Model'
```

#### Methods

    
#### copy

```python3
def copy(
    self: 'Model',
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    update: Optional[ForwardRef('DictStrAny')] = None,
    deep: bool = False
) -> 'Model'
```
Duplicate a model, optionally choose which fields to include, exclude and change.

:param include: fields to include in new model
:param exclude: fields to exclude from new model, as with values this takes precedence over include
:param update: values to change/add in the new model. Note: the data is not validated before creating
    the new model: you should trust this data
:param deep: set to `True` to make a deep copy of the model
:return: new model instance

    
#### dict

```python3
def dict(
    self,
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False
) -> 'DictStrAny'
```
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

    
#### json

```python3
def json(
    self,
    *,
    include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    encoder: Optional[Callable[[Any], Any]] = None,
    models_as_dict: bool = True,
    **dumps_kwargs: Any
) -> 'unicode'
```
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.

### WhereCondition

```python3
class WhereCondition(
    /,
    *args,
    **kwargs
)
```

dict() -> new empty dictionary
dict(mapping) -> new dictionary initialized from a mapping object's
    (key, value) pairs
dict(iterable) -> new dictionary initialized as if via:
    d = {}
    for k, v in iterable:
        d[k] = v
dict(**kwargs) -> new dictionary initialized with the name=value pairs
    in the keyword argument list.  For example:  dict(one=1, two=2)

#### Ancestors (in MRO)

* builtins.dict

#### Methods

    
#### clear

```python3
def clear(
    ...
)
```
D.clear() -> None.  Remove all items from D.

    
#### copy

```python3
def copy(
    ...
)
```
D.copy() -> a shallow copy of D

    
#### fromkeys

```python3
def fromkeys(
    iterable,
    value=None,
    /
)
```
Create a new dictionary with keys from iterable and values set to value.

    
#### get

```python3
def get(
    self,
    key,
    default=None,
    /
)
```
Return the value for key if key is in the dictionary, else default.

    
#### items

```python3
def items(
    ...
)
```
D.items() -> a set-like object providing a view on D's items

    
#### keys

```python3
def keys(
    ...
)
```
D.keys() -> a set-like object providing a view on D's keys

    
#### pop

```python3
def pop(
    ...
)
```
D.pop(k[,d]) -> v, remove specified key and return the corresponding value.

If the key is not found, return the default if given; otherwise,
raise a KeyError.

    
#### popitem

```python3
def popitem(
    self,
    /
)
```
Remove and return a (key, value) pair as a 2-tuple.

Pairs are returned in LIFO (last-in, first-out) order.
Raises KeyError if the dict is empty.

    
#### setdefault

```python3
def setdefault(
    self,
    key,
    default=None,
    /
)
```
Insert key with a value of default if key is not in the dictionary.

Return the value for key if key is in the dictionary, else default.

    
#### update

```python3
def update(
    ...
)
```
D.update([E, ]**F) -> None.  Update D from dict/iterable E and F.
If E is present and has a .keys() method, then does:  for k in E: D[k] = E[k]
If E is present and lacks a .keys() method, then does:  for k, v in E: D[k] = v
In either case, this is followed by: for k in F:  D[k] = F[k]

    
#### values

```python3
def values(
    ...
)
```
D.values() -> an object providing a view on D's values