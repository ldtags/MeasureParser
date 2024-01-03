import os
import sqlite3
from typing import Any, Optional
try:
    from types import SimpleNamespace as Namespace
except ImportError:
    from argparse import Namespace

import measureparser.objects as obj
from measureparser.exceptions import (
    DatabaseConnectionError,
    DatabaseContentError
)

# connecting the database
__db_filepath = './measureparser/resources/database.db'
if not os.path.isfile(__db_filepath):
    raise DatabaseConnectionError('database file not found')
connection = sqlite3.connect(__db_filepath)
cursor = connection.cursor()
if len(cursor.execute('SELECT name FROM sqlite_master').fetchall()) < 1:
    raise DatabaseContentError('database is empty')


# queries the database for shared parameter names
#
# Parameters:
#   measure (Measure)   : a measure object that will determine criteria
#                         and allow for accurate data processing
#
# Returns:
#   list[str]   : a list of shared parameter names
def get_param_names(measure: obj.Measure=None) -> list[str]:
    query: str = 'SELECT api_name FROM parameters'
    if measure != None:
        query += f' WHERE criteria IN {queryfy(measure.get_criteria())}'
    query += ' ORDER BY ord ASC'
    response: list[tuple[str,]] = cursor.execute(query).fetchall()
    param_names: list[str] = listify(response)

    # measure specific post-processing
    if measure != None:
        if (measure.is_interactive()
                and not measure.contains_param('LightingType')):
            param_names.remove('LightingType')

    return listify(response)


# queries the database for a list of non-shared value table names
#   specified by @criteria
#
# Parameters:
#   criteria (list[str])    : a list of criteria
#
# Returns:
#   list[str]   : the list of non-shared value table names
def get_value_table_names(criteria: list[str]) -> list[str]:
    query: str = 'SELECT api_name FROM tables WHERE shared = 0'
    query += ' AND criteria IN ' + queryfy(criteria)
    query += ' ORDER BY ord ASC'
    tables: list[str] = cursor.execute(query).fetchall()
    return listify(tables)


# queries the database for a list of shared value table names specified
#   by @criteria
#
# Parameters:
#   criteria (list[str])    : a list of criteria
#
# Returns:
#   list[str]   : the list of shared value table names
def get_shared_table_names(criteria: list[str]) -> list[str]:
    query: str = 'SELECT api_name FROM tables WHERE shared != 0'
    query += ' AND criteria IN ' + queryfy(criteria)
    query += ' ORDER BY ord ASC'
    tables: list[str] = cursor.execute(query).fetchall()
    return listify(tables)


# queries the database for value table names
#
# Parameters:
#   measure (Measure)   : a measure object that will determine criteria
#                         and allow for accurate data processing
#   shared (bool)       : limit tables queried to shared tables
#   nonshared(bool)     : limit tables queried to nonshared tables
#
# Returns:
#   list[str]   : a list of value table names
def get_table_names(measure: obj.Measure=None,
                    shared: bool=False,
                    nonshared: bool=False) -> list[tuple[str, int]]:
    query: str = 'SELECT api_name, ord FROM tables'

    if measure or shared or nonshared:
        query += ' WHERE '

    shared_vals: list[int] = []
    if shared:
        shared_vals.append(1)
    if nonshared:
        shared_vals.append(0)

    if shared or nonshared:
        query += f'shared IN {queryfy(shared_vals)}'
        if measure:
            query += ' AND '

    criteria: list[str] = []
    if measure:
        criteria = measure.get_criteria()
        query += f'criteria IN {queryfy(criteria)}'

    query += ' ORDER BY ord ASC'
    cursor.execute(query)
    tables: dict[int, str] \
        = {table[1]: table[0] for table in cursor.fetchall()}

    if measure:
        # adding tables that can either be shared or non-shared
        # these tables are currently all optional, regardless of
        #   how they are defined in the database
        cursor.execute('SELECT api_name, ord FROM tables'
                            ' WHERE shared = -1'
                           f' AND criteria IN {queryfy(criteria)}'
                            ' ORDER BY ord ASC')
        for table in cursor.fetchall():
            if ((shared and measure.contains_shared_table(table[0]))
                    or (nonshared and measure.contains_value_table(table[0]))):
                tables[table[1]] = table[0]

        # postprocessing for table names that require it
        for index, table_name in tables.items():
            match table_name:
                case 'EnergyImpact':
                    tables[index] = f'EnergyImpact{measure.use_category}'
 
    table_names: list[str] = []
    for index in sorted(tables):
        table_names.append(tables[index])

    if measure:
        table_names = filter_optional_tables(tables, table_names, measure)

    return table_names


