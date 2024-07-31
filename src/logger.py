import sys
from typing import Self

from src import dbservice as db
from src.etrm.models import Measure
from src.parserdata import (
    ParserData
)


class MeasureDataLogger:
    def __init__(self,
                 measure: Measure,
                 output_path: str | None = None):
        self.measure = measure
        if output_path != None:
            self.out = open(output_path, 'w+')
        else:
            self.out = sys.stdout

        self.data: ParserData | None = None

    def close(self):
        if self.out != None:
            self.out.close()

    def __exit__(self, *args):
        self.close()

    def __enter__(self) -> Self:
        return self

    def log(self, *values: object):
        print(*values, file=self.out)

    def log_measure_details(self) -> None:
        """Logs measure identification details."""

        self.log('Measure Details:'
                 f'\n\tMeasure Version ID: {self.measure.version_id}'
                 f'\n\tMeasure Name: {self.measure.name}'
                 f'\n\tPA Lead: {self.measure.pa_lead}'
                 f'\n\tStart Date: {self.measure.start_date}'
                 f'\n\tEnd Date: {self.measure.end_date}')
        self.log('\n')

    def log_parameter_data(self) -> None:
        """Logs all measure specific parameters and invalid measure parameter
        data.

        Invalid Parameter data:
            - Unexpected parameters
            - Missing parameters
        """

        param_data = self.data.parameter
        self.log('Parameters:')

        nonshared_names = list(
            map(
                lambda param: param.name,
                param_data.nonshared
            )
        )
        self.log(f'\tMeasure Specific Parameters: {nonshared_names}')
        self.log()

        unexpected_names = list(
            map(
                lambda param: param.name,
                param_data.unexpected
            )
        )
        self.log(f'\tUnexpected Shared Parameters: {unexpected_names}')
        self.log(f'\tMissing Shared Parameters: {param_data.missing}')
        self.log()
        self.log('\tParameter Order:')
        # for param_name in param_data.unordered:
        #     self.log(f'\t\t{param_name} is out of order')
        if param_data.unordered == []:
            self.log('\t\tAll shared parameters are in the correct order')
        else:
            self.log('\t\tShared parameters may be out of order, '
                     'please review the QA/QC guidelines')
        self.log('\n')

    def log_exclusion_table_data(self) -> None:
        """Logs all measure exclusion tables and invalid exclusion table data.

        Exclusion Table data:
            - Name
            - Parameters

        Invalid Exclusion Table data:
            - Whitespace in name
            - Incorrect amount of hyphens in name
        """

        self.log('Exclusion Tables:')
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
        if exclusion_data.is_empty():
            self.log('\tAll exclusion tables are valid')
        self.log('\n')

    def log_value_table_data(self) -> None:
        """Logs parsed invalid shared and non-shared value table data to
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
        """

        self.log('Value Tables:')
        shared_data = self.data.value_table.shared
        unexpected_names = list(
            map(
                lambda table: table.name,
                shared_data.unexpected
            )
        )
        self.log(f'\tUnexpected Shared Tables: {unexpected_names}')
        self.log(f'\tMissing Shared Tables: {shared_data.missing}')
        self.log()

        nonshared_data = self.data.value_table.nonshared
        unexpected_names = list(
            map(
                lambda table: table.name,
                nonshared_data.unexpected
            )
        )
        self.log(f'\tUnexpected Non-Shared Tables: {unexpected_names}')
        self.log(f'\tMissing Non-Shared Tables: {nonshared_data.missing}')
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
        """Logs all measure non-shared value tables to the output file.
        
        Non-Shared Value Table data:
            - Name
            - API name
            - Parameters
            - Columns
                - Name
                - API name
                - Unit
        """

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
        """Logs all measure calculations to the output file.
        
        Calculation data:
            - Name
            - API name
            - Unit
            - Parameters
        """

        self.log('Calculations:')
        for calculation in self.measure.calculations:
            if self.measure.calculations.index(calculation) != 0:
                self.log()
            self.log(f'\tCalculation Name: {calculation.name}\n'
                     f'\t\tAPI Name: {calculation.api_name}\n'
                     f'\t\tUnit: {calculation.unit}\n'
                     f'\t\tParameters: {calculation.determinants}')
        self.log('\n')

    def log_permutations(self) -> None:
        """Logs all measure permutations to the output file.
        
        Permutation data:
            - Reporting name
            - Verbose name
            - Mapped field
        """

        self.log('Permutations:')
        for err in self.data.permutation.invalid:
            self.log(f'\tInvalid Permutation ({err.reporting_name}) - '
                     f'{err.mapped_name} should be ' +
                     (f'{err.valid_names[0]}' if len(err.valid_names) == 1
                        else f'one of {err.valid_names}'))

        for perm_name in self.data.permutation.unexpected:
            self.log(f'\tUnexpected Permutation - {perm_name}')

        if self.data.permutation.is_empty():
            self.log('\tAll permutations are valid')
        self.log()

        for permutation in self.measure.permutations:
            perm_data = db.get_permutation_data(
                permutation.reporting_name
            )

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
        """Logs parsed invalid charaterization data to the output file.
        
        General data:
            - Missing characterizations
        
        Characterization specific data:
            - Header order (h3 -> h4 -> h5)
            - Reference tag spacing and required content
            - Sentence and punctuation spacing
        """

        self.log('Characterizations:')
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

    def log_data(self, data: ParserData):
        self.data = data

        self.log_measure_details()
        self.log_parameter_data()
        self.log_exclusion_table_data()
        self.log_value_table_data()
        self.log_value_tables()
        self.log_calculations()
        if self.measure.source == 'json':
            self.log_permutations()
        self.log_characterization_data()

        self.data = None
