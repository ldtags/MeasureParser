import json
import os
from jsonschema import validate, ValidationError

from src.measure_parser.exceptions import (
    SchemaNotFoundError,
    CorruptedSchemaError
)

# validates that the given filepath leads to an eTRM measure JSON file
#
# Parameters:
#   filepath (str): specifies the path to the file being validated
#
# Returns:
#   bool: true if @filepath points to a correctly formatted eTRM
#         measure JSON file, false otherwise
def is_etrm_measure(filepath: str) -> bool:
    if not os.path.isfile(filepath):
        return False

    try:
        with open('./resources/measure.schema.json', 'r') as schema_file:
            measure_schema: dict = json.loads(schema_file.read())
    except OSError:
        raise SchemaNotFoundError()
    except json.JSONDecodeError:
        raise CorruptedSchemaError()

    try:
        with open(filepath, 'r') as measure_file:
            measure_json: dict = json.loads(measure_file.read())
    except OSError as err:
        raise err
    except json.JSONDecodeError:
        return False

    try:
        validate(instance=measure_json, schema=measure_schema)
        return True
    except ValidationError:
        return False
