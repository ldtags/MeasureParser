from __future__ import annotations
import os
import sqlite3
from typing import Optional, final, TYPE_CHECKING
from argparse import Namespace

from src import utils
from src.dbservice.basedb import (
    BaseDatabase,
    queryfy,
    listify
)
from src.dbservice.exceptions import (
    DatabaseConnectionError,
    DatabaseContentError
)

if TYPE_CHECKING:
    from src.models import Measure


class LocalDatabase(BaseDatabase):
    """Data interaction layer for the local database."""

    def __init__(self,
                 db_name: str = 'database.db',
                 db_dir: str = 'resources'):
        self.path = utils.resource_path(db_name, db_dir)
        if not os.path.isfile(self.path):
            raise DatabaseConnectionError(f'{self.path} is not a valid database')

        self.connection = sqlite3.connect(self.path)
        self.cursor = self.connection.cursor()
        if len(self.cursor.execute('SELECT name FROM sqlite_master').fetchall()) < 1:
            raise DatabaseContentError('database is empty')

    def close(self):
        self.cursor.close()
        self.connection.close()

    def __enter__(self) -> sqlite3.Connection:
        return self.connection

    def __exit__(self):
        self.close()

    @final
    def get_measure(self, path_to_json: str) -> object:
        return utils.json_obj(path_to_json)

    @final
    def get_param_api_names(self, measure: Measure | None = None) -> list[str]:
        """Queries the database for shared parameter names.

        Parameters:
            measure `Measure` : a measure object that will determine criteria
                                and allow for accurate data processing

        Returns:
            `list[str]` : a list of shared parameter names
        """

        query: str = 'SELECT api_name FROM parameters'
        if measure != None:
            query += f' WHERE criteria IN {queryfy(measure.get_criteria())}'
        query += ' ORDER BY ord ASC'
        response: list[tuple[str,]] = self.cursor.execute(query).fetchall()
        param_names: list[str] = listify(response)

        # measure specific post-processing
        if measure != None:
            if (measure.is_interactive()
                    and not measure.contains_param('LightingType')):
                param_names.remove('LightingType')

        return listify(response)

    @final
    def get_value_table_api_names(self, criteria: list[str]) -> list[str]:
        """Queries the database for a list of non-shared value table names
        specified by `criteria`.
        
        Parameters:
            criteria `list[str]` : a list of criteria

        Returns:
            `list[str]` : the list of non-shared value table names
        """

        query: str = 'SELECT api_name FROM tables WHERE shared = 0'
        query += ' AND criteria IN ' + queryfy(criteria)
        query += ' ORDER BY ord ASC'
        tables: list[str] = self.cursor.execute(query).fetchall()
        return listify(tables)

    @final
    def get_shared_table_api_names(self, criteria: list[str]) -> list[str]:
        """Queries the database for a list of shared value table names specified
        by `criteria`.

        Parameters:
            criteria `list[str]` : a list of criteria

        Returns:
            `list[str]` : the list of shared value table names
        """

        query: str = 'SELECT api_name FROM tables WHERE shared != 0'
        query += ' AND criteria IN ' + queryfy(criteria)
        query += ' ORDER BY ord ASC'
        tables: list[str] = self.cursor.execute(query).fetchall()
        return listify(tables)

    @final
    def get_table_api_names(self,
                            measure: Measure | None = None,
                            shared: bool = False,
                            nonshared: bool = False) -> list[str]:
        """Queries the database for value table names.

        Parameters:
            measure     `Measure`   : a measure object that will determine
                                      criteria and allow for accurate data
                                      processing
            shared      `bool`      : limit tables queried to shared tables
            nonshared   `bool`      : limit tables queried to nonshared tables

        Returns:
            `list[str]` : a list of value table names
        """
    
        query: str = 'SELECT api_name, ord FROM tables'

        if measure != None or shared or nonshared:
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
        if measure != None:
            criteria = measure.get_criteria()
            query += f'criteria IN {queryfy(criteria)}'

        query += ' ORDER BY ord ASC'
        self.cursor.execute(query)
        tables: dict[int, str] \
            = {table[1]: table[0] for table in self.cursor.fetchall()}

        if measure != None:
            # Adding tables that can either be shared or non-shared.
            #
            # These tables are currently all optional, regardless of
            #   how they are defined in the database.
            self.cursor.execute('SELECT api_name, ord FROM tables'
                                    ' WHERE shared = -1'
                                   f' AND criteria IN {queryfy(criteria)}'
                                    ' ORDER BY ord ASC')
            for table in self.cursor.fetchall():
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

        if measure != None:
            table_names = self.filter_optional_tables(tables,
                                                      table_names,
                                                      measure)

        return table_names

    @final
    def get_standard_table_names(self,
                                 measure: Measure | None = None
                                 ) -> dict[str, str]:
        """Queries for nonshared value table standard names.

        Parameters:
            measure `Measure` : a measure object used for specifying
                                which tables to query for

         Returns:
            `dict[str, str]` : table api_names mapped to the standard name
        """

        standard_names: dict[str, str] = {}
        query = 'SELECT api_name, name FROM tables WHERE shared = 0'
        if measure != None:
            query += f' AND criteria IN {queryfy(measure.get_criteria())}'
        response: list[tuple[str, str]] = self.cursor.execute(query).fetchall()
        for names in response:
            standard_names[names[0]] = names[1]
        return standard_names

    @final
    def filter_optional_tables(self,
                               tables: dict[int, str],
                               table_names: list[str],
                               measure: Measure) -> list[str]:
        """Filters out optional tables that don't exist in the measure.

        Parameters:
            tables      `dict[int, str]`    : a dict mapping the order
                                              index to table name
            table_names `list[str]`         : a list of table names
            measure     `Measure`           : a measure object

        Returns:
            `list[str]` : the filtered list of table names
        """

        names: list[str] = table_names.copy()

        self.cursor.execute('SELECT api_name FROM tables WHERE optional = 0')
        response: list[tuple[str,]] = self.cursor.fetchall()
        optional_tables: list[str] = [element[0] for element in response]

        for table_name in tables.values():
            if ((table_name in optional_tables)
                    and not measure.contains_table(table_name)):
                names.remove(table_name)

        return names

    @final
    def get_table_columns(self,
                          measure: Measure | None = None,
                          table_api_name: str | None = None
                         ) -> dict[str, list[dict[str, str]]]:
        """Queries the database for non-shared value table columns.

        Parameters:
            measure         `Measure`   : a measure used to determine table
                                          column criteria,
                                          does not limit table columns queried
                                          if not included
            table_api_name  `str`       : limit columns to only columns
                                          associated with this table api name

        Returns:
           `dict[str, list[dict[str, str]]]` : a dict that maps table api names
                                               to their associated columns
               table columns in this dict are formatted as:
                   'table_api' : the api_name of the associated value table
                   'name'      : the name of the table column
                   'api_name'  : the api_name of the table column
                   'unit'      : the unit of the column
        """

        query = 'SELECT table_api, name, api_name, unit FROM table_columns'

        if table_api_name != None:
            query += f' WHERE table_api = {table_api_name}'

        if measure != None:
            criteria = measure.get_table_column_criteria()
            if not table_api_name:
                query += ' WHERE '
            else:
                query += ' AND '
            query += 'criteria IS NULL'

            if len(criteria) > 0:
                query += f' OR criteria IN {queryfy(criteria)}'

        response: list[tuple] = self.cursor.execute(query).fetchall()
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

    @final
    def get_permutations(self) -> list[tuple[str, str, Optional[str]]]:
        """Queries the database for all permutations.

        Returns:
            `list[tuple[str, str, Optional[str]]]` : a list of permutations
                permutations in this format are specified as:
                    (reporting_name, verbose_name, valid_name)
        """

        query = 'SELECT reporting_name, verbose_name, valid_name'
        query += ' FROM permutation_names'
        response = self.cursor.execute(query).fetchall()
        return listify(response)

    @final
    def get_permutation_data(self, reporting_name: str) -> dict[str, str]:
        """Queries the database for permutation data for the permutation
        associated with `reporting_name`.

        Parameters:
            reporting_name `str` : the reporting name of the desired
                                   permutation

        Returns:
            `dict[str, str]` : a dict representation of permutation data
                Values in this dict are formatted as:
                    {
                        'verbose'  : str
                        'valid'    : str
                    }
        """

        query = 'SELECT verbose_name, valid_name FROM permutation_names'
        query += f' WHERE reporting_name = \"{reporting_name}\"'
        response = self.cursor.execute(query).fetchall()
        response_list: list[str] = listify(response)
        if len(response_list) == 0:
            return ('', None)

        return {'verbose': response_list[0],
                'valid': response_list[1] if len(response_list) > 1 else None}

    @final
    def get_permutation_names(self) -> list[str]:
        """Retrieves a list of all permutation names."""

        query = 'SELECT reporting_name FROM permutation_names'
        self.cursor.execute(query)
        response: list[tuple[str,]] = self.cursor.fetchall()
        return listify(response)

    @final
    def get_all_characterization_names(self) -> list[str]:
        """Retrieves a list of all characterization names."""

        query = 'SELECT name FROM characterizations'
        self.cursor.execute(query)
        response: list[tuple[str,]] = self.cursor.fetchall()
        return listify(response)

    @final
    def get_characterization_names(self, measure: Namespace) -> list[str]:
        """Retrieves a list of characterization names that have mapped values.

        Parameters:
            measure (Namespace): a namespace representation of an eTRM measure
                                 JSON file

        Returns:
            list[str]: a list of characterization names
        """

        char_list: list[str] = []
        for char_name in self.get_all_characterization_names():
            content: str = getattr(measure, char_name, None)
            if content != None:
                char_list.append(char_name)
        return char_list

    def insert_table(self,
                     api_name: str,
                     order: int,
                     shared: bool,
                     optional: bool,
                     criteria: str | None = None):
        """Insert a new record into the `Value Tables` table.

        Parameters:
            api_name    `str`               : the api_name of the value table
            order       `int`               : the order of the value table
            shared      `bool`              : shared or non-shared value table
            optional    `bool`              : specify if the value table is
                                              optional
            criteria    `Optional[str]`     : the criteria (if any) for the
                                              parameter
        """

        self.cursor.execute('SELECT * FROM tables')
        response: list[tuple[str,]] = self.cursor.fetchall()
        tables: list[tuple] = listify(response)
        for table in tables:
            if table[0] == api_name:
                print(f'{api_name} already exists')
                return

        self.cursor.execute('UPDATE tables'
                            ' SET ord = tables.ord + 1'
                           f' WHERE ord >= {order}')

        self.cursor.execute('INSERT INTO tables VALUES (?, ?, ?, ?, ?)',
                            (api_name,
                             order,
                             criteria if criteria else 'REQ',
                             1 if shared else 0,
                             0 if optional else 1))

        self.connection.commit()

    def insert_parameter(self,
                        api_name: str,
                        order: int,
                        criteria: str | None = None):
        """Insert a new shared parameter record into the `Parameters` table.

        Parameters:
            api_name    `str`               : the api_name of the parameter
            order       `int`               : the order of this parameter
            criteria    `Optional[str]`     : the criteria (if any) for the
                                              parameter
        """

        self.cursor.execute('SELECT * FROM parameters')
        response: list[tuple[str,]] = self.cursor.fetchall()
        params: list[tuple] = listify(response)
        for param in params:
            if param[0] == api_name:
                print(f'{api_name} already exists')
                return

        self.cursor.execute('UPDATE parameters'
                            ' SET ord = parameters.ord + 1'
                           f' WHERE ord >= {order}')

        self.cursor.execute('INSERT INTO parameters VALUES (?, ?, ?)',
                            (api_name,
                             order,
                             criteria if criteria else 'REQ'))

        self.connection.commit()

    def insert_permutation(self,
                           reporting_name: str,
                           verbose_name: str,
                           valid_name: str | None = None):
        """Create a new record in the `permutations` table.
        
        Parameters:
            reporting_name  `str`           : the permutation's reporting name
            verbose_name    `str`           : the permutation's verbose name
            valid_name      `Optional[str]` : the permutation's valid name
        """

        self.cursor.execute('INSERT INTO permutations VALUES (?, ?, ?)',
                            (reporting_name,
                             verbose_name,
                             valid_name if valid_name else 'NULL'))

        self.connection.commit()
