import sys
from typing import Self

from measureparser.parserdata import (
    ParserData
)

class MeasureDataLogger:
    def __init__(self, output_path: str | None = None):
        self.output_path: str | None = output_path
        if output_path != None:
            self.out = open(output_path, 'w+')
        else:
            self.out = sys.stdout

        self.data: ParserData | None = None

    def close(self):
        if self.out != None:
            self.out.close()

    def __exit__(self):
        self.close()

    def __enter__(self) -> Self:
        return self
        
    def log(self, *values: object):
        print(*values, file=self.out)

    def log_measure_details(self) -> None:
        '''Logs measure identification details.
        
        Measure Details:
            - Version ID
            - Name
            - PA Lead
            - Start Date
            - End Date
        '''

        self.log('Measure Details:'
                 f'\n\tMeasure Version ID: {self.measure.version_id}'
                 f'\n\tMeasure Name: {self.measure.name}'
                 f'\n\tPA Lead: {self.measure.pa_lead}'
                 f'\n\tStart Date: {self.measure.start_date}'
                 f'\n\tEnd Date: {self.measure.end_date}')
        self.log('\n')

    def log_parameter_data(self) -> None:
        '''Logs all measure specific parameters and invalid measure parameter data.
        
        Invalid Parameter data:
            - Unexpected parameters
            - Missing parameters
        '''

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
        # for param_name in param_data.unordered:
        #     self.log(f'\t\t{param_name} is out of order')
        if param_data.unordered == []:
            self.log('\t\tAll shared parameters are in the correct order')
        else:
            self.log('\t\tShared parameters may be out of order, '
                     'please review the QA/QC guidelines')
        self.log('\n')

    def log_exclusion_table_data(self) -> None:
        '''Logs all measure exclusion tables and invalid exclusion table data.

        Exclusion Table data:
            - Name
            - Parameters

        Invalid Exclusion Table data:
            - Whitespace in name
            - Incorrect amount of hyphens in name
        '''

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
        if exclusion_data.is_empty():
            self.log('\tAll exclusion tables are valid')
        self.log('\n')

    def log_data(self, data: ParserData):
        self.data = data

        self.log_measure_details()
        self.log_parameter_data()
        self.log_exclusion_table_data()
        self.log_value_table_data()
        self.log_value_tables()
        self.log_calculations()
        self.log_permutation_data()
        self.log_permutations()
        self.log_characterization_data()

        self.data = None

