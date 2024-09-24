import os
import re
import pandas as pd
import unittest as ut
from typing import Type

from src import _ROOT
from src.etrm import constants as cnst
from src.permqaqc import PermutationQAQC, FieldData, Severity
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

    def test_rearrange_columns(self) -> None:
        if self.tool is None:
            self.fail('Cannot run test without QA/QC tool')

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
 
 
class ComboTestCase(MeasureTestCase):
    def setUp(self) -> None:
        self.tool = tool = PermutationQAQC()
        # file_path = resources.get_path('combo_mat.xlsm')
        # convert_to_csv(file_path)
        file_path = resources.get_path('combo_mat.csv')
        tool.set_permutations(file_path)

    def assert_errors(self,
                      error_map: dict[str, dict[Severity, list[int]]]
                     ) -> None:
        for column, errors in error_map.items():
            existing_errors = self.tool.field_data.get_error_map(column=column)
            for severity, indexes in errors.items():
                actual_errors = set(
                    map(
                        lambda val: val + 2,
                        existing_errors[severity]
                    )
                )
                if actual_errors != set(indexes):
                    self.fail(f'Missing errors in {column}: {set(indexes).difference(actual_errors)}')

    def test_file(self) -> None:
        self.tool.rearrange_columns()
        self.tool.validate_data()
        with open(os.path.join(_ROOT, '..', 'outputs', 'test_results.txt'), 'w+') as fp:
            fp.write(str(self.tool.field_data))

        valid_errors: dict[str, dict[Severity, list[int]]] = {
            cnst.STATEWIDE_MEASURE_ID: {},
            cnst.MEASURE_VERSION_ID: {},
            cnst.MEASURE_NAME: {},
            cnst.OFFERING_ID: {},
            cnst.FIRST_BASE_CASE_DESCRIPTION: {
                CRITICAL: [2, 7]
            },
            cnst.SECOND_BASE_CASE_DESCRIPTION: {
                CRITICAL: [2, 7, 10, 19, 21]
            },
            cnst.MEASURE_CASE_DESCRIPTION: {
                CRITICAL: [6, 7]
            },
            cnst.EXISTING_DESCRIPTION: {
                OPTIONAL: [6, 19, 21],
                CRITICAL: [7]
            },
            cnst.STANDARD_DESCRIPTION: {
                CRITICAL: [6, 7]
            },
            cnst.FIRST_BASELINE_CASE: {
                CRITICAL: [4, 5, 6]
            },
            cnst.SECOND_BASELINE_CASE: {
                CRITICAL: [3, 5, 6, 7, 8]
            },
            cnst.MEASURE_APPLICATION_TYPE: {},
            cnst.BUILDING_TYPE: {},
            cnst.BUILDING_VINTAGE: {
                CRITICAL: [3, 7, 19, 21]
            },
            cnst.BUILDING_LOCATION: {},
            cnst.NORM_UNIT: {},
            cnst.SECTOR: {},
            cnst.PROGRAM_ADMINISTRATOR_TYPE: {},
            cnst.PROGRAM_ADMINISTRATOR: {},
            cnst.EUL_VERSION: {},
            cnst.FIRST_BASELINE_PEDR: {
                CRITICAL: [2, 4, 7, 8, 17, 18, 21, 22]
            },
            cnst.FIRST_BASELINE_ES: {
                CRITICAL: [2, 4, 7, 8, 17, 18, 21, 22]
            },
            cnst.FIRST_BASELINE_GS: {
                CRITICAL: [2, 4, 7, 8, 17, 18, 21, 22]
            },
            cnst.SECOND_BASELINE_PEDR: {
                CRITICAL: [2, 4, 5, 6, 8, 9, 17, 18, 19, 21, 22, 23]
            },
            cnst.SECOND_BASELINE_ES: {
                CRITICAL: [2, 4, 5, 6, 8, 9, 17, 18, 19, 21, 22, 23]
            },
            cnst.SECOND_BASELINE_GS: {
                CRITICAL: [2, 4, 5, 6, 8, 9, 17, 18, 19, 21, 22, 23]
            },
            cnst.FIRST_BASELINE_LC: {
                CRITICAL: [5, 6, 8, 9, 10, 19, 20, 21, 22]
            },
            cnst.FIRST_BASELINE_MC: {
                CRITICAL: [5, 6, 8, 9, 10, 17, 18, 19, 20, 21, 22]
            },
            cnst.FIRST_BASELINE_MTC: {
                CRITICAL: [2, 3, 7, 8],
                MINOR: [4, 5, 9]
            },
            cnst.MEASURE_LABOR_COST: {
                CRITICAL: [2, 3, 4, 7, 8, 9, 18, 19, 21, 22]
            },
            cnst.MEASURE_MATERIAL_COST: {
                CRITICAL: [2, 3, 4, 7, 8, 9, 18, 19, 21, 22]
            },
            cnst.SECOND_BASELINE_LC: {
                CRITICAL: [2, 3, 4, 5, 7, 17, 18, 19, 21, 22, 23]
            },
            cnst.SECOND_BASELINE_MC: {
                CRITICAL: [2, 3, 4, 5, 7, 17, 18, 19, 21, 22, 23]
            },
            cnst.SECOND_BASELINE_MTC: {
                CRITICAL: [3, 4, 5, 6, 8, 9, 17, 18, 19, 21, 22, 23],
                MINOR: [7]
            },
            cnst.LOC_COST_ADJ_ID: {},
            cnst.EUL_ID: {
                CRITICAL: [2, 3, 7, 8, 17, 18, 21, 22]
            },
            cnst.EUL_YEARS: {
                CRITICAL: [2, 2, 3, 4, 5, 7, 17, 17, 18, 19, 20, 21, 21, 22, 23, 24]
            },
            cnst.RUL_ID: {
                CRITICAL: [5, 6, 7, 8, 10, 17, 18, 19, 20, 21, 22]
            },
            cnst.RUL_YEARS: {
                CRITICAL: [3, 4, 5, 6, 7, 7, 8, 10, 10, 17, 18, 21, 22]
            },
            cnst.FIRST_BASELINE_LIFE_CYCLE: {
                CRITICAL: [2, 3, 4, 5, 7, 8, 9, 10, 17, 18, 19, 20, 21, 22, 23, 24]
            },
            cnst.SECOND_BASELINE_LIFE_CYCLE: {
                CRITICAL: [2, 3, 4, 7, 8, 9, 17, 18, 19, 21, 22, 23]
            },
            cnst.FIRST_BASELINE_UEC_KW: {
                CRITICAL: [2, 3, 7, 8, 17, 18, 21, 22]
            },
            cnst.FIRST_BASELINE_UEC_KWH: {
                CRITICAL: [2, 3, 7, 8, 17, 18, 21, 22]
            },
            cnst.FIRST_BASELINE_UEC_THERM: {
                CRITICAL: [2, 3, 7, 8, 17, 18, 21, 22]
            },
            cnst.SECOND_BASELINE_UEC_KW: {
                CRITICAL: [2, 3, 4, 7, 8, 17, 18, 19, 21, 22, 23]
            },
            cnst.SECOND_BASELINE_UEC_KWH: {
                CRITICAL: [2, 3, 4, 7, 8, 17, 18, 19, 21, 22, 23]
            },
            cnst.SECOND_BASELINE_UEC_THERM: {
                CRITICAL: [2, 3, 4, 7, 8, 17, 18, 19, 21, 22, 23]
            },
            cnst.MEASURE_UEC_KW: {
                CRITICAL: [2, 3, 7, 8, 17, 18, 21, 22]
            },
            cnst.MEASURE_UEC_KWH: {
                CRITICAL: [2, 3, 7, 8, 17, 18, 21, 22]
            },
            cnst.MEASURE_UEC_THERM: {
                CRITICAL: [2, 3, 7, 8, 17, 18, 21, 22]
            },
            cnst.DELIV_TYPE: {
                CRITICAL: [2, 3, 4, 7, 8, 9, 17, 18, 19, 21, 22, 23, 28, 29, 30]
            },
            cnst.NTG_ID: {},
            cnst.NTG_KWH: {},
            cnst.NTG_KW: {},
            cnst.NTG_THERMS: {},
            cnst.NTGR_COST: {},
            cnst.GSIA_ID: {
                CRITICAL: [2, 2, 3, 3, 7, 7, 8, 8, 17, 17, 18, 18, 21, 21, 22, 22]
            },
            cnst.RESTRICTED_PERMUTATION: {
                CRITICAL: [2, 3, 7, 8, 12, 17, 18, 21, 22]
            },
            cnst.ELEC_IMPACT_PROFILE_ID: {},
            cnst.GAS_IMPACT_PROFILE_ID: {},
            cnst.UNIT_GAS_INFRA_BENS: {},
            cnst.UNIT_REFRIG_COSTS: {},
            cnst.UNIT_REFRIG_BENS: {},
            cnst.UNIT_MISC_COSTS: {},
            cnst.UNIT_MISC_BENS: {},
            cnst.MISC_BENS_DESC: {},
            cnst.MARKET_EFFECTS_BENS: {},
            cnst.MARKET_EFFECTS_COSTS: {},
            cnst.MEASURE_INFLATION: {},
            cnst.COMBUST_TYPE: {},
            cnst.MEAS_IMPACT_CALC_TYPE: {},
            cnst.UPSTREAM_FLAG: {
                CRITICAL: [2, 30]
            },
            cnst.VERSION: {},
            cnst.VERSION_SOURCE: {
                CRITICAL: [2, 3, 7, 8, 17, 18, 21, 22]
            },
            cnst.ELECTRIC_BENEFITS: {
                CRITICAL: [2, 7, 17, 21]
            },
            cnst.GAS_BENEFITS: {
                CRITICAL: [2, 7, 17, 21]
            },
            cnst.TRC_COST_NAC: {
                CRITICAL: [2, 7, 17, 21]
            },
            cnst.PAC_COST_NAC: {
                CRITICAL: [2, 7, 17, 21]
            },
            cnst.TRC_RATIO_NAC: {
                CRITICAL: [2, 7, 17, 21]
            },
            cnst.PAC_RATIO_NAC: {
                CRITICAL: [2, 7, 17, 21]
            },
            cnst.TOTAL_SYSTEM_BENEFIT: {
                CRITICAL: [2, 7, 17, 21]
            },
            cnst.WATER_ENERGY_BENEFITS: {
                CRITICAL: [2, 7, 17, 21]
            },
            cnst.OTHER_BENEFITS: {
                CRITICAL: [2, 7, 17, 21]
            },
            cnst.OTHER_COSTS: {
                CRITICAL: [2, 7, 17, 21]
            },
            cnst.WATER_MEASURE_TYPE: {
                CRITICAL: [4, 9, 19, 23]
            },
            cnst.FIRST_BASELINE_WS: {
                CRITICAL: [2, 5, 10, 17, 20, 21, 24]
            },
            cnst.SECOND_BASELINE_WS: {
                CRITICAL: [2, 5, 7, 10, 17, 18, 21, 22]
            },
            cnst.FIRST_BASELINE_IOU_EWES: {
                CRITICAL: [2, 5, 10, 17, 20, 21, 24]
            },
            cnst.SECOND_BASELINE_IOU_EWES: {
                CRITICAL: [2, 5, 7, 10, 17, 18, 21, 22]
            },
            cnst.FIRST_BASELINE_TOTAL_EWES: {
                CRITICAL: [2, 5, 10, 17, 20, 21, 24]
            },
            cnst.SECOND_BASELINE_TOTAL_EWES: {
                CRITICAL: [2, 5, 7, 10, 17, 18, 21, 22]
            },
            cnst.MEAS_TECH_ID: {
                CRITICAL: [6, 7, 17, 21]
            },
            cnst.PRE_TECH_ID: {
                CRITICAL: [7, 17]
            },
            cnst.STD_TECH_ID: {
                CRITICAL: [6, 21]
            },
            cnst.TECH_GROUP: {
                CRITICAL: [2, 3, 7, 8, 17, 18, 21, 22]
            },
            cnst.PRE_TECH_GROUP: {
                CRITICAL: [2, 3, 7, 8, 17, 18, 21, 22]
            },
            cnst.STD_TECH_GROUP: {
                CRITICAL: [2, 3, 7, 8, 17, 18, 21, 22]
            },
            cnst.TECH_TYPE: {
                CRITICAL: [2, 3, 7, 8, 17, 18, 21, 22]
            },
            cnst.PRE_TECH_TYPE: {
                CRITICAL: [2, 3, 7, 8, 17, 18, 21, 22]
            },
            cnst.STD_TECH_TYPE: {
                CRITICAL: [2, 3, 7, 8, 17, 18, 21, 22]
            },
            cnst.USE_CATEGORY: {},
            cnst.USE_SUB_CATEGORY: {},
            cnst.BUILDING_HVAC: {},
            cnst.ETP_FLAG: {
                CRITICAL: [3, 4, 7, 8, 17, 18, 21, 22]
            },
            cnst.ETP_FIRST_YEAR: {},
            cnst.IE_FACTOR: {
                CRITICAL: [2, 3, 7, 8, 17, 18, 21, 22]
            },
            cnst.IE_TABLE_NAME: {
                CRITICAL: [4, 5, 6]
            },
            cnst.MEAS_QUALIFIER: {},
            cnst.DEER_MEAS_ID: {
                CRITICAL: [3, 5, 15]
            },
            cnst.MEAS_COST_ID: {},
            cnst.MEAS_IMPACT_TYPE: {
                CRITICAL: [2, 3, 4, 28, 29, 30]
            },
            cnst.OFFERING_DESCRIPTION: {
                CRITICAL: [6, 7]
            },
            cnst.SOURCE_DESCRIPTION: {},
            cnst.PA_LEAD: {},
            cnst.START_DATE: {},
            cnst.END_DATE: {},
            cnst.MEAS_DETAIL_ID: {
                CRITICAL: [2, 3, 11, 12]
            }
        }

        self.assert_errors(valid_errors)


def get_test_methods(test_case: Type[ut.TestCase]) -> list[ut.TestCase]:
    return [
        test_case(func)
            for func
            in dir(test_case)
            if (
                callable(getattr(test_case, func))
                    and func.startswith('test_')
            )
    ]


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
