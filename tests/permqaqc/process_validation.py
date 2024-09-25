import os
import re
import json
import pandas as pd
import unittest as ut
from typing import Literal

from src import _ROOT
from src.etrm import constants as cnst
from src.permqaqc import PermutationQAQC, Severity
from tests.utils import get_test_methods
from tests.permqaqc import resources


COLUMN_ORDER = [
    cnst.STATEWIDE_MEASURE_ID, cnst.MEASURE_VERSION_ID, cnst.MEASURE_NAME,
    cnst.OFFERING_ID, cnst.FIRST_BASE_CASE_DESCRIPTION,
    cnst.SECOND_BASE_CASE_DESCRIPTION, cnst.MEASURE_CASE_DESCRIPTION,
    cnst.EXISTING_DESCRIPTION, cnst.STANDARD_DESCRIPTION,
    cnst.FIRST_BASELINE_CASE, cnst.SECOND_BASELINE_CASE,
    cnst.MEASURE_APPLICATION_TYPE, cnst.BUILDING_TYPE, cnst.BUILDING_VINTAGE,
    cnst.BUILDING_LOCATION, cnst.NORM_UNIT, cnst.SECTOR,
    cnst.PROGRAM_ADMINISTRATOR_TYPE, cnst.PROGRAM_ADMINISTRATOR,
    cnst.FIRST_BASELINE_PEDR, cnst.FIRST_BASELINE_ES, cnst.FIRST_BASELINE_GS,
    cnst.SECOND_BASELINE_PEDR, cnst.SECOND_BASELINE_ES,
    cnst.SECOND_BASELINE_GS, cnst.FIRST_BASELINE_LC, cnst.FIRST_BASELINE_MC,
    cnst.FIRST_BASELINE_MTC, cnst.MEASURE_LABOR_COST,
    cnst.MEASURE_MATERIAL_COST, cnst.SECOND_BASELINE_LC,
    cnst.SECOND_BASELINE_MC, cnst.SECOND_BASELINE_MTC, cnst.LOC_COST_ADJ_ID,
    cnst.EUL_ID, cnst.EUL_YEARS, cnst.RUL_ID, cnst.RUL_YEARS,
    cnst.FIRST_BASELINE_LIFE_CYCLE, cnst.SECOND_BASELINE_LIFE_CYCLE,
    cnst.FIRST_BASELINE_UEC_KW, cnst.FIRST_BASELINE_UEC_KWH,
    cnst.FIRST_BASELINE_UEC_THERM, cnst.SECOND_BASELINE_UEC_KW,
    cnst.SECOND_BASELINE_UEC_KWH, cnst.SECOND_BASELINE_UEC_THERM,
    cnst.MEASURE_UEC_KW, cnst.MEASURE_UEC_KWH, cnst.MEASURE_UEC_THERM,
    cnst.DELIV_TYPE, cnst.NTG_ID, cnst.NTG_KWH, cnst.NTG_KW, cnst.NTG_THERMS,
    cnst.NTGR_COST, cnst.GSIA_ID, cnst.GSIA_VALUE, cnst.RESTRICTED_PERMUTATION,
    cnst.ELEC_IMPACT_PROFILE_ID, cnst.GAS_IMPACT_PROFILE_ID,
    cnst.UNIT_GAS_INFRA_BENS, cnst.UNIT_REFRIG_COSTS, cnst.UNIT_REFRIG_BENS,
    cnst.UNIT_MISC_COSTS, cnst.MISC_COSTS_DESC, cnst.UNIT_MISC_BENS,
    cnst.MISC_BENS_DESC, cnst.MARKET_EFFECTS_BENS, cnst.MARKET_EFFECTS_COSTS,
    cnst.MEASURE_INFLATION, cnst.COMBUST_TYPE, cnst.MEAS_IMPACT_CALC_TYPE,
    cnst.UPSTREAM_FLAG, cnst.VERSION, cnst.VERSION_SOURCE,
    cnst.ELECTRIC_BENEFITS, cnst.GAS_BENEFITS, cnst.TRC_COST_NAC,
    cnst.PAC_COST_NAC, cnst.TRC_RATIO_NAC, cnst.PAC_RATIO_NAC,
    cnst.TOTAL_SYSTEM_BENEFIT, cnst.WATER_ENERGY_BENEFITS, cnst.OTHER_BENEFITS,
    cnst.OTHER_COSTS, cnst.WATER_MEASURE_TYPE, cnst.FIRST_BASELINE_WS,
    cnst.SECOND_BASELINE_WS, cnst.FIRST_BASELINE_IOU_EWES,
    cnst.SECOND_BASELINE_IOU_EWES, cnst.FIRST_BASELINE_TOTAL_EWES,
    cnst.SECOND_BASELINE_TOTAL_EWES, cnst.MEAS_TECH_ID, cnst.PRE_TECH_ID,
    cnst.STD_TECH_ID, cnst.TECH_GROUP, cnst.PRE_TECH_GROUP,
    cnst.STD_TECH_GROUP, cnst.TECH_TYPE, cnst.PRE_TECH_TYPE,
    cnst.STD_TECH_TYPE, cnst.USE_CATEGORY, cnst.USE_SUB_CATEGORY,
    cnst.BUILDING_HVAC, cnst.ETP_FLAG, cnst.ETP_FIRST_YEAR, cnst.IE_FACTOR,
    cnst.IE_TABLE_NAME, cnst.MEAS_QUALIFIER, cnst.DEER_MEAS_ID,
    cnst.MEAS_COST_ID, cnst.MEAS_IMPACT_TYPE, cnst.OFFERING_DESCRIPTION,
    cnst.SOURCE_DESCRIPTION, cnst.PA_LEAD, cnst.START_DATE, cnst.END_DATE,
    cnst.MEAS_DETAIL_ID, cnst.EMERGING_TECHNOLOGIES_PFY, cnst.NTG_VERSION,
    cnst.EUL_VERSION, cnst.HOST_EUL_VERSION
]


