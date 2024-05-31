import json
import os
import sys

from measureparser import _ROOT
from measureparser.exceptions import (
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


def resource_path(filename: str) -> str:
    '''Returns an absolute path to a resource file in the package.'''

    return os.path.join(_ROOT, 'resources', filename)


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
        schema_path = resource_path('measure.schema.json')
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
