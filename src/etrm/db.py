import itertools
import sqlite3 as sql
import pylightxl as xl
from typing import (
    Any,
    Optional,
    Literal,
    Type
)

from src.etrm import resources
from src.etrm.models import Measure
from src.etrm.exceptions import ETRMError, DatabaseError


class ColumnPragma:
    def __init__(self,
                 column: str,
                 _type: Type[str | int | float],
                 non_null: bool=False,
                 default: str | int | float | None=None,
                 pk: bool=False):
        self.__column = column
        self.__type = _type
        self.__non_null = non_null
        self.__default = default
        self.__pk = pk

    @property
    def column(self) -> str:
        return self.__column

    @property
    def type(self) -> Type[str | int | float | None]:
        return self.__type

    @property
    def non_null(self) -> bool:
        return self.__non_null

    @property
    def default(self) -> str | int | float | None:
        return self.__default

    @property
    def pk(self) -> bool:
        return self.__pk


class TablePragma:
    def __init__(self, table: str):
        self.table = table
        self.__columns: dict[str, ColumnPragma] = []

    @property
    def columns(self) -> list[ColumnPragma]:
        return list(self.__columns.values())

    def add_pragma(self, pragma: ColumnPragma) -> None:
        try:
            self.__columns[pragma.column]
            raise ValueError(
                f'A column pragma for {pragma.column} already exists'
            )
        except KeyError:
            self.__columns[pragma.column] = pragma


class LocalDatabase:
    table_names = {
        'characterizations',
        'parameters',
        'permutation_names',
        'permutation_objects',
        'table_columns',
        'tables',
        'eul',
        'measure_impact_type',
        'ntg',
        'permutation_valid_data',
        'use_categories',
        'delivery_type',
        'exclusions'
    }

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
        self.connection: sql.Connection | None = None
        self.pragma: dict[str, TablePragma] = {}

    def __enter__(self) -> sql.Connection:
        self.close()
        self.connection = sql.connect(self.path)
        return self.connection

    def __exit__(self, *args) -> None:
        self.close()

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def connect(self, path: str | None=None) -> sql.Connection:
        path = path or self.path
        self.connection = sql.connect(path)
        return self.connection

    def get_pragma(self, table: str) -> TablePragma:
        """Returns a mapping of each `table` column to their type,
        non-null status, default value (if exists) and primary key stautus.
        """

        if table not in LocalDatabase.table_names:
            raise DatabaseError(f'Unknown table: {table}')

        try:
            return self.pragma[table]
        except KeyError:
            pass

        query = f'PRAGMA table_info({table});'
        with self.connect() as conn:
            cursor = conn.cursor()
            try:
                response = cursor.execute(query).fetchall()
            finally:
                cursor.close()

        pragma = TablePragma(table)
        for _, name, type_str, not_null, default, pk in response:
            match type_str:
                case 'INTEGER' | 'NUMERIC':
                    _type = int
                case 'REAL':
                    _type = float
                case 'TEXT' | 'BLOB':
                    _type = str
                case other:
                    raise DatabaseError(f'Unknown type: {other}')

            pragma.add_pragma(
                ColumnPragma(
                    name=name,
                    _type=_type,
                    non_null=False if not_null == 0 else True,
                    default=default,
                    pk=False if pk == 0 else True
                )
            )

        self.pragma[table] = pragma
        return pragma

    def validate_values(self,
                        table: str,
                        *values: list[str | int | float | None]
                       ) -> None:
        """Validates that all values in `*values` are valid to be inserted
        into `table`.
        """

        if table not in LocalDatabase.table_names:
            raise DatabaseError(f'Unknown table: {table}')

        pragma = self.get_pragma(table)
        for value_row in values:
            if len(value_row) != len(pragma.columns):
                raise ValueError(f'Invalid number of values')

            for i, value in enumerate(value_row):
                if not pragma.columns[i].non_null and value is None:
                    raise ValueError(f'Non-null constraint failed')
                elif value is not None:
                    _type = pragma.columns[i]
                    if not isinstance(value, _type):
                        raise ValueError(
                            f'Invalid type: {value} must be a {_type} object'
                        )

    def insert(self,
               table: str,
               values: list[str | int | float | None]
              ) -> None:
        if table not in LocalDatabase.table_names:
            raise DatabaseError(f'Unknown table: {table}')

        self.validate_values(table, values)

        param_str = ','.join(['?'] * len(values))
        query = f'INSERT INTO {table} VALUES ({param_str})'
        with self.connect() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, tuple(values))
            finally:
                cursor.close()
            conn.commit()

    def insert_many(self,
                    table: str,
                    values: list[list[str | int | float | None]]
                   ) -> None:
        if table not in LocalDatabase.table_names:
            raise DatabaseError(f'Unknown table: {table}')

        self.validate_values(table, *values)

        param_str = ','.join(['?'] * len(values))
        query = f'INSERT INTO {table} VALUES ({param_str})'
        with self.connect() as conn:
            cursor = conn.cursor()
            try:
                cursor.executemany(
                    query,
                    list(
                        map(
                            lambda row: tuple(row),
                            values
                        )
                    )
                )
            finally:
                cursor.close()
            conn.commit()

    @classmethod
    def __validate(cls, db_path) -> None:
        connection = sql.connect(db_path)
        cursor = connection.cursor()
        query = (
            'SELECT name'
            ' FROM sqlite_master'
            ' WHERE type = \'table\';'
        )
        table_names: list[tuple[str,]] = cursor.execute(query).fetchall()
        table_names = set(map(lambda item: item[0], table_names))
        if table_names != cls.table_names:
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


