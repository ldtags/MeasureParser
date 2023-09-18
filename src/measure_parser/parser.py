import json
from typing import Optional, TextIO
try:
    from types import SimpleNamespace as Namespace
except ImportError:
    from argparse import Namespace
from src.measure_parser.objects import Measure, Permutation
from src.measure_parser.htmlparser import CharacterizationParser
from src.measure_parser.data.parameters import ALL_PARAMS
from src.measure_parser.data.permutations import ALL_PERMUTATIONS
from src.measure_parser.data.valuetables import (
    ALL_SHARED_TABLES,
    ALL_VALUE_TABLES
)
from src.measure_parser.exceptions import (
    RequiredParameterError,
    MeasureFormatError,
    UnknownPermutationError
)


class MeasureParser:
    """The parser for eTRM measure JSON files

    Attributes:
        measure (Measure): an object containing data from the measure file
        out (Optional[TextIO]): a file stream for the log file
        ordered_params (list[str]): an ordered list of the names of all
                                    valid parameters
        ordered_val_tables (list[str]): an ordered list of the names of
                                        all valid non-shared value tables
        ordered_sha_tables (list[str]): an ordered list of the names of
                                        all valid shared value tables
    """

    def __init__(self, measure_file: TextIO, console: bool=False):
        self.measure: Measure = Measure(
            json.loads(measure_file.read(),
                       object_hook=lambda dict: Namespace(**dict)))
        self.out: Optional[TextIO] = None
        if not console:
            self.out = open('output-' + self.measure.id + '.txt', 'w')

        try:
            self.ordered_params: list[str] \
                = get_ordered_params(self.measure)
            self.ordered_val_tables: list[str] \
                = get_ordered_value_tables(self.measure)
            self.ordered_sha_tables: list[str] \
                = get_ordered_shared_tables(self.measure)
        except RequiredParameterError as err:
            print('ERROR - the measure is missing required information\n',
                  err)
            return
        except MeasureFormatError as err:
            print(f'ERROR - the measure is incorrectly formatted:\n{err}')
            return
        except Exception as err:
            print(f'ERROR - something went wrong:\n{err}')
            return

    # defines the control flow for the generic parsing of @measure
    def parse(self) -> None:
        print(f'starting to parse measure {self.measure.id}\n')

        self.print_measure_details()

        print('validating parameters')
        self.validate_parameters()
        print('finished validating parameters\n')
        
        print('validating tables')
        self.validate_tables()
        print('finished validating tables\n')

        self.print_value_tables()
        
        print('validating exclusion tables')
        self.validate_exclusion_tables()
        print('finished validating exclusion tables\n')

        self.print_calculations()
        
        print('validating permutations')
        self.validate_permutations()
        print('finished validating permutations\n')

        self.print_permutations()

        print('parsing characterizations')
        self.parse_characterizations()
        print('finished parsing characterizations\n')
        
        print(f'finished parsing measure {self.measure.id}')


    def print_measure_details(self) -> None:
        print('Measure Details: ', file=self.out)
        print('\tMeasure Version ID: ' + self.measure.version_id,
              file=self.out)
        print('\tMeasure Name: ' + self.measure.name, file=self.out)
        print('\tPA Lead: ' + self.measure.pa_lead, file=self.out)
        print('\tStart Date: ' + self.measure.start_date, file=self.out)
        print('\tEnd Date: ' + self.measure.end_date, '\n\n',
              file=self.out)


    def validate_parameters(self) -> None:
        print('Validating Parameters:', file=self.out)
        print('\tMeasure Specific Parameters: ',
              list(map(lambda param: param.name, self.measure.params)),
              file=self.out)
        print('\n\tUnexpected Shared Parameters: ', list(
              map(lambda param: param.version.version_string,
                  self.measure.remove_unknown_params(
                      self.ordered_params))),
              file=self.out)
        print('\tMissing Shared Parameters: ',
              self.validate_param_existence(),
              file=self.out)
        print('\n\tParameter Order:', file=self.out)
        in_order: bool = self.validate_param_order()
        if in_order:
            print('\t\tAll shared parameters are in the correct order',
                  file=self.out)
        else:
            print('', file=self.out)


    def validate_tables(self):
        print('\nValidating Value Tables:', file=self.out)
        print('\tUnexpected Shared Tables: ', list(
              map(lambda table: table.version.version_string,
                  self.measure.remove_unknown_shared_tables(
                      self.ordered_sha_tables))),
              file=self.out)
        print('\tMissing Shared Tables: ',
              self.validate_shared_table_existence(),
              file=self.out)

        print('\n\tUnexpected Non-Shared Tables: ', list(
              map(lambda table: table.api_name,
                  self.measure.remove_unknown_value_tables(
                      self.ordered_val_tables))),
              file=self.out)
        print('\tMissing Non-Shared Tables: ',
              self.validate_value_table_existence(),
              file=self.out)

        print('\n\tValue Table Order: ', file=self.out)
        if self.validate_shared_table_order():
            print('\t\tAll shared value tables are in the correct order',
                  file=self.out)
        if self.validate_value_table_order():
            print('\t\tAll non-shared value tables are in the '
                    + 'correct order',
                  file=self.out)


    # validates that all shared value tables names in @ordered_sha_tables
    # correlate to a shared value table in @measure
    def validate_shared_table_existence(self) -> list[str]:
        missing_tables: list[str] = []
        for table in self.ordered_sha_tables:
            if not self.measure.contains_shared_table(table):
                missing_tables.append(table)
        return missing_tables

    # validates that all non-shared value tables names in
    # @ordered_val_tables correlate to a non-shared value table in
    # @measure
    def validate_value_table_existence(self) -> list[str]:
        missing_tables: list[str] = []
        for table in self.ordered_val_tables:
            if not self.measure.contains_value_table(table):
                missing_tables.append(table)
        return missing_tables

    # validates that all parameter names in @ordered_params correlates
    # to a parameter in @measure
    #
    # Returns
    #   list[str]: the list of parameter names associated with all missing
    #              shared parameters
    def validate_param_existence(self) -> list[str]:
        missing_params: list[str] = []
        for param in self.ordered_params:
            if not self.measure.contains_param(param):
                missing_params.append(param)
        return missing_params

    # validates that all parameters in @measure are in the same order as the
    # parameters represented by @ordered_params
    #
    # Parameters:
    #   measure (Measure): the measure object being parsed
    #   ordered_params (list[str]): the list of all valid parameter names
    def validate_param_order(self) -> bool:
        for param in self.measure.shared_params:
            param_name: str = param.version.version_string
            index: int = self.ordered_params.index(param_name)
            if param.order != (index + 1):
                print('\t\tShared parameters may be out of order,',
                      'please review the QA/QC guidelines',
                      file=self.out)
                return False
        return True

    # validates that all non-shared value tables in @measure are in the same
    # order as the non-shared value tables represented by @ordered_tables
    #
    # Parameters:
    #   measure (Measure): the measure object being parsed
    #   ordered_tables (list[str]): the list of all valid non-shared value
    #                               table names
    def validate_value_table_order(self) -> bool:
        for table in self.measure.value_tables:
            table_name: str = table.api_name
            index: int = self.ordered_val_tables.index(table_name)
            if table.order != (index + 1):
                print(f'\t\tNon-shared value tables may be out of order,',
                      'please review the QA/QC guidelines',
                      file=self.out)
                return False
        return True

    # validates that all shared value tables in @measure are in the same
    # order as the non-shared value tables represented by @ordered_tables
    def validate_shared_table_order(self) -> list[str]:
        for table in self.measure.shared_tables:
            table_name: str = table.version.version_string
            index: int = self.ordered_sha_tables.index(table_name)
            if table.order != (index + 1):
                print('\t\tShared value tables may be out of order,',
                      'please review the QA/QC guidelines',
                      file=self.out)
                return False
        return True

    # validates that all permutations have the correct mapped name
    def validate_permutations(self) -> None:
        print('\nValidating Permutations:', file=self.out)
        for permutation in self.measure.permutations:
            try:
                valid_name: str = self.__get_valid_perm_name(permutation)
                mapped_name: str = permutation.mapped_name
                if mapped_name != valid_name:
                    print('\tIncorrect Permutation',
                          f'({permutation.reporting_name})',
                          f'- {mapped_name} should be {valid_name}',
                          file=self.out)
            except UnknownPermutationError as err:
                print(f'UNKNOWN PERMUTATION: {err.name}', file=self.out)

    # returns the valid name for @permutation
    #
    # Paramters:
    #   permutation (Permutation): the permutation being validated
    #
    # Returns:
    #   str: the valid name of @permutation
    def __get_valid_perm_name(self, permutation: Permutation) -> str:
        name: str = permutation.reporting_name
        data: dict[str, str] = ALL_PERMUTATIONS.get(name, None)
        if data == None:
            raise UnknownPermutationError(name=name)

        mapped_name: str = permutation.mapped_name
        valid_name: Optional[str] = data.get('validity', None)
        if valid_name == None:
            return mapped_name

        cond_names: list[str] = data.get('conditional', [])
        if len(cond_names) == 0:
            return valid_name

        get_param: function = self.measure.get_param
        get_value_table: function = self.measure.get_value_table
        if name == 'BaseCase2nd' \
                and 'AR' in get_param('MeasAppType').labels:
            valid_name = cond_names[0]
        elif name == 'Upstream_Flag' \
                and 'UpDeemed' in get_param('DelivType').labels:
            valid_name = cond_names[0]
        elif name == 'WaterUse' \
                and get_param('waterMeasureType') != None:
            valid_name = cond_names[0]
        elif name == 'ETP_Flag' \
                and get_value_table('emergingTech') != None:
            valid_name = cond_names[0]
        elif name == 'ETP_YearFirstIntroducedToPrograms' \
                and get_value_table('emergingTech') != None:
            valid_name = cond_names[0]

        return valid_name


    def validate_exclusion_tables(self) -> None:
        print('\nAll Exclusion Tables:', file=self.out)
        for table in self.measure.exclusion_tables:
            name: str = table.name
            print(f'\t{name.replace(" ", "")}:', file=self.out)
            if ' ' in name:
                print('\t\t\tWarning: Whitespace(s) detected in table',
                      'name, please remove the whitespace(s)',
                      file=self.out)

            params: list[str] = table.determinants
            print(f'\t\tParams: {params}', file=self.out)
            if name.count('-') != (len(params) - 1):
                print('\t\t\tWarning: Amount of hyphens found in the',
                      'table name does not equal one less than the',
                      'amount of parameters',
                      file=self.out)
            print(file=self.out)

    # calls the characterization parser to parse each characterization
    # in @measure
    def parse_characterizations(self) -> None:
        parser: CharacterizationParser \
            = CharacterizationParser(out=self.out, tabs=1)
        print('\nParsing Characterizations:', file=self.out)
        for characterization in self.measure.characterizations:
            print(f'\tparsing {characterization.name}')
            parser.parse(characterization)

    # prints a representation of every non-shared value table in @measure
    def print_value_tables(self) -> None:
        print('\n\nAll Value Tables:', file=self.out)
        for table in self.measure.value_tables:
            print(f'\tTable Name: {table.name}', file=self.out)
            print(f'\t\tAPI Name: {table.api_name}', file=self.out)
            print('\t\tColumns:', file=self.out)
            for column in table.columns:
                print(f'\t\t\tColumn Name: {column.name}',
                      file=self.out)
                print(f'\t\t\t\tAPI Name: {column.api_name}',
                      file=self.out)
            print(file=self.out)

    # prints out every calculation in @measure' name and API name
    def print_calculations(self) -> None:
        print('\nAll Calculations:', file=self.out)
        for calculation in self.measure.calculations:
            print(f'\tCalculation Name: {calculation.name}',
                  file=self.out)
            print(f'\t\tAPI Name: {calculation.api_name}',
                  file=self.out)
            print(f'\t\tUnit: {calculation.unit}', file=self.out)
            print(f'\t\tParams: {calculation.determinants}\n',
                  file=self.out)

    # prints out every permutation in @measure's reporting name,
    # verbose name, and mapped field
    def print_permutations(self) -> None:
        print('\n\nAll Permutations:', file=self.out)
        for permutation in self.measure.permutations:
            try:
                perm_data = ALL_PERMUTATIONS[permutation.reporting_name]
            except:
                raise MeasureFormatError()

            try:
                verbose_name = perm_data['verbose']
                print(f'\t{permutation.reporting_name}:'
                      f'\n\t\tVerbose Name: {verbose_name}',
                      f'\n\t\tMapped Field: {permutation.mapped_name}\n',
                      file=self.out)
            except:
                continue

    # method to print to the parser's out stream
    def printo(self, *strings: str) -> None:
        concat_string: str = ''
        for string in strings:
            concat_string += string
        print(concat_string, file=self.out)

