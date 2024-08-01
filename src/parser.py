import os

from src import dbservice as db
from src.logger import MeasureDataLogger
from src.etrm.models import (
    Measure,
    Permutation,
    SharedDeterminantRef,
    ValueTable,
    SharedLookupRef,
    Characterization
)
from src.htmlparser import CharacterizationParser
from src.parserdata import (
    parser_data_factory,
    MissingValueTableColumnData,
    InvalidValueTableColumnUnitData,
    StdValueTableNameData,
    InvalidPermutationData
)
from src.exceptions import (
    ParserError,
    MeasureContentError
)


class MeasureParser:
    """Data validation parser for eTRM measures."""

    def __init__(self, measure: Measure):
        self.measure = measure
        self.data = parser_data_factory(measure.source)
        self.ordered_params = db.get_param_api_names(measure=measure)
        self.ordered_val_tables = db.get_table_api_names(measure=measure,
                                                         nonshared=True)
        self.ordered_sha_tables = db.get_table_api_names(measure=measure,
                                                         shared=True)

        names = db.get_all_characterization_names(self.measure.source)
        for char_name in names:
            if self.measure.get_characterization(char_name) == None:
                self.data.characterization[char_name].missing = True
        self.characterization_parser = CharacterizationParser(
            self.data.characterization,
            characterizations=self.measure.characterizations
        )

    def get_known_parameters(self) -> list[SharedDeterminantRef]:
        """Returns a collection of all shared determinant refs that
        appear in both the measure and ordered parameters.
        """

        return self.measure.get_shared_parameters(self.ordered_params)

    def get_known_value_tables(self) -> list[ValueTable]:
        """Returns a collection of all non-shared value tables that
        appear in both the measure and ordered non-shared value tables.
        """

        return self.measure.get_value_tables(self.ordered_val_tables)

    def get_known_shared_tables(self) -> list[SharedLookupRef]:
        """Returns a collection of all shared lookup refs that appear
        in both the measure and ordered shared value tables.
        """

        return self.measure.get_shared_lookups(self.ordered_sha_tables)

    def validate_parameters(self) -> None:
        self.data.parameter.nonshared = list(
            map(
                lambda param: param,
                self.measure.determinants
            )
        )

        known_params = self.get_known_parameters()
        self.data.parameter.unexpected = list(
            filter(
                lambda param: param not in known_params,
                self.measure.determinants
            )
        )
        self.data.parameter.missing = self.get_missing_parameter_names()
        self.data.parameter.unordered = self.get_unordered_parameter_names()

    def validate_tables(self) -> None:
        shared_data = self.data.value_table.shared
        known_tables = self.get_known_shared_tables()
        shared_data.unexpected = list(
            filter(
                lambda table: table not in known_tables,
                self.measure.shared_lookup_refs
            )
        )
        shared_data.missing = self.get_missing_shared_table_names()
        shared_data.unordered = self.get_unordered_shared_table_names()

        nonshared_data = self.data.value_table.nonshared
        known_tables = self.get_known_value_tables()
        nonshared_data.unexpected = list(
            filter(
                lambda table: table not in known_tables,
                self.measure.value_tables
            )
        )
        nonshared_data.missing = self.get_missing_value_table_names()
        nonshared_data.unordered = self.get_unordered_value_table_names()
        self.validate_standard_table_names()
        self.validate_table_columns()

    def validate_table_columns(self) -> None:
        column_data = self.data.value_table.nonshared.column
        column_dict = db.get_table_columns()

        for table in self.measure.value_tables:
            table_columns = column_dict.get(table.api_name)
            if table_columns == None:
                continue

            for column_info in table_columns:
                if column_info == None:
                    continue

                name = column_info.get('name')
                api_name = column_info.get('api_name')
                if api_name == None:
                    continue

                if not table.contains_column(api_name):
                    column_data.missing.append(
                        MissingValueTableColumnData(
                            table.name,
                            name or api_name))
                    continue

                column = table.get_column(api_name)
                unit = column_info.get('unit')
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

    def validate_standard_table_names(self) -> None:
        """Validates that all non-shared value tables have the correct
        name.
        """

        name_map = db.get_standard_table_names(self.measure)
        for table in self.measure.value_tables:
            std_name = name_map.get(table.api_name)
            if std_name == None:
                continue
            if table.name != std_name:
                self.data.value_table.nonshared.invalid_name.append(
                    StdValueTableNameData(table.name, std_name))

    def get_missing_shared_table_names(self) -> list[str]:
        """Returns a collection of the names of all shared lookup refs
        that were expected but are missing.
        """

        missing_tables: list[str] = []
        for table in self.ordered_sha_tables:
            if not self.measure.contains_shared_table(table):
                missing_tables.append(table)
        return missing_tables

    def get_missing_value_table_names(self) -> list[str]:
        """Returns a collection of the names of all value tables that
        were expected but are missing.
        """

        missing_tables: list[str] = []
        for table in self.ordered_val_tables:
            if not self.measure.contains_value_table(table):
                missing_tables.append(table)
        return missing_tables

    def get_missing_parameter_names(self) -> list[str]:
        """Returns a collection of the names of all shared determinant
        refs that were expected but are missing.
        """

        missing_params: list[str] = []
        for param in self.ordered_params:
            if not self.measure.contains_parameter(param):
                missing_params.append(param)
        return missing_params

    def get_unordered_parameter_names(self) -> list[str]:
        """Returns a collection of the names of all shared determinant
        refs that are out of order.
        """

        ordered_params = list(
            filter(
                lambda name: self.measure.contains_parameter(name),
                self.ordered_params
            )
        )

        parameters = self.get_known_parameters()
        parameters.sort(key=lambda ref: ref.order)
        return list(
            set(ordered_params).symmetric_difference(
                map(
                    lambda parameter: parameter.name,
                    parameters
                )
            )
        )

    def get_unordered_value_table_names(self) -> list[str]:
        """Returns a collection of the names of all non-shared value
        tables that are out of order.
        """

        ordered_table_names = list(
            filter(
                lambda name: self.measure.contains_value_table(name),
                self.ordered_val_tables
            )
        )

        value_tables = self.get_known_value_tables()
        value_tables.sort(key=lambda table: table.order)
        return list(
            set(ordered_table_names).symmetric_difference(
                map(
                    lambda table: table.name,
                    value_tables
                )
            )
        )

    def get_unordered_shared_table_names(self) -> list[str]:
        ordered_table_names = list(
            filter(
                lambda name: self.measure.contains_shared_table(name),
                self.ordered_sha_tables
            )
        )

        lookup_refs = self.get_known_shared_tables()
        lookup_refs.sort(key=lambda ref: ref.order)
        return list(
            set(ordered_table_names).symmetric_difference(
                map(
                    lambda table: table.name,
                    lookup_refs
                )
            )
        )

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
        data: dict[str, str] = db.get_permutation_data(reporting_name)
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
                if ('AR' in get_param('MeasAppType').active_labels):
                    valid_name = 'measOffer__descBase2'
            
            case 'Upstream_Flag':
                if ('UpDeemed' in get_param('DelivType').active_labels):
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
                mat_labels: list[str] = get_param('MeasAppType').active_labels
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

    def parse_characterization(self,
                               characterization: Characterization
                              ) -> None:
        self.characterization_parser.parse(characterization)

    # calls the characterization parser to parse each characterization
    # in @measure
    def parse_characterizations(self) -> None:
        for characterization in self.measure.characterizations:
            self.characterization_parser.parse(characterization)

    def log_output(self, out_file: str, override: bool=False) -> None:
        """Specifies the control flow for logging parsed measure data."""

        out_dir, file_name = os.path.split(out_file)
        if not os.path.exists(out_dir):
            raise ParserError(
                f'Invalid File Path: directory {out_dir} does not exist'
            )
        elif os.path.exists(out_file) and not override:
            raise ParserError(
                f'Invalid File Path: a file named {file_name} already'
                f' exists at {out_dir}'
            )

        if self.data == None:
            raise ParserError('Parser data is required to log output')

        try:
            with MeasureDataLogger(self.measure, out_file) as _logger:
                _logger.log_data(self.data)
        except:
            if os.path.exists(out_file):
                os.remove(out_file)
            raise
