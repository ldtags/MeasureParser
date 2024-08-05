import sqlite3
from typing import Any, Optional, Literal

from src.etrm import resources
from src.etrm.models import Measure
from src.etrm.exceptions import ETRMError, DatabaseError


class LocalDatabase:
    table_names = [
        'characterizations',
        'parameters',
        'permutation_names',
        'permutation_objects',
        'table_columns',
        'tables'
    ]

    def __init__(self):
        try:
            db_path = resources.get_path('database.db')
        except FileNotFoundError:
            raise ETRMError(
                'The eTRM local database resource file is missing. Please'
                ' reaquire the database file or reinstall the application'
            )
        self.__validate(db_path)
        self.path = db_path
        self.connection: sqlite3.Connection | None = None
        self.cursor: sqlite3.Cursor | None = None

    def __enter__(self) -> sqlite3.Cursor:
        self.close()
        self.connection = sqlite3.connect(self.path)
        self.cursor = self.connection.cursor()
        return self.cursor

    def __exit__(self, *args) -> None:
        self.close()

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

        if self.cursor is not None:
            self.cursor.close()
            self.cursor = None

    def connect(self, path: str | None=None) -> sqlite3.Connection:
        path = path or self.path
        self.connection = sqlite3.connect(path)
        return self.connection

    @classmethod
    def __validate(cls, db_path) -> None:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        query = (
            'SELECT name'
            ' FROM sqlite_master'
            ' WHERE type = \'table\';'
        )
        table_names: list[str] = cursor.execute(query).fetchall()
        if set(table_names) != set(cls.table_names):
            raise DatabaseError(
                'The eTRM local database is corrupted. Please reaquire the'
                ' database file or reinstall the application'
            )
        cursor.close()
        connection.close()


_DB = LocalDatabase()


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


# queries the database for shared parameter names
#
# Parameters:
#   measure (Measure)   : a measure object that will determine criteria
#                         and allow for accurate data processing
#
# Returns:
#   list[str]   : a list of shared parameter names
def get_param_api_names(measure: Measure | None=None) -> list[str]:
    query: str = 'SELECT api_name FROM parameters'
    if measure is not None:
        query += f' WHERE criteria IN {queryfy(measure.get_criteria())}'

    query += ' ORDER BY ord ASC'
    with _DB as cursor:
        response: list[tuple[str,]] = cursor.execute(query).fetchall()

    param_names: list[str] = listify(response)

    # measure specific post-processing
    if measure is not None:
        if (measure.is_interactive()
                and not measure.contains_parameter('LightingType')):
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
def get_value_table_api_names(criteria: list[str]) -> list[str]:
    query = (
        'SELECT api_name'
        ' FROM tables'
        ' WHERE shared = 0'
       f' AND criteria IN {queryfy(criteria)}'
        ' ORDER BY ord ASC'
    )
    with _DB as cursor:
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
def get_shared_table_api_names(criteria: list[str]) -> list[str]:
    query = (
        'SELECT api_name FROM tables WHERE shared != 0'
        ' FROM tables'
        ' WHERE shared != 0'
       f' AND criteria IN {queryfy(criteria)}'
        ' ORDER BY ord ASC'
    )
    with _DB as cursor:
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
def get_table_api_names(measure: Measure | None=None,
                        shared: bool = False,
                        nonshared: bool = False
                       ) -> list[str]:
    query: str = 'SELECT api_name, ord FROM tables'

    if measure is not None or shared or nonshared:
        query += ' WHERE '

    shared_vals: list[int] = []
    if shared:
        shared_vals.append(1)
    if nonshared:
        shared_vals.append(0)

    if shared or nonshared:
        query += f'shared IN {queryfy(shared_vals)}'
        if measure != None:
            query += ' AND '

    criteria: list[str] = []
    if measure is not None:
        criteria = measure.get_criteria()
        query += f'criteria IN {queryfy(criteria)}'

    query += ' ORDER BY ord ASC'
    with _DB as cursor:
        _tables: list[tuple[str, int]] = cursor.execute(query).fetchall()

    tables = {
        int(table[1]): str(table[0])
        for table
        in _tables
    }

    if measure is not None:
        # adding tables that can either be shared or non-shared
        # these tables are currently all optional, regardless of
        #   how they are defined in the database
        query = (
            'SELECT api_name, ord'
            ' FROM tables'
            ' WHERE shared = -1'
           f' AND criteria IN {queryfy(criteria)}'
            ' ORDER BY ord ASC'
        )
        with _DB as cursor:
            _tables: list[tuple[str, int]] = cursor.execute(query).fetchall()

        for table in _tables:
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

    if measure is not None:
        table_names = filter_optional_tables(tables, table_names, measure)

    return table_names


