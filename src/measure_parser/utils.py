import json
import os
from jsonschema import validate, ValidationError

try:
    from types import SimpleNamespace as Namespace
except ImportError:
    from argparse import Namespace

from src.measure_parser.exceptions import (
    MeasureFormatError,
    SchemaNotFoundError
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
    except json.JSONDecodeError as err:
        raise err

    try:
        with open(filepath, 'r') as measure_file:
            measure_json: dict = json.loads(measure_file.read())
    except OSError as err:
        raise err
    except json.JSONDecodeError:
        raise MeasureFormatError()

    try:
        validate(instance=measure_json, schema=measure_schema)
        return True
    except ValidationError as err:
        print(err.message)
        return False


# creates a Measure object from the given filepath
#
# Parameters:
#   filepath (str): specifies the path to the eTRM measure JSON file
#
# Returns:
#   Measure: the Measure object that represents the eTRM measure JSON file
#   None: returned if @filepath does not point to an eTRM measure JSON
#         file or if @filepath does not point to a file
# def create_measure(filepath: str) -> obj.Measure | None:
#     if not is_etrm_measure(filepath):
#         return None

#     try:
#         with open(filepath, 'r') as measure_file:
#             return obj.Measure(
#                 json.loads(measure_file.read(),
#                            object_hook=lambda dict: Namespace(**dict)))
#     except OSError:
#         print(filepath + ' not found')
#         return None