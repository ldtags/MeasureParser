import json
import sys
from types import UnionType, NoneType
from typing import (
    Type,
    TypeVar,
    NewType,
    Any,
    overload,
    get_args,
    get_origin
)
from urllib.parse import urlparse

from src import _ROOT, get_path
from src.assets import (
    get_path as get_asset_path,
    get_image,
    get_tkimage
)
from src.resources import get_path as get_resource_path
from src.exceptions import (
    SchemaNotFoundError,
    CorruptedSchemaError
)


def json_obj(filepath: str) -> object:
    '''Creates a JSON object from the JSON file at `filepath`.'''

    _obj: object | None = None
    with open(filepath, 'r') as json_file:
        _obj = json.load(json_file)

    if _obj == None:
        raise OSError()

    return _obj


# validates that the given filepath leads to an eTRM measure JSON file
#
# Parameters:
#   filepath (str): specifies the path to the file being validated
#
# Returns:
#   bool: true if @filepath points to a correctly formatted eTRM
#         measure JSON file, false otherwise
def is_etrm_measure(measure_json: object) -> bool:
    '''Validates that the given file is an eTRM measure JSON file.'''

    from jsonschema import validate, ValidationError

    try:
        schema_path = get_resource_path('measure.schema.json')
        measure_schema = json_obj(schema_path)
    except OSError:
        raise SchemaNotFoundError()
    except json.JSONDecodeError:
        raise CorruptedSchemaError()

    try:
        validate(instance=measure_json, schema=measure_schema)
        return True
    except ValidationError:
        return False


def perror(*values: object):
    """Logs data to the defined output stream.
    
    Params:
        values `*object` : content being logged
    """

    print(*values, file=sys.stderr)


_NotDefined = NewType('_NotDefined', None)

_T = TypeVar('_T')
_U = TypeVar('_U')


@overload
def getc(o: dict, name: str, _type: Type[_T], /) -> _T:
    ...


@overload
def getc(o: dict, name: str, _type: None, /) -> None:
    ...


@overload
def getc(o: dict, name: str, _type: Type[_T], default: _U, /) -> _T | _U:
    ...


@overload
def getc(o: dict, name: str, _type: None, default: _U, /) -> None | _U:
    ...


def getc(o: dict,
         name: str,
         _type: Type[_T] | None,
         default: _U | Type[_NotDefined]=_NotDefined
        ) -> _T | _U | None:
    """Alternative for `dict.get()` that casts the attribute to `_type`."""

    try:
        attr = o.get(name)
    except AttributeError:
        if default is _NotDefined:
            raise
        return default

    attr_type = type(attr)
    _types = get_args(_type)
    _origin = get_origin(_type)

    if _origin is None:
        try:
            return _type(attr)
        except:
            raise TypeError(f'cannot cast attribute to type {_type}')
    elif _origin is list:
        if not isinstance(attr, list):
            raise TypeError(f'field {name} does not map to a list')

        if len(_types) > 1:
            if len(attr) != len(_types):
                raise TypeError(f'incompatible lists')
            results = []
            for i, list_type in enumerate(_types):
                try:
                    results.append(list_type(attr[i]))
                except:
                    raise TypeError(f'incompatible types: {type(attr[i])}'
                                    f' != {list_type}')
            return results

        list_type = _types[0]
        if list_type is UnionType:
            list_types = get_args(list_type)
            results = []
            for item in attr:
                i = 0
                for union_type in list_types:
                    try:
                        results.append(union_type(item))
                        break
                    except:
                        i = i + 1
                if i == len(_types):
                    raise TypeError(f'list item {attr} cannot cast to'
                                    f' any of {_types}')
            return results

        try:
            return list(map(lambda item: list_type(item), attr))
        except Exception as err:
            raise TypeError(f'list item {attr} cannot cast to'
                            f' {list_type}') from err
    elif _origin is dict:
        # TODO implement type union support
        if not isinstance(attr, dict):
            raise TypeError(f'field {name} does not map to a dict')

        args_len = len(_types)
        if args_len < 3:
            key_type = _types[0]
            val_type = Any if args_len < 2 else _types[1]
            for _key, _val in attr.items():
                try:
                    key_type(_key)
                except:
                    raise TypeError(f'type {type(_key)} is not compatible'
                                    f' with key type {key_type}')
                if args_len == 2:
                    try:
                        val_type(_val)
                    except:
                        raise TypeError(f'type {type(_val)} is not compatible'
                                        f' with val type {val_type}')
            return attr

        raise TypeError(f'unsupported dict type: {_type}')
    elif _origin is UnionType:
        if NoneType in _types and attr == None:
            return None

        for union_type in _types:
            try:
                return union_type(attr)
            except:
                continue
        type_union = ' | '.join(_types)
        raise TypeError(f'cannot cast attribute of type {attr_type}'
                        f' to {type_union}')
    else:
        raise TypeError(f'unsupported type: {_origin}')


class JSONObject:
    """Interface for converting a JSON string or object into a class.

    Extend when defining a class representation of a JSON object.

    Useful Methods:
        - `get` returns the type-hinted contents of a JSON field
    """

    def __init__(self, _json: str | dict[str, Any]):
        if isinstance(_json, str):
            self.json: dict[str, Any] = json.loads(_json)
        else:
            self.json = _json

    @overload
    def get(self, name: str, _type: Type[_T], /) -> _T:
        ...

    @overload
    def get(self, name: str, _type: None, /) -> None:
        ...

    @overload
    def get(self, name: str, _type: Type[_T], default: _U, /) -> _T | _U:
        ...

    @overload
    def get(self, name: str, _type: None, default: _U, /) -> None | _U:
        ...

    def get(self,
            name: str,
            _type: Type[_T] | None,
            default: _U | Type[_NotDefined]=_NotDefined
           ) -> _T | _U | None:
        return getc(self.json, name, _type, default)


class ParsedUrl:
    def __init__(self, url: str):
        parsed_result = urlparse(url)
        self.scheme = parsed_result.scheme
        self.netloc = parsed_result.netloc
        self.path = parsed_result.path
        self.query = self.get_queries(parsed_result.query)

    def get_queries(self, query_str: str | bytes) -> dict[str, str | None]:
        if isinstance(query_str, bytes):
            query_str = query_str.decode()

        if query_str == '':
            return {}

        url_queries: dict[str, str | None] = {}
        queries = query_str.split('&')
        for query in queries:
            try:
                key, val = query.split('=')
                url_queries[key] = val
            except ValueError:
                url_queries[query] = None
        return url_queries


def parse_url(url: str) -> ParsedUrl:
    return ParsedUrl(url)