OPTIONAL = Severity.OPTIONAL
MINOR = Severity.MINOR
CRITICAL = Severity.CRITICAL


def convert_to_csv(file_path: str) -> None:
    """Converts data from the first sheet of the Excel file at `file_path`
    to a CSV file.

    Excel file must be formatted like an eTRM measure permutations CSV file.
    """

    file_name_ext = os.path.basename(file_path)
    if re.fullmatch('^.+\.xls[bms]$') is None:
        raise RuntimeError(f'Invalid Excel file: {file_name_ext}')

    df = pd.read_excel(file_path, sheet_name=None, keep_default_na=False)    
    file_name = file_name_ext.rsplit('.', 1)[0]
    csv_path_parts = [
        _ROOT,
        '..',
        'tests',
        'permqaqc'
        'resources',
        f'{file_name}.csv'
    ]
    csv_path = os.path.join(*csv_path_parts)
    df[list(df.keys())[0]].to_csv(csv_path, index=False)


class MeasureTestCase(ut.TestCase):
    tool: PermutationQAQC | None = None
    name: str | None = None

    @property
    def data_errors(self) -> dict[str, dict[str, list[int]]]:
        json_path = self.get_path('data_validation_errors.json')
        with open(json_path, 'r') as fp:
            valid_errors = json.load(fp)

        return valid_errors

    @property
    def exclusion_errors(self) -> dict[str, dict[str, list[int]]]:
        json_path = self.get_path('exclusion_validation_errors.json')
        with open(json_path, 'r') as fp:
            valid_errors = json.load(fp)

        return valid_errors

    @property
    def all_errors(self) -> dict[str, dict[str, list[int]]]:
        valid_errors = self.data_errors
        for column, errors in self.exclusion_errors.items():
            if column in valid_errors:
                for severity, indexes in errors.items():
                    if severity in valid_errors[column]:
                        valid_errors[column][severity].extend(indexes)
                    else:
                        valid_errors[column][severity] = indexes
            else:
                valid_errors[column] = errors

        return valid_errors

    def data_fail(self, cause: Literal['name', 'tool']) -> None:
        description = ''
        match cause:
            case 'name':
                description = (
                    'No test case name specified, are you using the'
                    ' base class?'
                )
            case 'tool':
                description = 'Cannot run test without QA/QC tool'
            case other:
                description = other

        self.fail(description)

    def setUp(self) -> None:
        if self.name is None:
            self.data_fail('name')

        self.tool = tool = PermutationQAQC()
        file_path = resources.get_path(self.name, 'permutations.csv')
        tool.set_permutations(file_path)

    def tearDown(self) -> None:
        self.tool = None

    def get_path(self, file_name: str, exists: bool=True) -> str:
        if self.name is None:
            self.data_fail('name')

        return resources.get_path(self.name, file_name, exists=exists)

    def assert_errors(self,
                      error_map: dict[str, dict[str, list[int]]]
                     ) -> None:
        for column, errors in error_map.items():
            existing_errors = self.tool.field_data.get_error_map(column=column)
            for severity, indexes in errors.items():
                actual_errors = set(
                    map(
                        lambda val: val + 2,
                        existing_errors[Severity[severity]]
                    )
                )
                if actual_errors != set(indexes):
                    self.fail(f'Missing errors in {column}: {set(indexes).difference(actual_errors)}')

    def test_rearrange_columns(self) -> None:
        if self.tool is None:
            self.data_fail('tool')

        self.tool.rearrange_columns()
        columns = list(self.tool.permutations.data.columns)

        try:
            heul_index = columns.index(cnst.HOST_EUL_VERSION)
        except ValueError:
            self.fail(f'Missing the {cnst.HOST_EUL_VERSION} column')

        # remove measure specific permutations
        columns = columns[0:heul_index + 1]

        self.assertEqual(
            len(columns),
            len(COLUMN_ORDER),
            msg=f'Missing cols: {list(set(COLUMN_ORDER).difference(columns))}'
        )
        for tool_column, ordered_column in zip(columns, COLUMN_ORDER):
            match ordered_column:
                case cnst.ETP_FLAG:
                    self.assertRegex(tool_column, r'^ETP Flag.*$')
                case _:
                    self.assertEqual(tool_column, ordered_column)

    # def test_validate_data(self) -> None:
    #     self.tool.rearrange_columns()
    #     self.tool.validate_data()
    #     self.assert_errors(self.data_errors)

    # def test_validate_exclusions(self) -> None:
    #     self.tool.rearrange_columns()
    #     self.tool.validate_exclusions()
    #     self.assert_errors(self.exclusion_errors)

    def test_validate_calculations(self) -> None:
        self.tool.rearrange_columns()
        self.tool.validate_calculations()
        path = self.get_path('calculation_validation_errors.json', exists=False)
        self.tool.field_data.to_json(path)

    # def test_start(self) -> None:
    #     self.tool.start()
    #     self.assert_errors(self.all_errors)


class ComboTestCase(MeasureTestCase):
    name = 'combo_mat'


def suite() -> ut.TestSuite:
    suite = ut.TestSuite()
    test_cases: list[MeasureTestCase] = [
        ComboTestCase
    ]

    for test_case in test_cases:
        methods = get_test_methods(test_case)
        suite.addTests(methods)

    return suite


if __name__ == '__main__':
    runner = ut.TextTestRunner()
    runner.run(suite())