def get_permutation_name_map() -> dict[str, str]:
    """Returns a dict mapping each reporting name to its verbose name."""

    query = (
        'SELECT reporting_name, verbose_name'
        ' FROM permutation_names'
    )
    with _DB as cursor:
        response = cursor.execute(query).fetchall()

    return {
        str(names[0]): str(names[1])
        for names
        in response
    }


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


def get_eul_ids() -> set[str]:
    """Returns a set of all valid EUL IDs."""

    query = (
        'SELECT value'
        ' FROM permutation_valid_data'
        ' WHERE verbose_name = \'shared__EULID\''
    )
    with _DB as cursor:
        response = cursor.execute(query).fetchall()

    return set(map(lambda val: val[0], response))


def get_delivery_types() -> dict[str, tuple[str, str | None]]:
    """Returns a dict mapping all valid delivery types to their
    start and end dates.

    Mapped tuples are structured as a two-tuple containing:
        1. Start date (naive, formatted YYYY-MM-DD)
        2. End date (naive, formatted YYYY-MM-DD) or `None`
    """

    query = (
        'SELECT type, start_date, expire_date'
        ' FROM delivery_type'
    )
    with _DB as cursor:
        response = cursor.execute(query).fetchall()

    deliv_types: dict[str, tuple[str, str | None]] = {}
    for item in response:
        deliv_types[item[0]] = (item[1], item[2])

    return deliv_types


def get_measure_impact_types() -> dict[str, tuple[str, str | None]]:
    query = (
        'SELECT type, start_date, expire_date'
        ' FROM measure_impact_type'
    )
    with _DB as cursor:
        response = cursor.execute(query).fetchall()

    mit_types: dict[str, tuple[str, str | None]] = {}
    for item in response:
        mit_types[item[0]] = (item[1], item[2])

    return mit_types


def get_exclusions(*columns: str,
                   valid: bool=True,
                   allowed:bool=True,
                   exclusive: bool=True
                  ) -> list[list[str]]:
    """Returns a list of ordered exclusions.

    Exclusions will be ordered in the same order that their
    associated columns are provided.
    """

    valid_int = 0 if valid else 1
    allowed_int = 0 if allowed else 1
    query = (
        'SELECT labels, exclusion_values'
        ' FROM exclusions'
       f' WHERE allowed = {allowed_int}'
           f' AND valid = {valid_int}'
    )

    if not exclusive:
        for column in columns:
            query += (
                ' AND ('
                   f' labels LIKE \'{column};;%\''
                   f' OR labels LIKE \'%;;{column}\''
                   f' OR labels LIKE \'%;;{column};;%\''
                ' )'
            )
    else:
        query += ' AND ('
        permutations = list(itertools.permutations(list(columns)))
        for i, permutation in enumerate(permutations):
            if i != 0:
                query += ' OR '
            query += 'labels = \''
            query += ';;'.join(permutation)
            query += '\''
        query += ')'

    with _DB as conn:
        cursor = conn.cursor()
        try:
            response = cursor.execute(query).fetchall()
        finally:
            cursor.close()

    column_list = list(columns)
    column_order: dict[str, int] = {}
    exclusions: list[list[str]] = []
    for label_join, value_join in response:
        labels = str(label_join).split(';;')
        values = str(value_join).split(';;')
        exclusion = [''] * len(columns)
        for label, value in zip(labels, values):
            if value == '1':
                value = 'False'
            elif value == '0':
                value = 'True'

            try:
                order = column_order[label]
            except KeyError:
                try:
                    order = column_list.index(label)
                except ValueError as err:
                    raise RuntimeError(f'Invalid column: {label}') from err
                column_order[label] = order
            exclusion[order] = value
        exclusions.append(exclusion)

    return exclusions