# returns the ordered list of all parameters to check for
#
# Parameters:
#   measure (Measure): the measure object being parsed
#
# Returns:
#   list[str]: a list of parameter names
def get_ordered_params(measure: Measure) -> list[str]:
    ordered_params = ALL_PARAMS

    try:
        if not measure.is_DEER():
            ordered_params = filter_dict(ordered_params, 'DEER')

        if not measure.is_GSIA_nondef():
            ordered_params = filter_dict(ordered_params, 'GSIA')

        if not (measure.contains_MAT_label('AR')
                or measure.contains_MAT_label('AOE')):
            ordered_params = filter_dict(ordered_params, 'MAT')

        if not measure.is_WEN():
            ordered_params = filter_dict(ordered_params, 'WEN')

        if not measure.is_sector_nondef():
            ordered_params = filter_dict(ordered_params, 'NTG')

        if not measure.is_interactive():
            ordered_params = filter_dict(ordered_params, 'INTER')
        else:
            ordered_params = filter_inter_params(measure,
                                                 ordered_params)
    except Exception as err:
        raise err

    return list(ordered_params.keys())

# returns the ordered list of all non-shared value tables to check for
#
# Parameters:
#   measure (Measure): the measure object being parsed
#
# Returns:
#   list[str]: a list of non-shared value table names
def get_ordered_value_tables(measure: Measure) -> list[str]:
    ordered_val_tables = ALL_VALUE_TABLES

    try:
        if not measure.is_DEER():
            ordered_val_tables = filter_dict(ordered_val_tables, 'DEER')

        if not (measure.contains_MAT_label('AR')
                or measure.contains_MAT_label('AOE')):
            ordered_val_tables \
                = filter_dict(ordered_val_tables, 'NRNC+ARAOE')

        if not (measure.contains_MAT_label('NR')
                or measure.contains_MAT_label('NC')):
            ordered_val_tables \
                = filter_dict(ordered_val_tables, 'NRNC+ARAOE')

        if not measure.contains_value_table('emergingTech'):
            ordered_val_tables = filter_dict(ordered_val_tables, 'ET')

        if not measure.is_deemed():
            ordered_val_tables = filter_dict(ordered_val_tables, 'DEEM')

        if not measure.is_fuel_sub():
            ordered_val_tables = filter_dict(ordered_val_tables, 'FUEL')

        if not measure.is_interactive():
            ordered_val_tables = filter_dict(ordered_val_tables, 'INTER')
        else:
            ordered_val_tables \
                    = filter_inter_value_tables(measure,
                                                ordered_val_tables)
    except Exception as err:
        raise err

    return list(ordered_val_tables.keys())