# queries for nonshared value table standard names
#
# Parameters:
#   measure (Measure): a measure object used for specifying
#                      which tables to query for
#
# Returns:
#   dict[str, str]: table api_names mapped to the standard name
def get_standard_table_names(measure: Measure | None=None
                             ) -> dict[str, str]:
    standard_names: dict[str, str] = {}
    query = 'SELECT api_name, name FROM tables WHERE shared = 0'
    if measure is not None:
        query += f' AND criteria IN {queryfy(measure.get_criteria())}'

    with _DB as cursor:
        response: list[tuple[str, str]] = cursor.execute(query).fetchall()

    for names in response:
        standard_names[names[0]] = names[1]

    return standard_names


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
                           measure: Measure
                          ) -> list[str]:
    names = table_names.copy()
    query = (
        'SELECT api_name'
        ' FROM tables'
        ' WHERE optional = 0'
    )
    with _DB as cursor:
        response = cursor.execute(query).fetchall()

    optional_tables = [str(element[0]) for element in response]
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
def get_table_columns(measure: Measure | None=None,
                      table_api_name: str | None=None
                     ) -> dict[str, list[dict[str, str]]]:
    query = 'SELECT table_api, name, api_name, unit FROM table_columns'

    if table_api_name is not None:
        query += f' WHERE table_api = {table_api_name}'

    if measure is not None:
        criteria = measure.get_table_column_criteria()
        if not table_api_name:
            query += ' WHERE '
        else:
            query += ' AND '
        query += 'criteria IS NULL'

        if len(criteria) > 0:
            query += f' OR criteria IN {queryfy(criteria)}'

    with _DB as cursor:
        response = cursor.execute(query).fetchall()

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
    query = (
        'SELECT reporting_name, verbose_name, valid_name'
        ' FROM permutation_names'
    )
    with _DB as cursor:
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
def get_permutation_data(reporting_name: str) -> dict[str, str] | None:
    query = (
        'SELECT verbose_name, valid_name'
        ' FROM permutation_names'
       f' WHERE reporting_name = \'{reporting_name}\''
    )
    with _DB as cursor:
        response = cursor.execute(query).fetchall()

    response_list: list[str] = listify(response)
    if len(response_list) == 0:
        return None

    return {
        'verbose': response_list[0],
        'valid': response_list[1] if len(response_list) > 1 else None
    }


def get_permutation_names() -> list[str]:
    query = (
        'SELECT reporting_name'
        ' FROM permutation_names'
    )
    with _DB as cursor:
        response = cursor.execute(query).fetchall()

    return listify(response)


def get_all_characterization_names(source: Literal['json', 'etrm']
                                  ) -> list[str]:
    query = (
        'SELECT name'
        ' FROM characterizations'
       f' WHERE source = \'{source}\''
    )
    with _DB as cursor:
        response = cursor.execute(query).fetchall()

    return listify(response)


# returns a list of characterization names that have mapped values
#
# Parameters:
#   measure (Namespace): a namespace representation of an eTRM measure
#                        JSON file
#
# Returns:
#   list[str]: a list of characterization names
def get_characterization_names(measure: dict[str, Any]) -> list[str]:
    char_list: list[str] = []
    for char_name in get_all_characterization_names():
        content: str = getattr(measure, char_name, None)
        if content != None:
            char_list.append(char_name)
    return char_list


# used to insert shared or non-shared value tables
def __insert_table(api_name: str,
                   order: int,
                   shared: bool,
                   optional: bool,
                   criteria: str=None) -> None:
    with _DB as cursor:
        response = cursor.execute('SELECT * FROM tables').fetchall()

    tables: list[tuple] = listify(response)
    for table in tables:
        if table[0] == api_name:
            print(f'{api_name} already exists')
            return

    connection = _DB.connect()
    cursor = connection.cursor()
    try:
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
    finally:
        cursor.close()
        _DB.close()


# used to insert shared parameters
#
# Parameters:
#   api_name (str)  : the api_name of the parameter
#   order (int)     : the order of this parameter
#   criteria (str)  : the criteria (if any) for the parameter
def __insert_parameter(api_name: str,
                       order: int,
                       criteria: str=None) -> None:
    with _DB as cursor:
        response = cursor.execute('SELECT * FROM parameters').fetchall()

    params: list[tuple] = listify(response)
    for param in params:
        if param[0] == api_name:
            print(f'{api_name} already exists')
            return

    connection = _DB.connect()
    cursor = connection.cursor()
    try:
        cursor.execute('UPDATE parameters'
                        ' SET ord = parameters.ord + 1'
                       f' WHERE ord >= {order}')

        cursor.execute('INSERT INTO parameters VALUES (?, ?, ?)',
                       (api_name, order, criteria if criteria else 'REQ'))

        connection.commit()
    finally:
        cursor.close()
        _DB.close()


# used to insert permutations
#
# Parameters:
#   reporting_name (str)    : the permutation's reporting name
#   verbose_name (str)      : the permutation's verbose name
#   valid_name (str)        : the permutation's valid name
def __insert_permutation(reporting_name: str,
                         verbose_name: str,
                         valid_name: str=None) -> None:
    connection = _DB.connect()
    cursor = connection.cursor()
    try:
        cursor.execute('INSERT INTO permutations VALUES (?, ?, ?)',
                       (reporting_name, verbose_name,
                        valid_name if valid_name else 'NULL'))

        connection.commit()
    finally:
        cursor.close()
        _DB.close()