def get_exclusion_map(key_name: str,
                      mapped_name: str,
                      valid: bool=True,
                      allowed: bool=True,
                      strict: bool=False
                     ) -> dict[str, set[str]]:
    """Returns a mapping of `key_name` exclusion values to allowed
    `mapped_name` exclusion values.
    """

    valid_int = 0 if valid else 1
    allowed_int = 0 if allowed else 1
    query = (
        'SELECT labels, exclusion_values'
        ' FROM exclusions'
       f' WHERE allowed = {allowed_int}'
           f' AND valid = {valid_int}'
    )
    if not strict:
        for verbose_name in [key_name, mapped_name]:
            query += (
                ' AND ('
                   f' labels LIKE \'{verbose_name};;%\''
                   f' OR labels LIKE \'%;;{verbose_name}\''
                   f' OR labels LIKE \'%;;{verbose_name};;%\''
                ' )'
            )
    else:
        query += f' AND (labels = \'{key_name};;{mapped_name}\')'

    with _DB as conn:
        cursor = conn.cursor()
        try:
            response = cursor.execute(query).fetchall()
        finally:
            cursor.close()

    exclusions: dict[str, set[str]] = {}
    for label_join, value_join in response:
        labels = str(label_join).split(';;')
        values = str(value_join).split(';;')
        key_index = labels.index(key_name)
        mapped_index = labels.index(mapped_name)
        try:
            exclusions[values[key_index]].add(values[mapped_index])
        except KeyError:
            exclusions[values[key_index]] = {values[mapped_index]}

    return exclusions


def get_all_exclusions(*permutations: str,
                       valid: bool=True,
                       allowed: bool=True
                      ) -> list[list[str]]:
    valid_int = 0 if valid else 1
    allowed_int = 0 if allowed else 1
    query = (
        'SELECT labels, exclusion_values'
        ' FROM exclusions'
       f' WHERE allowed = {allowed_int}'
           f' AND valid = {valid_int}'
    )
    for verbose_name in permutations:
        query += (
            ' AND ('
               f' labels LIKE \'{verbose_name};;%\''
               f' OR labels LIKE \'%;;{verbose_name}\''
               f' OR labels LIKE \'%;;{verbose_name};;%\''
            ' )'
        )

    with _DB as conn:
        cursor = conn.cursor()
        try:
            response = cursor.execute(query).fetchall()
        finally:
            cursor.close()

    perm_list = list(permutations)
    exclusions: list[list[str]] = []
    for labels, values in response:
        try:
            label_split = str(labels).split(';;')
        except ValueError:
            raise DatabaseError(f'Invalid exclusion labels: {labels}')

        if set(label_split) != set(permutations):
            continue

        perm_indexes: dict[int, int] = []
        for i, label in enumerate(label_split):
            try:
                perm_indexes[i] = perm_list.index(label)
            except ValueError:
                raise DatabaseError(
                    f'Incorrect response: {label} not in {permutations}'
                )

        try:
            value_split = str(values).split(';;')
        except ValueError:
            raise DatabaseError(f'Invalid exclusion values: {values}')

        if len(value_split) != len(label_split):
            raise DatabaseError(
                f'Invalid exclusion value length: expected {len(label_split)},'
                f' but got {len(value_split)}'
            )

        value_list: list[str] = [''] * len(perm_indexes)
        for i, value in enumerate(value_split):
            index = perm_indexes[i]
            value_list[index] = value

        exclusions.append(value_split)

    return exclusions

