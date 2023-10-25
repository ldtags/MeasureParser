import json
from typing import Optional, TextIO
try:
    from types import SimpleNamespace as Namespace
except ImportError:
    from argparse import Namespace
from src.measure_parser.objects import Measure, Permutation
from src.measure_parser.htmlparser import CharacterizationParser
from src.measure_parser.data.permutations import ALL_PERMUTATIONS
import src.measure_parser.dbservice as db
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

    def __init__(self, filename: str):
        measure_file: TextIO = open(filename, 'r')
        self.measure: Measure = Measure(
            json.loads(measure_file.read(),
                       object_hook=lambda dict: Namespace(**dict)))
        measure_file.close()

        self.out: TextIO = open('output-' + self.measure.id + '.txt', 'w')

        try:
            self.ordered_params: list[str] \
                = self.__get_ordered_params()
            self.ordered_val_tables: list[str] \
                = self.__get_ordered_value_tables()
            self.ordered_sha_tables: list[str] \
                = self.__get_ordered_shared_tables()
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
        if self.measure == None:
            print('ERROR - measure parser requires a measure to parse')
            return

        print(f'starting to parse measure {self.measure.id}\n')

        self.log_measure_details()

        print('validating parameters')
        self.validate_parameters()
        print('finished validating parameters\n')

        print('validating exclusion tables')
        self.validate_exclusion_tables()
        print('finished validating exclusion tables\n')

        print('validating tables')
        self.validate_tables()
        print('finished validating tables\n')

        self.log_value_tables()

        self.log_calculations()

        print('validating permutations')
        self.validate_permutations()
        print('finished validating permutations\n')

        self.log_permutations()

        print('parsing characterizations')
        self.parse_characterizations()
        print('finished parsing characterizations\n')

        print(f'finished parsing measure {self.measure.id}')


    def log_measure_details(self) -> None:
        self.log('Measure Details:\n'
                 f'\tMeasure Version ID: {self.measure.version_id}\n'
                 f'\tMeasure Name: {self.measure.name}\n'
                 f'\tPA Lead: {self.measure.pa_lead}\n'
                 f'\tStart Date: {self.measure.start_date}\n'
                 f'\tEnd Date: {self.measure.end_date}\n\n')


    def validate_parameters(self) -> None:
        self.log('Validating Parameters:')
        self.log('\tMeasure Specific Parameters: ',
                 list(map(lambda param: param.name, self.measure.params)))
        self.log('\n\tUnexpected Shared Parameters: ',
                 list(map(lambda param: param.version.version_string,
                          self.measure.remove_unknown_params(
                            self.ordered_params))))
        self.log('\tMissing Shared Parameters: ',
                 self.validate_param_existence())
        self.log('\n\tParameter Order:')
        in_order: bool = self.validate_param_order()
        if in_order:
            self.log('\t\tAll shared parameters are in the correct order')
        else:
            self.log()


    def validate_tables(self):
        self.log('\nValidating Value Tables:')
        self.log('\tUnexpected Shared Tables: ',
                 list(map(lambda table: table.version.version_string,
                          self.measure.remove_unknown_shared_tables(
                            self.ordered_sha_tables))))
        self.log('\tMissing Shared Tables: ',
              self.validate_shared_table_existence())

        self.log('\n\tUnexpected Non-Shared Tables: ',
                 list(map(lambda table: table.api_name,
                          self.measure.remove_unknown_value_tables(
                            self.ordered_val_tables))))
        self.log('\tMissing Non-Shared Tables: ',
                 self.validate_value_table_existence())

        self.log('\n\tValue Table Order: ')
        if self.validate_shared_table_order():
            self.log('\t\tAll shared value tables are in the '
                     'correct order')

        if self.validate_value_table_order():
            self.log('\t\tAll non-shared value tables are in the '
                     'correct order')


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
                self.log('\t\tShared parameters may be out of order, '
                         'please review the QA/QC guidelines')
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
                self.log(f'\t\tNon-shared value tables may be out of '
                         'order, please review the QA/QC guidelines')
                return False
        return True

    # validates that all shared value tables in @measure are in the same
    # order as the non-shared value tables represented by @ordered_tables
    def validate_shared_table_order(self) -> list[str]:
        for table in self.measure.shared_tables:
            table_name: str = table.version.version_string
            index: int = self.ordered_sha_tables.index(table_name)
            if table.order != (index + 1):
                self.log('\t\tShared value tables may be out of order, '
                         'please review the QA/QC guidelines')
                return False
        return True

    # validates that all permutations have the correct mapped name
    def validate_permutations(self) -> None:
        self.log('\nValidating Permutations:')
        invalid_perms: list[str] = []
        for permutation in self.measure.permutations:
            try:
                valid_name: str = self.__get_valid_perm_name(permutation)
                mapped_name: str = permutation.mapped_name
                if mapped_name != valid_name:
                    invalid_perms.append(permutation.reporting_name)
                    self.log('\tIncorrect Permutation '
                             f'({permutation.reporting_name}) '
                             f'- {mapped_name} should be {valid_name}')
            except UnknownPermutationError as err:
                self.log(f'UNKNOWN PERMUTATION: {err.name}')

        if len(invalid_perms) == 0:
            self.log('\tAll permutations are valid')

    # returns the valid name for @permutation
    #
    # Paramters:
    #   permutation (Permutation): the permutation being validated
    #
    # Returns:
    #   str: the valid name of @permutation
    def __get_valid_perm_name(self, permutation: Permutation) -> str:
        reporting_name: str = permutation.reporting_name
        data: tuple[str, Optional[str]] \
            = db.get_permutation_data(reporting_name)

        mapped_name: str = permutation.mapped_name
        if len(data) != 2:
            return mapped_name
        elif data[0] == '':
            raise UnknownPermutationError(name=reporting_name)

        valid_name: str = data[1] or mapped_name
        get_param: function = self.measure.get_shared_parameter
        get_value_table: function = self.measure.get_value_table
        if reporting_name == 'BaseCase2nd' \
                and 'AR' in get_param('MeasAppType').labels:
            valid_name = 'measOffer__descBase2'
        elif reporting_name == 'Upstream_Flag' \
                and 'UpDeemed' in get_param('DelivType').labels:
            valid_name = 'upstreamFlag__upstreamFlag'
        elif reporting_name == 'WaterUse' \
                and get_param('waterMeasureType') != None:
            valid_name = 'p.waterMeasureType__label'
        elif reporting_name == 'ETP_Flag' \
                and get_value_table('emergingTech') != None:
            valid_name = 'emergingTech__projectNumber'
        elif reporting_name == 'ETP_YearFirstIntroducedToPrograms' \
                and get_value_table('emergingTech') != None:
            valid_name = 'emergingTech__introYear'

        return valid_name

    # validates that all exclusion tables follow the following
    #   1. There are no whitespaces in the table name
    #   2. The amount of hyphens in the table name must be one less than
    #            the total amount of parameters
    #
    # prints out all exclusion tables
    def validate_exclusion_tables(self) -> None:
        self.log('\nValidating Exclusion Tables:')
        invalid_tables: list[str] = []
        for table in self.measure.exclusion_tables:
            name: str = table.name
            self.log(f'\t{name.replace(" ", "")}:')
            if ' ' in name:
                if name not in invalid_tables:
                    invalid_tables.append(name)
                self.log('\t\t\tWarning: Whitespace(s) detected in table '
                         'name, please remove the whitespace(s)')

            params: list[str] = table.determinants
            self.log(f'\t\tParams: {params}')
            if name.count('-') != (len(params) - 1):
                if name not in invalid_tables:
                    invalid_tables.append(name)
                self.log('\t\t\tWarning: Incorrect amount of hyphens '
                         'in the table name')
            self.log()

        if len(invalid_tables) == 0:
            self.log('\tAll exclusion tables are valid')
            self.log()

    # calls the characterization parser to parse each characterization
    # in @measure
    def parse_characterizations(self) -> None:
        parser: CharacterizationParser \
            = CharacterizationParser(out=self.out, tabs=1)
        self.log('\nParsing Characterizations:')
        for characterization in self.measure.characterizations:
            print(f'\tparsing {characterization.name}')
            parser.parse(characterization)

    # prints a representation of every non-shared value table in @measure
    def log_value_tables(self) -> None:
        self.log('\n\nStandard Non-Shared Value Tables:')
        for table in self.measure.value_tables:
            self.log(f'\tTable Name: {table.name}\n'
                     f'\t\tAPI Name: {table.api_name}\n'
                     f'\t\tParameters: {table.determinants}')
            self.log('\t\tColumns:')
            for column in table.columns:
                self.log(f'\t\t\tColumn Name: {column.name}\n'
                         f'\t\t\t\tAPI Name: {column.api_name}\n'
                         f'\t\t\t\tUnit: {column.unit}\n')

    # prints out every calculation in @measure' name and API name
    def log_calculations(self) -> None:
        self.log('\nAll Calculations:')
        for calculation in self.measure.calculations:
            self.log(f'\tCalculation Name: {calculation.name}\n'
                     f'\t\tAPI Name: {calculation.api_name}\n'
                     f'\t\tUnit: {calculation.unit}\n'
                     f'\t\tParameters: {calculation.determinants}\n')

    # prints out every permutation in @measure's reporting name,
    # verbose name, and mapped field
    def log_permutations(self) -> None:
        self.log('\n\nAll Permutations:')
        for permutation in self.measure.permutations:
            try:
                perm_data = ALL_PERMUTATIONS[permutation.reporting_name]
            except:
                raise MeasureFormatError()

            try:
                verbose_name = perm_data['verbose']
                self.log(f'\t{permutation.reporting_name}:\n'
                         f'\t\tVerbose Name: {verbose_name}\n'
                         f'\t\tMapped Field: {permutation.mapped_name}\n')
            except:
                continue


    def __get_ordered_params(self) -> list[str]:
        criteria: list[str] = ['REQ']
        if self.measure.is_DEER():
            criteria.append('DEER')

        if self.measure.is_GSIA_nondef():
            criteria.append('GSIA')

        if (self.measure.contains_MAT_label('AR')
                or self.measure.contains_MAT_label('AOE')):
            criteria.append('MAT')

        if self.measure.is_WEN():
            criteria.append('WEN')

        if self.measure.requires_ntg_version():
            criteria.append('NTG')

        if self.measure.is_interactive():
            criteria.append('INTER')

        params: list[str] = db.get_param_names(criteria)
        if (self.measure.is_interactive()
                and not self.measure.contains_param('LightingType')):
            params.remove('LightingType')
        return params


    def __get_ordered_value_tables(self) -> list[str]:
        criteria: list[str] = ['REQ']

        if self.measure.is_DEER():
            criteria.append('DEER')

        if (self.measure.contains_MAT_label('AR')
                or self.measure.contains_MAT_label('AOE')):
            criteria.append('MAT')

        if self.measure.contains_value_table('emergingTech'):
            criteria.append('ET')

        if self.measure.requires_upstream_flag():
            criteria.append('DEEM')

        if self.measure.is_fuel_sub():
            criteria.append('FUEL')

        if self.measure.is_interactive():
            criteria.append('INTER')

        tables: list[str] = db.get_value_table_names(criteria)
        if (self.measure.is_interactive()
                and not self.measure.contains_value_table(
                    'IEApplicability')):
            tables.remove('IEApplicability')
        return tables


    def __get_ordered_shared_tables(self) -> list[str]:
        criteria: list[str] = ['REQ']

        if self.measure.is_DEER():
            criteria.append('DEER')

        if self.measure.is_GSIA_default():
            criteria.append('GSIA-DEF')

        if self.measure.is_GSIA_nondef():
            criteria.append('GSIA')

        if (self.measure.contains_MAT_label('AR')
                or self.measure.contains_MAT_label('AOE')):
            criteria.append('MAT')

        if self.measure.is_WEN():
            criteria.append('WEN')

        if self.measure.is_res_default():
            criteria.append('RES-DEF')
        else:
            criteria.append('RES')

        if self.measure.is_nonres_default():
            criteria.append('RES-NDEF')
        elif 'RES' not in criteria:
            criteria.append('RES')

        if self.measure.is_interactive():
            criteria.append('INTER')

        tables: list[str] = db.get_shared_table_names(criteria)
        if self.measure.is_interactive():
            commercial: str = 'commercialInteractiveEffects'
            if not self.measure.contains_shared_table(commercial):
                tables.remove(commercial)
            residential: str = 'residentialInteractiveEffects'
            if not self.measure.contains_shared_table(residential):
                tables.remove(residential)
        return tables

    # method to print to the parser's out stream
    def log(self, *values: object) -> None:
        print(*values, file=self.out)

    def close(self) -> bool:
        try:
            self.out.close()
        except OSError:
            print("error occurred while closing the output file")
            return False
        return True