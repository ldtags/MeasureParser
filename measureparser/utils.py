import json
import os

from .measure import Characterization
from .exceptions import (
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
    '''Validates that the given file is an eTRM measure JSON file'''
    from jsonschema import validate, ValidationError
    from . import get_path

    if not os.path.isfile(filepath):
        return False

    try:
        SCHEMA_PATH = get_path('measure.schema.json')
        with open(SCHEMA_PATH, 'r') as schema_file:
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


def visualize_html(characterizations: list[Characterization],
                   id: str | None = None) -> None:
    '''Formats and writes the given characterizations to an output file'''
    from bs4 import BeautifulSoup

    id_format = f'-{id}' if id != None else ''
    with open(f'visualized{id_format}.txt', 'w') as out:
        for char in characterizations:
            soup = BeautifulSoup(char.content, 'html.parser')
            out.write(f'{char.name}:\n')
            try:
                out.write(soup.prettify())
            except UnicodeEncodeError:
                out.write('\tUnicodeEncodeError encountered\n')
            out.write('\n')