def get_version_sources() -> set[str]:
    query = (
        'SELECT value'
        ' FROM permutation_valid_data'
       f' WHERE verbose_name = \'Version Source\''
    )
    with _DB as conn:
        cursor = conn.cursor()
        try:
            response = cursor.execute(query).fetchall()
        finally:
            cursor.close()

    return set(map(lambda item: item[0], response))


def get_technology_groups() -> set[str]:
    query = (
        'SELECT value'
        ' FROM permutation_valid_data'
       f' WHERE verbose_name = \'TechGroup\''
    )
    with _DB as conn:
        cursor = conn.cursor()
        try:
            response = cursor.execute(query).fetchall()
        finally:
            cursor.close()

    return set(map(lambda item: item[0], response))


def get_technology_types() -> set[str]:
    query = (
        'SELECT value'
        ' FROM permutation_valid_data'
       f' WHERE verbose_name = \'TechType\''
    )
    with _DB as conn:
        cursor = conn.cursor()
        try:
            response = cursor.execute(query).fetchall()
        finally:
            cursor.close()

    return set(map(lambda item: item[0], response))


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


def __insert_eul_table() -> None:
    import pylightxl as xl

    file_path = resources.get_path('permutation_tool.xlsm')
    db = xl.readxl(file_path)
    eul = db.ws('EUL')

    # read data from columns (A = 1, B = 2, ...)
    eul_id = eul.col(1)[1:]
    eul_version = eul.col(2)[1:]
    eul_bldg_type = eul.col(3)[1:]
    eul_description = eul.col(4)[1:]
    eul_sector = eul.col(5)[1:]
    eul_use_category = eul.col(6)[1:]
    eul_use_sub_category = eul.col(7)[1:]
    eul_tech_group = eul.col(8)[1:]
    eul_tech_type = eul.col(9)[1:]
    eul_basis_type = eul.col(10)[1:]
    eul_basis_value = eul.col(11)[1:]
    eul_def_eflh = eul.col(12)[1:]
    eul_max_years = eul.col(13)[1:]
    eul_hrs_of_use_category = eul.col(14)[1:]
    eul_yrs = eul.col(15)[1:]
    rul_yrs = eul.col(16)[1:]
    eul_start_date = eul.col(17)[1:]
    eul_expiry_date = eul.col(18)[1:]
    eul_proposed_flag = eul.col(19)[1:]

    # collect data into a 2D matrix
    vals: list[list[int | float | str | bool | None]] = []
    for i, _id in enumerate(eul_id):
        vals.append(
            [
                _id,
                eul_version[i],
                eul_bldg_type[i],
                eul_description[i],
                eul_sector[i],
                eul_use_category[i],
                eul_use_sub_category[i],
                eul_tech_group[i],
                eul_tech_type[i],
                eul_basis_type[i],
                eul_basis_value[i],
                eul_def_eflh[i],
                eul_max_years[i],
                eul_hrs_of_use_category[i],
                eul_yrs[i],
                rul_yrs[i],
                eul_start_date[i],
                eul_expiry_date[i],
                0 if eul_proposed_flag[i] else 1
            ]
        )

    # sanitize data
    for y, row in enumerate(vals):
        for x, item in enumerate(row):
            if item == '':
                vals[y][x] = None

    query = (
        'INSERT INTO eul'
        ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    )
    connection = sql.connect('src/etrm/resources/database.db')
    with connection:
        cursor = connection.cursor()
        for row in vals:
            print(f'Inserting: {tuple(row)})')
            cursor.execute(query, tuple(row))
        cursor.close()
        connection.commit()


def __insert_ntg_table() -> None:
    file_path = resources.get_path('permutation_tool.xlsm')
    db = xl.readxl(file_path)
    eul = db.ws('netToGrossRatio')

    ntg_id = eul.col(1)[1:]
    ntg_version = eul.col(2)[1:]
    ntg_description = eul.col(3)[1:]
    ntgr_kwh = eul.col(4)[1:]
    ntgr_therm = eul.col(5)[1:]
    ntg_start = eul.col(6)[1:]
    ntg_end = eul.col(7)[1:]
    ntg_mit = eul.col(8)[1:]
    ntg_mat = eul.col(9)[1:]
    ntg_deliv = eul.col(10)[1:]
    ntg_pf = eul.col(11)[1:]

    vals: list[list[int | float | str | bool | None]] = []
    for i, _id in enumerate(ntg_id):
        vals.append(
            [
                _id,
                ntg_version[i],
                ntg_description[i],
                ntgr_kwh[i],
                ntgr_therm[i],
                ntg_start[i],
                ntg_end[i],
                ntg_mit[i],
                ntg_mat[i],
                ntg_deliv[i],
                0 if ntg_pf[i] else 1
            ]
        )

    for y, row in enumerate(vals):
        for x, item in enumerate(row):
            if item == '':
                vals[y][x] = None

    query = (
        'INSERT INTO ntg'
        ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    )
    connection = sql.connect('src/etrm/resources/database.db')
    with connection:
        cursor = connection.cursor()
        for row in vals:
            print(f'Inserting: {tuple(row)})')
            cursor.execute(query, tuple(row))
        cursor.close()
        connection.commit()


