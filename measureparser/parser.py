from io import TextIOWrapper

import measureparser._parserdata as pd
import measureparser._dbservice as db
from ._htmlparser import CharacterizationParser
from .measure import (
    Measure,
    Permutation
)
from .exceptions import (
    RequiredParameterError,
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

    def __init__(self, filepath: str):
        self.measure = Measure(filepath)
        self.data = pd.ParserData()
        self.out: TextIOWrapper | None = None

        try:
            self.ordered_params: list[str] \
                = db.get_param_api_names(measure=self.measure)

            self.ordered_val_tables: list[str] \
                = db.get_table_api_names(measure=self.measure, nonshared=True)

            self.ordered_sha_tables: list[str] \
                = db.get_table_api_names(measure=self.measure, shared=True)
        except RequiredParameterError as err:
            print('ERROR - the measure is missing required information\n', 
                  err)
            return
        except Exception as err:
            print(f'ERROR - something went wrong:\n{err}')
            return


    # specifies the control flow for the generic parsing of @measure
    def parse(self) -> None:
        if self.measure == None:
            print('ERROR - measure parser requires a measure to parse')
            return

        print(f'starting to parse measure {self.measure.id}\n')

        print('validating parameters')
        self.validate_parameters()
        print('finished validating parameters\n')

        print('validating exclusion tables')
        self.validate_exclusion_tables()
        print('finished validating exclusion tables\n')

        print('validating tables')
        self.validate_tables()
        print('finished validating tables\n')

        print('validating permutations')
        self.validate_permutations()
        print('finished validating permutations\n')

        print('parsing characterizations')
        self.parse_characterizations()
        print('finished parsing characterizations\n')

        print(f'finished parsing measure {self.measure.id}')


    def validate_parameters(self) -> None:
        self.data.parameter.nonshared = list(
            map(lambda param: param.name, self.measure.parameters))

        self.data.parameter.unexpected = list(
            map(lambda param: param.version.version_string,
                self.measure.remove_unknown_params(self.ordered_params)))
        self.data.parameter.missing = self.validate_param_existence()
        self.data.parameter.unordered = self.smart_validate_param_order()


    def validate_tables(self) -> None:
        shared_data = self.data.value_table.shared
        shared_data.unexpected = list(
            map(lambda table: table.version.version_string,
                self.measure.remove_unknown_shared_tables(
                    self.ordered_sha_tables)))
        shared_data.missing = self.validate_shared_table_existence()
        shared_data.unordered = self.smart_validate_shared_table_order()

        nonshared_data = self.data.value_table.nonshared
        nonshared_data.unexpected = list(
            map(lambda table: table.name,
                self.measure.remove_unknown_value_tables(
                    self.ordered_val_tables)))
        nonshared_data.missing = self.validate_value_table_existence()
        nonshared_data.unordered = self.smart_validate_value_table_order()
        self.validate_standard_table_names()
        self.validate_table_columns()


    # validates all non-shared value table columns
    #
    # Returns:
    #   bool    : true if all columns are valid, false otherwise 
    def validate_table_columns(self) -> None:
        column_data = self.data.value_table.nonshared.column
        column_dict = db.get_table_columns(measure=self.measure)

        for table in self.measure.value_tables:
            for column_info in column_dict[table.api_name]:
                name: str = getattr(column_info, 'name', None)
                api_name: str = getattr(column_info, 'api_name', None)
                if api_name == None:
                    continue

                if not table.contains_column(api_name):
                    column_data.missing.append(
                        pd.MissingValueTableColumnData(
                            table.name,
                            name or api_name))
                    continue

                column = table.get_column(api_name)
                unit: str = getattr(column_info, 'unit', None)
                if not unit == column.unit:
                    column_data.invalid_unit.append(
                        pd.InvalidValueTableColumnUnitData(
                            table.name,
                            name or api_name,
                            column.unit,
                            unit))
                    continue


    # validates that all nonshared value tables have the correct standard name
    def validate_standard_table_names(self) -> None:
        name_map = db.get_standard_table_names(self.measure)
        for table in self.measure.value_tables:
            std_name = name_map.get(table.api_name)
            if std_name == None:
                continue
            if table.name != std_name:
                self.data.value_table.nonshared.invalid_name.append(
                    pd.StdValueTableNameData(table.name, std_name))


    # validates that all shared value tables names in @ordered_sha_tables
    # correlate to a shared value table in @measure
    #
    # Returns:
    #   list[str]   : the list of missing shared value tables,
    #                 returns an empty list if all tables are valid 
    def validate_shared_table_existence(self) -> list[str]:
        missing_tables: list[str] = []
        for table in self.ordered_sha_tables:
            if not self.measure.contains_shared_table(table):
                missing_tables.append(table)
        return missing_tables


    # validates that all non-shared value tables names in
    # @ordered_val_tables correlate to a non-shared value table in
    # @measure
    #
    # Returns:
    #   list[str]   : the list of missing non-shared value tables,
    #                 returns an empty list if all tables are valid 
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


    # validates that all parameters in @measure are in the same order as
    # the parameters represented by @ordered_params
    def validate_param_order(self) -> bool:
        param_names: list[str] = list(
            filter(lambda name: self.measure.contains_param(name),
                   self.ordered_params))
        for param in self.measure.shared_parameters:
            index: int = param_names.index(param.version.version_string)
            if param.order != (index + 1):
                self.log('\t\tShared parameters may be out of order, '
                         'please review the QA/QC guidelines')
                return False
        return True


    def smart_validate_param_order(self) -> list[str]:
        unordered_params: list[str] = []
        ordered_params: list[str] = list(
            filter(lambda name: self.measure.contains_param(name),
                   self.ordered_params))
        param_names: list[str] = list(
            map(lambda param: param.version.version_string,
                self.measure.shared_parameters))
        index: int = 0
        while index < len(param_names):
            param: str = param_names[index]
            ordered_param: str = ordered_params[index]
            if (param != ordered_param
                    and ordered_param not in unordered_params):
                unordered_params.append(ordered_param)
                param_names.remove(ordered_param)
                ordered_params.remove(ordered_param)
                index = 0
                continue
            index = index + 1

        return unordered_params


    # validates that all non-shared value tables in @measure are in the
    # same order as the non-shared value tables represented by
    # @ordered_val_tables
    def validate_value_table_order(self) -> bool:
        table_names: list[str] = list(
            filter(lambda name: self.measure.contains_value_table(name),
                   self.ordered_val_tables))
        for table in self.measure.value_tables:
            index: int = table_names.index(table.api_name)
            if table.order != (index + 1):
                self.log(f'\t\tNon-shared value tables may be out of '
                         'order, please review the QA/QC guidelines')
                return False
        return True


    def smart_validate_value_table_order(self) -> list[str]:
        unordered_tables: list[str] = []
        ordered_tables: list[str] = list(
            filter(lambda name: self.measure.contains_value_table(name),
                   self.ordered_val_tables))
        table_names: list[str] = list(
            map(lambda table: table.api_name, self.measure.value_tables))
        index: int = 0
        while index < len(table_names):
            table: str = table_names[index]
            ordered_table: str = ordered_tables[index]
            if (table != ordered_table
                    and ordered_table not in unordered_tables):
                unordered_tables.append(ordered_table)
                table_names.remove(ordered_table)
                ordered_tables.remove(ordered_table)
                index = 0
                continue
            index = index + 1

        return unordered_tables


    # validates that all shared value tables in @measure are in the same
    # order as the non-shared value tables represented by
    # @ordered_val_tables
    def validate_shared_table_order(self) -> bool:
        table_names: list[str] = list(
            filter(lambda name: self.measure.contains_shared_table(name),
                   self.ordered_sha_tables))
        for table in self.measure.shared_tables:
            index: int = table_names.index(table.version.version_string)
            if table.order != (index + 1):
                self.log('\t\tShared value tables may be out of order, '
                         'please review the QA/QC guidelines')
                return False
        return True


    def smart_validate_shared_table_order(self) -> list[str]:
        unordered_tables: list[str] = []
        ordered_tables: list[str] = list(
            filter(lambda name: self.measure.contains_shared_table(name),
                   self.ordered_sha_tables))
        table_names: list[str] = list(
            map(lambda table: table.version.version_string,
                self.measure.shared_tables))
        index: int = 0
        while index < len(table_names):
            table: str = table_names[index]
            ordered_table: str = ordered_tables[index]
            if (table != ordered_table
                    and ordered_table not in unordered_tables):
                unordered_tables.append(ordered_table)
                table_names.remove(ordered_table)
                ordered_tables.remove(ordered_table)
                index = 0
                continue
            index = index + 1

        return unordered_tables


    # validates that all permutations have a valid mapped name
    def validate_permutations(self) -> None:
        for permutation in self.measure.permutations:
            try:
                valid_names: list[str] \
                    = self.get_valid_perm_names(permutation)
                mapped_name: str = permutation.mapped_name
                if mapped_name not in valid_names:
                    self.data.permutation.invalid.append(
                        pd.InvalidPermutationData(
                            permutation.reporting_name,
                            mapped_name,
                            valid_names))
            except UnknownPermutationError as err:
                self.data.permutation.unexpected.append(err.name)


    # returns the valid name for @permutation
    #
    # Paramters:
    #   permutation (Permutation): the permutation being validated
    #
    # Returns:
    #   str : the valid name of @permutation
    def get_valid_perm_names(self, permutation: Permutation) -> list[str]:
        reporting_name: str = permutation.reporting_name
        data: dict[str, str] = db.get_permutation_data(reporting_name)
        if data['verbose'] == '':
            raise UnknownPermutationError(name=reporting_name)

        valid_name: str = data['valid']
        if valid_name == None:
            valid_name = permutation.mapped_name

        get_param: function = self.measure.get_shared_parameter
        get_value_table: function = self.measure.get_value_table
        match reporting_name:
            case 'BaseCase2nd':
                if ('AR' in get_param('MeasAppType').labels):
                    valid_name = 'measOffer__descBase2'
            
            case 'Upstream_Flag':
                if ('UpDeemed' in get_param('DelivType').labels):
                    valid_name = 'upstreamFlag__upstreamFlag'

            case 'WaterUse':
                if (get_param('waterMeasureType') != None):
                    valid_name = 'p.waterMeasureType__label'

            case 'ETP_Flag':
                if (get_value_table('emergingTech') != None):
                    valid_name = 'emergingTech__projectNumber'

            case 'ETP_YearFirstIntroducedToPrograms':
                if (get_value_table('emergingTech') != None):
                    valid_name = 'emergingTech__introYear'

            case 'RUL_Yrs':
                mat_labels: list[str] = get_param('MeasAppType').labels
                if ('AR' in mat_labels):
                    if (len(mat_labels) == 1):
                        valid_name = 'hostEulAndRul__RUL_Yrs'
                    elif (len(mat_labels) > 1):
                        valid_name = 'HostEULID__RUL_Yrs'
                else:
                    valid_name = 'Null__ZeroYrs'

            case 'RestrictedPerm':
                # special case, any of these can be valid names
                return ['Null__Zero',
                        'Null__One',
                        'restrictPerm__value',
                        'restrictPermFlag']

        return [valid_name]


    # validates that all exclusion tables follow the following
    #   1. There are no whitespaces in the table name
    #   2. The amount of hyphens in the table name must be one less than
    #            the total amount of parameters
    #
    # prints out all exclusion tables
    def validate_exclusion_tables(self) -> None:
        exclusion_data = self.data.exclusion_table
        for table in self.measure.exclusion_tables:
            name: str = table.name
            if ' ' in name:
                exclusion_data.whitespace.append(name)

            params: list[str] = table.determinants
            if name.count('-') != (len(params) - 1):
                exclusion_data.hyphen.append(name)


    # calls the characterization parser to parse each characterization
    # in @measure
    def parse_characterizations(self) -> None:
        parser = CharacterizationParser(self.data.characterization)
        for char_name in db.get_all_characterization_names():
            if self.measure.get_characterization(char_name) == None:
                self.data.characterization.missing.append(char_name)
        for characterization in self.measure.characterizations:
            print(f'\tparsing {characterization.name}')
            parser.parse(characterization)


    # specifies the control flow for parser logging
    def log_output(self, dirpath: str | None = None) -> None:
        if dirpath != None:
            self.out = open(f'{dirpath}/output-{self.measure.id}.txt', 'w+')

        self.log_measure_details()
        self.log_parameter_data()
        self.log_exclusion_table_data()
        self.log_value_table_data()
        self.log_value_tables()
        self.log_calculations()
        self.log_permutation_data()
        self.log_permutations()
        self.log_characterization_data()

        if self.out != None:
            self.out.close()
            self.out = None


    # logs specific details about the measure
    def log_measure_details(self) -> None:
        self.log('Measure Details:'
                 f'\n\tMeasure Version ID: {self.measure.version_id}'
                 f'\n\tMeasure Name: {self.measure.name}'
                 f'\n\tPA Lead: {self.measure.pa_lead}'
                 f'\n\tStart Date: {self.measure.start_date}'
                 f'\n\tEnd Date: {self.measure.end_date}')
        self.log('\n')


    def log_parameter_data(self) -> None:
        param_data = self.data.parameter
        self.log('Validating Parameters:')
        self.log('\tMeasure Specific Parameters: ',
                 param_data.nonshared)
        self.log()
        self.log('\tUnexpected Shared Parameters: ',
                 param_data.unexpected)
        self.log('\tMissing Shared Parameters: ',
                 param_data.missing)
        self.log()
        self.log('\tParameter Order:')
        for param_name in param_data.unordered:
            self.log(f'\t\t{param_name} is out of order')
        if param_data.unordered == []:
            self.log('\t\tAll shared parameters are in the correct order')
        self.log('\n')


    def log_exclusion_table_data(self) -> None:
        self.log('Validating Exclusion Tables:')
        for table in self.measure.exclusion_tables:
            self.log(f'\tTable Name: {table.name}\n',
                     f'\t\tParameters: {table.determinants}\n')
        exclusion_data = self.data.exclusion_table
        for table_name in exclusion_data.whitespace:
            self.log('\t\t\tWarning: Whitespace(s) detected in '
                     f'{table_name}, please remove the whitespace(s)')
        for table_name in exclusion_data.hyphen:
            self.log('\t\t\tWarning: Incorrect amount of hyphens '
                     f'in {table_name}')
        if exclusion_data.isEmpty():
            self.log('\tAll exclusion tables are valid')
        self.log('\n')


    def log_value_table_data(self) -> None:
        self.log('Validating Value Tables:')
        shared_data = self.data.value_table.shared
        self.log('\tUnexpected Shared Tables: ',
                 shared_data.unexpected)
        self.log('\tMissing Shared Tables: ',
                 shared_data.missing)
        self.log()

        nonshared_data = self.data.value_table.nonshared
        self.log('\tUnexpected Non-Shared Tables: ',
                 nonshared_data.unexpected)
        self.log('\tMissing Non-Shared Tables: ',
                 nonshared_data.missing)
        self.log()

        self.log('\tValue Table Names:')
        for err in nonshared_data.invalid_name:
            self.log(f'\t\tTable {err.table_name} should be named '
                     f'{err.correct_name}')
        if nonshared_data.invalid_name == []:
            self.log('\t\tAll value table names are correct')
        self.log()

        self.log('\tValue Table Columns:')
        for err in nonshared_data.column.missing:
            self.log(f'\t\tTable {err.table_name} is missing '
                     f'column {err.column_name}')

        for err in nonshared_data.column.invalid_unit:
            self.log(f'\t\tTable {err.table_name} may have an '
                     f'incorrect unit in {err.column_name}, '
                     f'{err.mapped_unit} should be {err.correct_unit}')

        if nonshared_data.column.isEmpty():
            self.log('\t\tAll table columns are valid')
        self.log()

        self.log('\tValue Table Order: ')

        for table in shared_data.unordered:
            self.log(f'\t\t{table} is out of order')
        if shared_data.unordered == []:
            self.log('\t\tAll shared value tables are in the '
                     'correct order')

        for table in nonshared_data.unordered:
            self.log(f'\t\t{table} is out of order')
        if nonshared_data.unordered == []:
            self.log('\t\tAll non-shared value tables are in the '
                     'correct order')
        self.log('\n')


    # prints a representation of every non-shared value table in @measure
    def log_value_tables(self) -> None:
        self.log('Standard Non-Shared Value Tables:')
        for table in self.measure.value_tables:
            if self.measure.value_tables.index(table) != 0:
                self.log()
            self.log(f'\tTable Name: {table.name}\n'
                     f'\t\tAPI Name: {table.api_name}\n'
                     f'\t\tParameters: {table.determinants}')
            self.log('\t\tColumns:')
            for column in table.columns:
                self.log(f'\t\t\tColumn Name: {column.name}\n'
                         f'\t\t\t\tAPI Name: {column.api_name}\n'
                         f'\t\t\t\tUnit: {column.unit}')
        self.log('\n')


    # prints out every calculation in @measure' name and API name
    def log_calculations(self) -> None:
        self.log('All Calculations:')
        for calculation in self.measure.calculations:
            if self.measure.calculations.index(calculation) != 0:
                self.log()
            self.log(f'\tCalculation Name: {calculation.name}\n'
                     f'\t\tAPI Name: {calculation.api_name}\n'
                     f'\t\tUnit: {calculation.unit}\n'
                     f'\t\tParameters: {calculation.determinants}')
        self.log('\n')


    def log_permutation_data(self) -> None:
        self.log('Validating permutations:')
        for err in self.data.permutation.invalid:
            self.log(f'\tInvalid Permutation ({err.reporting_name}) - '
                     f'{err.mapped_name} should be ' +
                     (f'{err.valid_names[0]}' if len(err.valid_names) == 1
                        else f'one of {err.valid_names}'))

        for perm_name in self.data.permutation.unexpected:
            self.log(f'\tUnexpected Permutation - {perm_name}')

        if self.data.permutation.isEmpty():
            self.log('\tAll permutations are valid')
        self.log('\n')


    # prints out every permutation in @measure's reporting name,
    # verbose name, and mapped field
    def log_permutations(self) -> None:
        self.log('All Permutations:')
        for permutation in self.measure.permutations:
            perm_data = db.get_permutation_data(
                permutation.reporting_name)

            if self.measure.permutations.index(permutation) != 0:
                self.log()
            try:
                verbose_name = perm_data['verbose']
                self.log(f'\t{permutation.reporting_name}:\n'
                         f'\t\tVerbose Name: {verbose_name}\n'
                         f'\t\tMapped Field: {permutation.mapped_name}')
            except:
                continue
        self.log('\n')


    def log_characterization_data(self) -> None:
        self.log('Parsing characterizations:')
        for err in self.data.characterization.punc_space:
            self.log('\tExtra space(s) detected after punctuation '
                     f'in {err.name} - {err.spaces} space(s)')

        for err in self.data.characterization.refr_space:
            self.log('\tExtra space(s) detected before a reference '
                     f'in {err.name} - {err.spaces} space(s)')

        for err in self.data.characterization.capitalization:
            self.log(f'\tUncapitalized word detected in {err.name} - '
                     f'{err.word} should be {err.capitalized}')

        for err in self.data.characterization.inv_header:
            self.log(f'\tInvalid header in {err.name} - {err.tag}')

        for err in self.data.characterization.init_header:
            self.log(f'\tIncorrect initial header in {err.name} - '
                     f'expected h3, but detected {err.tag}')

        for err in self.data.characterization.inc_header:
            prev = err.prev_level
            self.log(f'\tIncorrect header in {err.name} - '
                     f'expected h{prev} or h{prev + 1}, '
                     f'but detected {err["tag"]}')

        if self.data.characterization.isEmpty():
            self.log('\tAll characterizations are valid')


    # method to print to the parser's out stream
    #
    # Parameters:
    #   *object : the object being printed
    def log(self, *values: object) -> None:
        print(*values, file=self.out)
