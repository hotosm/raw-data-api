Module API.auth
===============

Sub-modules
-----------
* [API.auth.routers](routers/)

Variables
---------

```python3
osm_auth
```

Functions
---------

    
#### login_required

```python3
def login_required(
    access_token: str = Header(Ellipsis)
)
```

Classes
-------

### AuthUser

```python3
class AuthUser(
    __pydantic_self__,
    **data: Any
)
```

#### Ancestors (in MRO)

* pydantic.main.BaseModel
* pydantic.utils.Representation

#### Descendants

* pydantic.main.AuthUser

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