# filters out optional tables that don't exist in the measure
#
# Parameters:
#   tables (dict[int, str]) : a dict mapping the order index to table name
#   table_names (list[str]) : a list of table names
#   measure (Measure)       : a measure object
#
# Returns:
#   list[str]   : the filtered list of table names
def filter_optional_tables(tables: dict[int, str],
                           table_names: list[str],
                           measure: obj.Measure) -> list[str]:
    names: list[str] = table_names.copy()

    cursor.execute('SELECT api_name FROM tables WHERE optional = 0')
    response: list[tuple[str,]] = cursor.fetchall()
    optional_tables: list[str] = [element[0] for element in response]

    for table_name in tables.values():
        if ((table_name in optional_tables)
                and not measure.contains_table(table_name)):
            names.remove(table_name)

    return names


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
def get_table_columns(measure: obj.Measure=None,
                      table_api_name: str=None
                      ) -> dict[str, list[dict[str, str]]]:
    query: str = 'SELECT table_api, name, api_name, unit FROM table_columns'

    if table_api_name:
        query += f' WHERE table_api = {table_api_name}'

    if measure:
        criteria: list[str] = []
        mat_labels = measure.get_shared_parameter('MeasAppType').labels
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
            query += ' OR criteria IS NULL'

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


# queries the database for all permutations
#
# Returns:
#   list[tuple[str, str, Optional[str]]]    : a list of permutations
#       permutations in this format are specified as:
#           (reporting_name, verbose_name, valid_name)
def get_permutations() -> list[tuple[str, str, Optional[str]]]:
    query: str = 'SELECT reporting_name, verbose_name, valid_name'
    query += ' FROM permutations'
    response = cursor.execute(query).fetchall()
    return listify(response)


# queries the database for permutation data for the permutation associated
#   with @reporting_name
#
# Parameters:
#   reporting_name (str)    : the reporting name of the desired
#                             permutation
#
# Returns:
#   dict[str, str]  : a dict representation of permutation data
#       this dict is formatted as:
#           {'verbose'  : str
#            'valid'    : str}
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


# returns a list of characterization names that have mapped values
#
# Parameters:
#   measure (Namespace): a namespace representation of an eTRM measure
#                        JSON file
#
# Returns:
#   list[str]: a list of characterization names
def get_characterization_names(measure: Namespace) -> list[str]:
    char_list: list[str] = []
    for char_name in get_all_characterization_names():
        content: str = getattr(measure, char_name, None)
        if content != None:
            char_list.append(char_name)
    return char_list


# generates a list that is understood by SQL
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


# returns a list of the first elements in a list of tuples
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
                   optional: bool,
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

    cursor.execute('INSERT INTO tables VALUES (?, ?, ?, ?, ?)',
                   (api_name,
                    order,
                    criteria if criteria else 'REQ',
                    1 if shared else 0,
                    0 if optional else 1))

    connection.commit()


# used to insert shared parameters
#
# Parameters:
#   api_name (str)  : the api_name of the parameter
#   order (int)     : the order of this parameter
#   criteria (str)  : the criteria (if any) for the parameter
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
    
    cursor.execute('INSERT INTO parameters VALUES (?, ?, ?)',
                   (api_name, order, criteria if criteria else 'REQ'))

    connection.commit()


# used to insert permutations
#
# Parameters:
#   reporting_name (str)    : the permutation's reporting name
#   verbose_name (str)      : the permutation's verbose name
#   valid_name (str)        : the permutation's valid name
def __insert_permutation(reporting_name: str,
                         verbose_name: str,
                         valid_name: str=None) -> None:
    cursor.execute('INSERT INTO permutations VALUES (?, ?, ?)',
                   (reporting_name, verbose_name,
                    valid_name if valid_name else 'NULL'))

    connection.commit()
