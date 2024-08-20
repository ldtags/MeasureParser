import re
import json
import datetime as dt
import jsonschema as jschema
from typing import Any
from urllib.parse import urlparse

from src.etrm import resources, patterns
from src.etrm.exceptions import (
    ETRMError,
    SchemaError
)


def version_key(full_version_id: str) -> int:
    """Sorting key for measure versions."""

    re_match = re.fullmatch(patterns.VERSION_ID, full_version_id)
    if re_match is None:
        return -1

    key = 0
    measure_type = re_match.group(3)
    key += sum([ord(c) * 1000 for c in measure_type])

    use_category = re_match.group(4)
    key += sum([ord(c) * 1000 for c in use_category])

    uc_version = re_match.group(5)
    key += int(uc_version) * 100

    version_id = re_match.group(6)
    try:
        version, _ = version_id.split('-', 1)
        version = int(version)
        draft = 0
    except ValueError:
        version = int(version_id)
        draft = -1

    key += version * -10
    key += draft
    return key


def to_date(date_str: str) -> dt.date:
    """Converts a date string of format `YYYY-MM-DD` to a
    datetime object.
    """

    if not re.fullmatch(patterns.DATE, date_str):
        raise RuntimeError(
            f'Invalid Date Format: {date_str}'
        )

    year, month, day = date_str.split('-', 2)
    try:
        end_date = dt.date(int(year), int(month), int(day))
    except ValueError as err:
        raise RuntimeError(
            f'Invalid Date Format: {date_str}'
        ) from err

    return end_date


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


def is_etrm_measure(measure_json: dict[str, Any]) -> bool:
    """Validates the provided measure json against a JSON schema."""

    try:
        schema_path = resources.get_path('measure.schema.json')
    except FileNotFoundError:
        raise ETRMError(
            'Measure schema is either missing or has been renamed'
        )

    try:
        with open(schema_path, 'r') as fp:
            schema_json = json.load(fp)
    except json.JSONDecodeError as err:
        raise SchemaError(
            'An error occurred while parsing the eTRM measure JSON schema,'
            ' please reaquire the correct schema file or reinstall the'
            ' application'
        ) from err
    except OSError as err:
        raise ETRMError(
            'An error occurred while reading the measure JSON schema'
            f' file {schema_path}'
        ) from err

    try:
        jschema.validate(instance=measure_json, schema=schema_json)
        return True
    except jschema.ValidationError:
        pass

    return False
