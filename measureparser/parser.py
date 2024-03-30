import os
from io import TextIOWrapper


from .dbservice import (
    BaseDatabase
)
from .htmlparser import CharacterizationParser
from .measure import (
    Measure,
    Permutation
)
from .parserdata import (
    ParserData,
    MissingValueTableColumnData,
    InvalidValueTableColumnUnitData,
    StdValueTableNameData,
    InvalidPermutationData
)
from .logger import MeasureDataLogger
from ._exceptions import (
    ParserError,
    MeasureContentError
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

    def __init__(self, database: BaseDatabase):
        if not (BaseDatabase in database.__mro__):
            raise ParserError('Parser database must extend BaseDatabase')

        self.db: BaseDatabase = database
        self.data: ParserData | None = None
        self.measure: Measure | None = None
        self.ordered_params: list[str] = []
        self.ordered_val_tables: list[str] = []
        self.ordered_sha_tables: list[str] = []

    def clear_measure(self):
        self.measure = None
        self.ordered_params = []
        self.ordered_val_tables = []
        self.ordered_sha_tables = []
        self.data = None

    def set_measure(self, measure: Measure):
        self.measure = measure
        self.ordered_params = self.db.get_param_api_names(measure=measure)
        self.ordered_val_tables = self.db.get_table_api_names(measure=measure,
                                                              nonshared=True)
        self.ordered_sha_tables = self.db.get_table_api_names(measure=measure,
                                                              shared=True)
        self.data = ParserData()

    # specifies the control flow for the generic parsing of @measure
    def parse(self, measure: Measure) -> ParserData:
        self.set_measure(measure)

        print(f'starting to parse measure {measure.id}\n')
        try:
            print('validating parameters\n')
            self.validate_parameters()

            print('validating exclusion tables\n')
            self.validate_exclusion_tables()

            print('validating value tables\n')
            self.validate_tables()

            print('validating permutations\n')
            self.validate_permutations()

            print('parsing characterizations\n')
            self.parse_characterizations()
        except ParserError as err:
            raise err
        except Exception as err:
            raise ParserError('Unexpected error occurred while parsing') \
                from err
        finally:
            self.clear_measure()

        print(f'finished parsing measure {measure.id}')


    def validate_parameters(self, measure: Measure) -> None:
        self.data.parameter.nonshared = list(
            map(lambda param: param.name, measure.parameters))

        self.data.parameter.unexpected = list(
            map(lambda param: param.version.version_string,
                measure.remove_unknown_params(self.ordered_params)))
        self.data.parameter.missing = self.validate_param_existence()
        self.data.parameter.unordered = self.validate_param_order()


    def validate_tables(self, measure: Measure) -> None:
        shared_data = self.data.value_table.shared
        shared_data.unexpected = list(
            map(lambda table: table.version.version_string,
                measure.remove_unknown_shared_tables(
                    self.ordered_sha_tables)))
        shared_data.missing = self.validate_shared_table_existence()
        shared_data.unordered = self.validate_shared_table_order()

        nonshared_data = self.data.value_table.nonshared
        nonshared_data.unexpected = list(
            map(lambda table: table.name,
                measure.remove_unknown_value_tables(
                    self.ordered_val_tables)))
        nonshared_data.missing = self.validate_value_table_existence()
        nonshared_data.unordered = self.validate_value_table_order()
        self.validate_standard_table_names()
        self.validate_table_columns()


    # validates all non-shared value table columns
    #
    # Returns:
    #   bool    : true if all columns are valid, false otherwise 
    def validate_table_columns(self) -> None:
        column_data = self.data.value_table.nonshared.column
        column_dict = self.db.get_table_columns()

        for table in self.measure.value_tables:
            table_columns: list[dict[str, str]] | None \
                = column_dict.get(table.api_name)
            if table_columns == None:
                continue

            for column_info in table_columns:
                if column_info == None:
                    continue

                name: str = column_info.get('name')
                api_name: str | None = column_info.get('api_name')
                if api_name == None:
                    continue

                if not table.contains_column(api_name):
                    column_data.missing.append(
                        MissingValueTableColumnData(
                            table.name,
                            name or api_name))
                    continue

                column = table.get_column(api_name)
                unit: str | None = column_info.get('unit')
                if unit == None:
                    continue

                if not unit == column.unit:
                    column_data.invalid_unit.append(
                        InvalidValueTableColumnUnitData(
                            table.name,
                            name or api_name,
                            column.unit,
                            unit))
                    continue


    # validates that all nonshared value tables have the correct standard name
    def validate_standard_table_names(self) -> None:
        name_map = self.db.get_standard_table_names(self.measure)
        for table in self.measure.value_tables:
            std_name = name_map.get(table.api_name)
            if std_name == None:
                continue
            if table.name != std_name:
                self.data.value_table.nonshared.invalid_name.append(
                    StdValueTableNameData(table.name, std_name))


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


    def validate_param_order(self) -> list[str]:
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


    def validate_value_table_order(self) -> list[str]:
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


    def validate_shared_table_order(self) -> list[str]:
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
                        InvalidPermutationData(
                            permutation.reporting_name,
                            mapped_name,
                            valid_names))
            except MeasureContentError as err:
                self.data.permutation.unexpected.append(err.name)


    # returns the valid name for @permutation
    #
    # Parameters:
    #   permutation (Permutation): the permutation being validated
    #
    # Returns:
    #   str : the valid name of @permutation
    def get_valid_perm_names(self, permutation: Permutation) -> list[str]:
        reporting_name: str = permutation.reporting_name
        data: dict[str, str] = self.db.get_permutation_data(reporting_name)
        if data['verbose'] == '':
            raise MeasureContentError(
                f'The permutation name [{reporting_name}] is unknown')

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
        for char_name in self.db.get_all_characterization_names():
            if self.measure.get_characterization(char_name) == None:
                self.data.characterization[char_name].missing = True
        for characterization in self.measure.characterizations:
            print(f'\tparsing {characterization.name}')
            parser.parse(characterization)


    def log_output(self,
                   dir_path: str | None = None,
                   file_name: str | None = None):
        '''Specifies the control flow for logging parsed measure data.
        
        Params:
            dir_path `str | None` : path of output file or `None` for standard output
        '''

        out: str | None = None
        if dir_path != None:
            if file_name == None:
                file_name = 'parser-output'
            out = os.path.join(dir_path, f'{file_name}.txt')
        elif file_name != None:
            raise ParserError(
                'No output directory path provided with file name')
        else:
            self.log('\n')

        if self.data == None:
            raise ParserError('Parser data is required to log output')

        with MeasureDataLogger(out) as _logger:
            _logger.log_data()

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


    def log_value_table_data(self) -> None:
        '''Logs parsed invalid shared and non-shared value table data to
        the output file.
        
        General data:
            - Unexpected shared/non-shared value tables
            - Missing shared/non-shared value tables
            - Value Table order

        Non-Shared Value Table specific data:
            - Name
            - Columns
                - Name
                - Unit
        '''

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

        if nonshared_data.column.is_empty():
            self.log('\t\tAll value table columns are valid')
        self.log()

        self.log('\tValue Table Order: ')

        # for table in shared_data.unordered:
        #     self.log(f'\t\t{table} is out of order')
        if shared_data.unordered == []:
            self.log('\t\tAll shared value tables are in the '
                     'correct order')
        else:
            self.log('\t\tShared value tables may be out of order, '
                     'please review the QA/QC guidelines')

        # for table in nonshared_data.unordered:
        #     self.log(f'\t\t{table} is out of order')
        if nonshared_data.unordered == []:
            self.log('\t\tAll non-shared value tables are in the '
                     'correct order')
        else:
             self.log('\t\tNon-shared value tables may be out of '
                      'order, please review the QA/QC guidelines')
        self.log('\n')


    def log_value_tables(self) -> None:
        '''Logs all measure non-shared value tables to the output file.
        
        Non-Shared Value Table data:
            - Name
            - API name
            - Parameters
            - Columns
                - Name
                - API name
                - Unit
        '''

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


    def log_calculations(self) -> None:
        '''Logs all measure calculations to the output file.
        
        Calculation data:
            - Name
            - API name
            - Unit
            - Parameters
        '''

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
        '''Logs parsed invalid permutation data to the output file.

        General data:
            - Unexpected permutation

        Permutation specific data:
            - Incorrect mapped field
        '''

        self.log('Validating permutations:')
        for err in self.data.permutation.invalid:
            self.log(f'\tInvalid Permutation ({err.reporting_name}) - '
                     f'{err.mapped_name} should be ' +
                     (f'{err.valid_names[0]}' if len(err.valid_names) == 1
                        else f'one of {err.valid_names}'))

        for perm_name in self.data.permutation.unexpected:
            self.log(f'\tUnexpected Permutation - {perm_name}')

        if self.data.permutation.is_empty():
            self.log('\tAll permutations are valid')
        self.log('\n')


    def log_permutations(self) -> None:
        '''Logs all measure permutations to the output file.
        
        Permutation data:
            - Reporting name
            - Verbose name
            - Mapped field
        '''

        self.log('All Permutations:')
        for permutation in self.measure.permutations:
            perm_data = self.db.get_permutation_data(
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
        '''Logs parsed invalid charaterization data to the output file.
        
        General data:
            - Missing characterizations
        
        Characterization specific data:
            - Header order (h3 -> h4 -> h5)
            - Reference tag spacing and required content
            - Sentence and punctuation spacing
        '''

        self.log('Parsing characterizations:')
        for name, data in self.data.characterization.items():
            if data.is_empty():
                continue

            if data.missing:
                self.log(f'\tMissing Characterization: {name}')
                continue

            self.log(f'\t{name}:')

            if data.initial_header != 'h3':
                self.log('\t\tInvalid initial header, '
                         f'{data.initial_header} should be h3')

            for err in data.invalid_headers:
                self.log('\t\tInvalid header order, '
                         f'{err.tag} should not directly follow h{err.prev_level}')

            for title, references in data.references.reference_map.items():
                for ref in references:
                    if ref.title.missing:
                        self.log('\t\tA reference is missing a static title')

                    if ref.spacing.leading != -1:
                        spaces = ref.spacing.leading
                        self.log('\t\tWhitespace detected before reference '
                                 f'[{title}] - {spaces} space(s)')

                    if ref.spacing.trailing != -1:
                        spaces = ref.spacing.trailing
                        self.log('\t\tWhitespace detected after reference '
                                 f'[{title}] - {spaces} space(s)')

                    if ref.title.spacing.leading != -1:
                        spaces = ref.title.spacing.leading
                        self.log('\t\tWhitespace detected before a '
                                 f'reference title [{title}] - '
                                 f'{spaces} space(s)')

                    if ref.title.spacing.trailing != -1:
                        spaces = ref.title.spacing.trailing
                        self.log('\t\tWhitespace detected after a '
                                 f'reference title [{title}] - '
                                 f'{spaces} space(s)')

            for sentence_data in data.sentences:
                if sentence_data.leading != -1:
                    spaces = sentence_data.leading
                    tol = 0 if sentence_data.initial or spaces == 0 else 1
                    self.log('\t\tExtra whitespace detected before a sentence - '
                             f'{spaces - tol} space(s) before '
                             f'sentence [{sentence_data.sentence}]')

                if sentence_data.trailing != -1:
                    spaces = sentence_data.trailing
                    self.log('\t\tExtra whitespace detected before punctuation - '
                             f'{spaces} space(s) in sentence '
                             f'[{sentence_data.sentence}]')
            self.log()

        if all(cd.is_empty() for cd in self.data.characterization.values()):
            self.log('\tAll characterizations are valid')


    def log(self, *values: object) -> None:
        '''Logs data to the defined output stream.
        
        Params:
            values (*object) : content being logged
        '''
        print(*values, file=self.out)


    def clear(self) -> None:
        if self.out != None:
            out_filepath = os.path.abspath(self.out.name)
            if os.path.exists(out_filepath):
                os.remove(out_filepath)