def __insert_valid_data() -> None:
    file_path = resources.get_path('permutation_tool.xlsm')
    db = xl.readxl(file_path)
    dv = db.ws('DataValue')
    data: dict[str, list[int | float | str | None]] = {}

    def get_column(col_index: str | int) -> list[int | float | str | bool]:
        if isinstance(col_index, str):
            col_index = ord(col_index.upper()) - 64
        return dv.col(col_index)

    def sanitize_column(vals: list[int | float | str | bool]
                       ) -> list[int | float | str | None]:
        _vals = vals.copy()
        for i, val in enumerate(_vals):
            if isinstance(val, bool):
                _vals[i] = 0 if val else 1
            elif isinstance(val, str) and val == '':
                _vals[i] = None
        return _vals

    def add_column(col_index: str | int) -> None:
        col = get_column(col_index)
        label = col[0]
        vals = list(
            filter(
                lambda val: val is not None,
                sanitize_column(col[1:])
            )
        )
        data[label] = vals

    # Effecting Useful Life ID
    add_column('A')

    # Program Administrator
    add_column('D')

    # Technology Group
    add_column('G')

    # Technology Type
    add_column('H')

    # Version Source
    add_column('K')

    # Delivery Type
    add_column('N')

    # Measure Impact Type
    add_column('S')

    deliv_type = list(
        filter(
            lambda val: val is not None,
            sanitize_column(get_column('N')[1:])
        )
    )
    deliv_start = list(
        filter(
            lambda val: val is not None,
            sanitize_column(get_column('O')[1:])
        )
    )
    deliv_expire = sanitize_column(get_column('P')[1:])
    deliv_params = zip(deliv_type, deliv_start, deliv_expire)

    meas_impact_type = list(
        filter(
            lambda val: val is not None,
            sanitize_column(get_column('S')[1:])
        )
    )
    mit_start = list(
        filter(
            lambda val: val is not None,
            sanitize_column(get_column('T')[1:])
        )
    )
    mit_expire = sanitize_column(get_column('U')[1:])
    mit_params = zip(meas_impact_type, mit_start, mit_expire)
    with _DB.connect() as conn:
        cursor = conn.cursor()
        try:
            query = (
                'DELETE FROM permutation_valid_data'
                ' WHERE 1=1'
            )
            cursor.execute(query)

            query = (
                'INSERT INTO permutation_valid_data'
                ' VALUES (?, ?)'
            )
            for label, vals in data.items():
                labels = [label] * len(vals)
                params = zip(labels, vals)
                cursor.executemany(query, params)

            query = (
                'DELETE FROM delivery_type'
                ' WHERE 1=1'
            )
            cursor.execute(query)

            query = (
                'INSERT INTO delivery_type'
                ' VALUES (?, ?, ?)'
            )
            cursor.executemany(query, deliv_params)

            query = (
                'DELETE FROM measure_impact_type'
                ' WHERE 1=1'
            )
            cursor.execute(query)

            query = (
                'INSERT INTO measure_impact_type'
                ' VALUES (?, ?, ?)'
            )
            cursor.executemany(query, mit_params)

            conn.commit()
        finally:
            cursor.close()