# returns the ordered list of all shared value tables to check for
#
# Parameters:
#   measure (Measure): the measure object being parsed
#
# Returns:
#   list[str]: a list of shared value table names
def get_ordered_shared_tables(measure: Measure) -> list[str]:
    ordered_sha_tables = ALL_SHARED_TABLES

    try:
        if not measure.is_DEER():
            ordered_sha_tables = filter_dict(ordered_sha_tables, 'DEER')

        if not measure.is_GSIA_default():
            ordered_sha_tables \
                = filter_dict(ordered_sha_tables, 'GSIA-DEF')

        if not measure.is_GSIA_nondef():
            ordered_sha_tables = filter_dict(ordered_sha_tables, 'GSIA')

        if not (measure.contains_MAT_label('AR')
                or measure.contains_MAT_label('AOE')):
            ordered_sha_tables = filter_dict(ordered_sha_tables, 'ARAOE')

        if not measure.is_WEN():
            ordered_sha_tables = filter_dict(ordered_sha_tables, 'WEN')

        if not measure.is_res_default():
            ordered_sha_tables \
                = filter_dict(ordered_sha_tables, 'RES-DEF')
        else:
            ordered_sha_tables = filter_dict(ordered_sha_tables, 'RES')

        if not measure.is_nonres_default():
            ordered_sha_tables \
                = filter_dict(ordered_sha_tables, 'RES-NDEF')
        else:
            ordered_sha_tables = filter_dict(ordered_sha_tables, 'RES')

        if not measure.is_interactive():
            ordered_sha_tables = filter_dict(ordered_sha_tables, 'INTER')
        else:
            ordered_sha_tables \
                = filter_inter_shared_tables(measure, ordered_sha_tables)
    except Exception as err:
        raise err

    return list(ordered_sha_tables.keys())

