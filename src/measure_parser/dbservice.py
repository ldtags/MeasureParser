import sys
import os
import sqlite3
from typing import Any, Optional
from src.measure_parser.exceptions import (
    DatabaseConnectionError,
    DatabaseContentError
)


# connecting the database
__filepath__: str \
    = sys.executable[0:sys.executable.rindex('\\')] + '\\database.db'
connection: sqlite3.Connection
if os.path.isfile(__filepath__):
    connection = sqlite3.connect(__filepath__)
elif os.path.isfile('database.db'):
    connection = sqlite3.connect('database.db')
else:
    raise DatabaseConnectionError('database file not found')
cursor: sqlite3.Cursor = connection.cursor()
if len(cursor.execute('SELECT name FROM sqlite_master').fetchall()) < 1:
    raise DatabaseContentError('database is empty')


def get_param_names(criteria: list[str]) -> list[str]:
    query: str = 'SELECT api_name FROM parameters'
    query += ' WHERE criteria IN ' + querify_list(criteria)
    query += ' ORDER BY ord ASC'
    params: list[str] = cursor.execute(query).fetchall()
    return listify(params)


def get_params(criteria: list[str] = None) -> dict[str, tuple[int, str]]:
    query: str = 'SELECT * FROM parameters'
    if criteria:
        query += ' WHERE criteria IN ' + querify_list(criteria)
    query += ' ORDER BY ord ASC'
    response: list[Any] = cursor.execute(query).fetchall()
    params: list[tuple[str, int, str]] = listify(response)
    criteria_map: dict[str, tuple[int, str]] = []
    for param in params:
        criteria_map[param[0]]



def get_value_table_names(criteria: list[str]) -> list[str]:
    query: str = 'SELECT api_name FROM tables WHERE shared = 0'
    query += ' AND criteria IN ' + querify_list(criteria)
    query += ' ORDER BY ord ASC'
    tables: list[str] = cursor.execute(query).fetchall()
    return listify(tables)


def get_shared_table_names(criteria: list[str]) -> list[str]:
    query: str = 'SELECT api_name FROM tables WHERE shared != 0'
    query += ' AND criteria IN ' + querify_list(criteria)
    query += ' ORDER BY ord ASC'
    tables: list[str] = cursor.execute(query).fetchall()
    return listify(tables)


def get_permutations() -> list[tuple[str, str, Optional[str]]]:
    query: str = 'SELECT reporting_name, verbose_name, valid_name'
    query += ' FROM permutations'
    response = cursor.execute(query).fetchall()
    return listify(response)


def get_permutation_data(reporting_name: str
                         ) -> tuple[str, Optional[str]]:
    query: str = 'SELECT verbose_name, valid_name FROM permutations'
    query += f' WHERE reporting_name = \"{reporting_name}\"'
    response = cursor.execute(query).fetchall()
    response_list: list[str] = listify(response)
    if len(response_list) == 0:
        return ('', None)
    return response_list[0]


def get_permutation_names() -> list[str]:
    query: str = 'SELECT reporting_name FROM permutations'
    cursor.execute(query)
    response: list[tuple[str,]] = cursor.fetchall()
    return listify(response)


def get_characterization_names() -> list[str]:
    query: str = 'SELECT name FROM characterizations'
    cursor.execute(query)
    response: list[tuple[str,]] = cursor.fetchall()
    return listify(response)


def querify_list(elements: list[str]) -> str:
    query_list: str = '('
    length: int = len(elements)
    for i, spec in enumerate(elements):
        query_list += '\"' + spec + '\"'
        if i != length - 1:
            query_list += ', '
    query_list += ')'
    return query_list


def listify(tuples: list[tuple[Any,]]) -> list[Any]:
    if type(tuples) is not list:
        return []

    if len(tuples) == 0:
        return []

    first = tuples[0]
    if type(first) is not tuple:
        return []

    if len(first) == 0:
        return []

    return [element[0] for element in tuples]