def __insert_exclusions() -> None:
    file_path = resources.get_path('permutation_tool.xlsm')
    db = xl.readxl(file_path)
    sheet = db.ws('Exclusion')
    valid_exclusions: list[tuple[str, str, int]] = []
    invalid_exclusions: list[tuple[str, str, int]] = []

    def get_column(index: str | int) -> list[int | float | str | bool]:
        if isinstance(index, str):
            i_val = 0
            for i, val in enumerate(reversed([*index])):
                # is this a (base 26) bird?
                i_val += int((26 ** i) * (ord(val.upper()) - 64))
            index = i_val

        col = sheet.col(index)

        # remove trailing None values
        trail_size = 0
        for val in reversed(col):
            if val != '':
                break

            trail_size += 1

        if trail_size != 0:
            col = col[0:len(col) - trail_size]

        # sanitize remaining values
        for i, val in enumerate(col):
            if val == '':
                col[i] = None
            elif isinstance(val, bool):
                col[i] = 0 if val else 1

        return col

    def add_exclusion(*column_indexes: int | str,
                      valid: bool=True
                     ) -> None:
        cols: list[list[int | float | str | None]] = []
        for index in column_indexes:
            cols.append(get_column(index))

        if not valid:
            exclusions = invalid_exclusions
        else:
            exclusions = valid_exclusions

        max_len = max([len(col) for col in cols])
        for i, col in enumerate(cols):
            col_len = len(col)
            if col_len < max_len:
                cols[i].extend([''] * (max_len - col_len))

        rows = [list(row) for row in zip(*cols)]
        label = ';;'.join(rows[0])
        values = []
        for row in rows[1:]:
            values.append(';;'.join([str(item) for item in row]))

        for value in values:
            value = str(value)
            if 'NOT ALLOWED' in value.upper() or 'REMOVE' in value.upper():
                allowed = 1
            else:
                allowed = 0

            match label:
                case 'Program Administrator Type;;Program Administrator':
                    if any([_value == '' for _value in value.split(';;')]):
                        continue
                case _:
                    if all([_value == '' for _value in value.split(';;')]):
                        break

            exclusions.append((label, value, allowed))

    # measure app type - building vintage
    add_exclusion('A', 'B')

    # sector - building type
    add_exclusion('F', 'G')

    # sector - NTGR ID
    add_exclusion('K', 'L')

    # sector - electric impact profile id
    add_exclusion('P', 'Q')

    # sector - GSIA ID
    add_exclusion('U', 'V')

    # sector - building HVAC
    add_exclusion('Z', 'AA')

    # use category - use sub category
    add_exclusion('AE', 'AF')

    # tech group - tech type
    add_exclusion('AJ', 'AK')

    # measure impact type - version
    add_exclusion('AT', 'AU')

    # delivery type - upstream flag
    add_exclusion('BF', 'BG')

    # measure application type - delivery type
    add_exclusion('BK', 'BL', valid=False)

    # building hvac - delivery type
    add_exclusion('BQ', 'BR', valid=False)

    # building type - delivery type
    add_exclusion('BW', 'BX', valid=False)

    # NTGR ID - NTG version - measure impact type
    add_exclusion('CB', 'CC', 'CD')

    # NTGR ID - NTG version - measure application type
    add_exclusion('CH', 'CI', 'CJ')

    # NTGR ID - NTG version - delivery type
    add_exclusion('CN', 'CO', 'CP')

    # EUL ID - EUL version - use category
    add_exclusion('CT', 'CU', 'CV')

    # EUL ID - EUL version - use sub category
    add_exclusion('CZ', 'DA', 'DB')

    # EUL ID - EUL version - tech group
    add_exclusion('DF', 'DG', 'DH')

    # EUL ID - EUL version - tech type
    add_exclusion('DL', 'DM', 'DN')

    # measure application type - first baseline case
    add_exclusion('DR', 'DS')

    # measure application type - second baseline case
    add_exclusion('DW', 'DX')

    # program administrator type - building location
    add_exclusion('AY', 'AZ')

    # program administrator type - program administrator
    add_exclusion('AY', 'BB')

    with _DB.connect() as conn:
        cursor = conn.cursor()
        try:
            query = (
                'DELETE FROM exclusions'
                ' WHERE 1=1'
            )
            cursor.execute(query)

            query = (
                'INSERT INTO exclusions'
                ' VALUES (?, ?, ?, 0)'
            )
            cursor.executemany(query, valid_exclusions)

            query = (
                'INSERT INTO exclusions'
                ' VALUES (?, ?, ?, 1)'
            )
            cursor.executemany(query, invalid_exclusions)

            conn.commit()
        finally:
            cursor.close()