# returns the provided dict excluding any item whose value matches @flag
#
# Parameters:
#   ordered_list (dict[str, str]): the dict being filtered
#   flag (str): the flag to filter the dict for
#
# Returns:
#   dict[str, str]: the filtered dict
def filter_dict(ordered_list: dict[str, str],
                flag: str) -> dict[str, str]:
    return {key:val for (key, val) in ordered_list.items() if val != flag}

# filters the provided list in accordance to the interactive measure specs
#
# Parameters:
#   measure (Measure):  the measure object being parsed
#   ordered_params (dict[str, str]): an ordered dict of parameter names
#
# Returns:
#   dict[str, str]: the dict filtered in accordance to the interactive
#   measure specs
def filter_inter_params(measure: Measure,
                        ordered_params: dict[str, str]
                       ) -> dict[str, str]:
    if not measure.contains_param('LightingType'):
        del ordered_params['LightingType']

    return ordered_params

# filters the provided list in accordance to the interactive measure specs
#
# Parameters:
#   measure (Measure):  the measure object being parsed
#   ordered_tables (dict[str, str]): an ordered dict of non-shared table
#                                    names
#
# Returns:
#   dict[str, str]: the dict filtered in accordance to the interactive
#   measure specs
def filter_inter_value_tables(measure: Measure,
                              ordered_tables: dict[str, str]
                             ) -> dict[str, str]:
    if not measure.contains_value_table('IEApplicability'):
        del ordered_tables['IEApplicability']

    return ordered_tables

# filters the provided list in accordance to the interactive measure specs
#
# Parameters:
#   measure (Measure): the measure object being parsed
#   ordered_tables (dict[str, str]): an ordered dict of shared table names
#
# Returns:
#   dict[str, str]: the dict filtered in accordance to the interactive
#                   measure specs
def filter_inter_shared_tables(measure: Measure,
                               ordered_tables: dict[str, str]
                              ) -> dict[str, str]:
    if not measure.contains_shared_table('commercialInteractiveEffects'):
        del ordered_tables['commercialInteractiveEffects']

    if not measure.contains_shared_table('residentialInteractiveEffects'):
        del ordered_tables['residentialInteractiveEffects']

    return ordered_tables