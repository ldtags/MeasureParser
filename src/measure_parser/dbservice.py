import sys
import sqlite3
from typing import Any, Optional


__filepath__ = sys.executable[0:sys.executable.rindex('\\')]
connection = sqlite3.connect(__filepath__ + '\\database.db')
cursor = connection.cursor()


def get_param_names(criteria: list[str]) -> list[str]:
    query: str = 'SELECT api_name FROM parameters'
    query += ' WHERE criteria IN ' + querify_list(criteria)
    query += ' ORDER BY ord ASC'
    params: list[str] = cursor.execute(query).fetchall()
    return listify(params)


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