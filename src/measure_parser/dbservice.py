import sys
import os
import sqlite3
from typing import Any, Optional
from src.measure_parser.objects import Measure
from src.measure_parser.exceptions import (
    DatabaseConnectionError,
    DatabaseContentError
)
try:
    from types import SimpleNamespace as Namespace
except ImportError:
    from argparse import Namespace


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
    query += ' WHERE criteria IN ' + queryfy(criteria)
    query += ' ORDER BY ord ASC'
    params: list[str] = cursor.execute(query).fetchall()
    return listify(params)


def get_params(criteria: list[str] = None) -> dict[str, tuple[int, str]]:
    query: str = 'SELECT * FROM parameters'
    if criteria:
        query += ' WHERE criteria IN ' + queryfy(criteria)
    query += ' ORDER BY ord ASC'
    response: list[Any] = cursor.execute(query).fetchall()
    params: list[tuple[str, int, str]] = listify(response)
    criteria_map: dict[str, tuple[int, str]] = []
    for param in params:
        criteria_map[param[0]]


def get_value_table_names(criteria: list[str]) -> list[str]:
    query: str = 'SELECT api_name FROM tables WHERE shared = 0'
    query += ' AND criteria IN ' + queryfy(criteria)
    query += ' ORDER BY ord ASC'
    tables: list[str] = cursor.execute(query).fetchall()
    return listify(tables)


def get_shared_table_names(criteria: list[str]) -> list[str]:
    query: str = 'SELECT api_name FROM tables WHERE shared != 0'
    query += ' AND criteria IN ' + queryfy(criteria)
    query += ' ORDER BY ord ASC'
    tables: list[str] = cursor.execute(query).fetchall()
    return listify(tables)


def get_table_names(measure: Measure,
                    criteria: list[str],
                    shared: bool=False,
                    nonshared: bool=False,
                    other: bool=False) -> list[str]:
    if measure.is_DEER():
        criteria.append('DEER')

    query: str = 'SELECT api_name FROM tables WHERE'

    shared_vals: list[int] = []
    if shared:
        shared_vals.append(1)
    if nonshared:
        shared_vals.append(0)
    if other:
        shared_vals.append(-1)
    if shared or nonshared or other:
        query += f' shared IN {queryfy(shared_vals)} AND'

    query += f' criteria IN {queryfy(criteria)}'
    query += ' ORDER BY ord ASC'

    response: list[tuple[str,]] = cursor.execute(query).fetchall()
    table_names: list[str] = listify(response)

    if 'EnergyImpact' in table_names:
        index: int = table_names.index('EnergyImpact')
        table_names[index] = f'EnergyImpact{measure.use_category}'

    return table_names


# queries the database for non-shared value table columns
#
# Parameters:
#   measure (Measure)    : a measure used to determine table column criteria,
#                          does not limit table columns queried if not included
#   table_api_name (str) : limit columns to only columns associated with this
#                          table api name
#
# Returns:
#   dict[str, list[dict[str, str]]] : a dict that maps table api names to their
#                                     associated columns
#       table columns in this dict are formatted as:
#           'table_api' : the api_name of the associated value table
#           'name'      : the name of the table column
#           'api_name'  : the api_name of the table column
#           'unit'      : the unit of the column
def get_table_columns(measure: Measure=None,
                      table_api_name: str=None
                      ) -> dict[str, list[dict[str, str]]]:
    query: str = 'SELECT table_api, name, api_name, unit FROM table_columns'

    if table_api_name:
        query += f' WHERE table_api = {table_api_name}'

    if measure:
        criteria: list[str] = []
        mat_labels: list[str] = measure.get_shared_parameter('MAT').labels
        if 'AR' in mat_labels:
            criteria.append('AR_MAT')
            if len(mat_labels) > 2:
                criteria.append('MAT+AR')
        if len(criteria) > 0:
            if not table_api_name:
                query += ' WHERE '
            else:
                query += ' AND '
            query += f'criteria IN {queryfy(criteria)}'

    response: list[tuple] = cursor.execute(query).fetchall()
    column_dict: dict[str, list[dict[str, str]]] = {}
    for column in response:
        table_api: str = column[0]
        column_data: dict = {
            'table_api': table_api,
            'name': column[1],
            'api_name': column[2],
            'unit': column[3]
        }
        if table_api not in column_dict.keys():
            column_dict[table_api] = [column_data]
        else:
            column_dict[table_api].append(column_data)
    return column_dict


def get_permutations() -> list[tuple[str, str, Optional[str]]]:
    query: str = 'SELECT reporting_name, verbose_name, valid_name'
    query += ' FROM permutations'
    response = cursor.execute(query).fetchall()
    return listify(response)


def get_permutation_data(reporting_name: str) -> dict[str, str]:
    query: str = 'SELECT verbose_name, valid_name FROM permutations'
    query += f' WHERE reporting_name = \"{reporting_name}\"'
    response = cursor.execute(query).fetchall()
    response_list: list[str] = listify(response)
    if len(response_list) == 0:
        return ('', None)

    return {'verbose': response_list[0],
            'valid': response_list[1] if len(response_list) > 1 else None}


def get_permutation_names() -> list[str]:
    query: str = 'SELECT reporting_name FROM permutations'
    cursor.execute(query)
    response: list[tuple[str,]] = cursor.fetchall()
    return listify(response)


def get_all_characterization_names() -> list[str]:
    query: str = 'SELECT name FROM characterizations'
    cursor.execute(query)
    response: list[tuple[str,]] = cursor.fetchall()
    return listify(response)


def get_characterization_names(measure: Namespace) -> list[str]:
    char_list: list[str] = []
    for char_name in get_all_characterization_names():
        content: str = getattr(measure, char_name, None)
        if content != None:
            char_list.append(char_name)
    return char_list


def queryfy(elements: list[Any]) -> str:
    query_list: str = '('
    length: int = len(elements)
    for i, element in enumerate(elements):
        match element:
            case str():
                query_list += '\"' + element + '\"'
            case _:
                query_list += str(element)

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


# used to insert shared or non-shared value tables
def __insert_table(api_name: str,
                   order: int,
                   shared: bool,
                   criteria: str=None) -> None:
    cursor.execute('SELECT * FROM tables')
    response: list[tuple[str,]] = cursor.fetchall()
    tables: list[tuple] = listify(response)
    for table in tables:
        if table[0] == api_name:
            print(f'{api_name} already exists')
            return

    cursor.execute('UPDATE tables'
                        ' SET ord = tables.ord + 1'
                       f' WHERE ord >= {order}')

    cursor.execute('INSERT INTO tables VALUES (?, ?, ?, ?)',
                   (api_name,
                    order,
                    criteria if criteria else 'REQ',
                    1 if shared else 0))

    connection.commit()


def __insert_parameter(api_name: str,
                       order: int,
                       criteria: str=None) -> None:
    cursor.execute('SELECT * FROM parameters')
    response: list[tuple[str,]] = cursor.fetchall()
    params: list[tuple] = listify(response)
    for param in params:
        if param[0] == api_name:
            print(f'{api_name} already exists')
            return

    cursor.execute('UPDATE parameters'
                    ' SET ord = parameters.ord + 1'
                   f' WHERE ord >= {order}')
    
    cursor.execute('INSERT INTO tables VALUES (?, ?, ?, ?)',
                   (api_name, order, criteria if criteria else 'REQ'))

    connection.commit()


def __insert_permutation(reporting_name: str,
                         verbose_name: str,
                         valid_name: str):
    pass # make sure to include id validation here as i just use math.rand (oops actually maybe do something else)
