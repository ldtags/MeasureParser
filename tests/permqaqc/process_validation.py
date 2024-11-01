import os
import re
import json
import pandas as pd
import unittest as ut
from copy import deepcopy
from typing import Literal, Iterable

from src import _ROOT
from src.etrm import resources as etrm_resources
from src.etrm._constants import verbose as cnst
from src.permqaqc import PermutationQAQC, Severity
from tests.utils import get_test_methods
from tests.permqaqc import resources


class ValidationData:
    @property
    def ordered_columns(self) -> list[str]:
        return [
            cnst.STATEWIDE_MEASURE_ID,
            cnst.MEASURE_VERSION_ID,
            cnst.MEASURE_NAME,
            cnst.OFFERING_ID,
            cnst.FIRST_BASE_CASE_DESCRIPTION,
            cnst.SECOND_BASE_CASE_DESCRIPTION,
            cnst.MEASURE_CASE_DESCRIPTION,
            cnst.EXISTING_DESCRIPTION,
            cnst.STANDARD_DESCRIPTION,
            cnst.FIRST_BASELINE_CASE,
            cnst.SECOND_BASELINE_CASE,
            cnst.MEASURE_APPLICATION_TYPE,
            cnst.BUILDING_TYPE,
            cnst.BUILDING_VINTAGE,
            cnst.BUILDING_LOCATION,
            cnst.NORM_UNIT,
            cnst.SECTOR,
            cnst.PROGRAM_ADMINISTRATOR_TYPE,
            cnst.PROGRAM_ADMINISTRATOR,
            cnst.FIRST_BASELINE_PEDR,
            cnst.FIRST_BASELINE_ES,
            cnst.FIRST_BASELINE_GS,
            cnst.SECOND_BASELINE_PEDR,
            cnst.SECOND_BASELINE_ES,
            cnst.SECOND_BASELINE_GS,
            cnst.FIRST_BASELINE_LC,
            cnst.FIRST_BASELINE_MC,
            cnst.FIRST_BASELINE_MTC,
            cnst.MEASURE_LABOR_COST,
            cnst.MEASURE_MATERIAL_COST,
            cnst.SECOND_BASELINE_LC,
            cnst.SECOND_BASELINE_MC,
            cnst.SECOND_BASELINE_MTC,
            cnst.LOC_COST_ADJ_ID,
            cnst.EUL_ID,
            cnst.EUL_YEARS,
            cnst.RUL_ID,
            cnst.RUL_YEARS,
            cnst.FIRST_BASELINE_LIFE_CYCLE,
            cnst.SECOND_BASELINE_LIFE_CYCLE,
            cnst.FIRST_BASELINE_UEC_KW,
            cnst.FIRST_BASELINE_UEC_KWH,
            cnst.FIRST_BASELINE_UEC_THERM,
            cnst.SECOND_BASELINE_UEC_KW,
            cnst.SECOND_BASELINE_UEC_KWH,
            cnst.SECOND_BASELINE_UEC_THERM,
            cnst.MEASURE_UEC_KW,
            cnst.MEASURE_UEC_KWH,
            cnst.MEASURE_UEC_THERM,
            cnst.DELIV_TYPE,
            cnst.NTG_ID,
            cnst.NTG_KWH,
            cnst.NTG_KW,
            cnst.NTG_THERMS,
            cnst.NTGR_COST,
            cnst.GSIA_ID,
            cnst.GSIA_VALUE,
            cnst.RESTRICTED_PERMUTATION,
            cnst.ELEC_IMPACT_PROFILE_ID,
            cnst.GAS_IMPACT_PROFILE_ID,
            cnst.UNIT_GAS_INFRA_BENS,
            cnst.UNIT_REFRIG_COSTS,
            cnst.UNIT_REFRIG_BENS,
            cnst.UNIT_MISC_COSTS,
            cnst.MISC_COSTS_DESC,
            cnst.UNIT_MISC_BENS,
            cnst.MISC_BENS_DESC,
            cnst.MARKET_EFFECTS_BENS,
            cnst.MARKET_EFFECTS_COSTS,
            cnst.MEASURE_INFLATION,
            cnst.COMBUST_TYPE,
            cnst.MEAS_IMPACT_CALC_TYPE,
            cnst.UPSTREAM_FLAG,
            cnst.VERSION,
            cnst.VERSION_SOURCE,
            cnst.ELECTRIC_BENEFITS,
            cnst.GAS_BENEFITS,
            cnst.TRC_COST_NAC,
            cnst.PAC_COST_NAC,
            cnst.TRC_RATIO_NAC,
            cnst.PAC_RATIO_NAC,
            cnst.TOTAL_SYSTEM_BENEFIT,
            cnst.WATER_ENERGY_BENEFITS,
            cnst.OTHER_BENEFITS,
            cnst.OTHER_COSTS,
            cnst.WATER_MEASURE_TYPE,
            cnst.FIRST_BASELINE_WS,
            cnst.SECOND_BASELINE_WS,
            cnst.FIRST_BASELINE_IOU_EWES,
            cnst.SECOND_BASELINE_IOU_EWES,
            cnst.FIRST_BASELINE_TOTAL_EWES,
            cnst.SECOND_BASELINE_TOTAL_EWES,
            cnst.MEAS_TECH_ID,
            cnst.PRE_TECH_ID,
            cnst.STD_TECH_ID,
            cnst.TECH_GROUP,
            cnst.PRE_TECH_GROUP,
            cnst.STD_TECH_GROUP,
            cnst.TECH_TYPE,
            cnst.PRE_TECH_TYPE,
            cnst.STD_TECH_TYPE,
            cnst.USE_CATEGORY,
            cnst.USE_SUB_CATEGORY,
            cnst.BUILDING_HVAC,
            cnst.ETP_FLAG,
            cnst.ETP_FIRST_YEAR,
            cnst.IE_FACTOR,
            cnst.IE_TABLE_NAME,
            cnst.MEAS_QUALIFIER,
            cnst.DEER_MEAS_ID,
            cnst.MEAS_COST_ID,
            cnst.MEAS_IMPACT_TYPE,
            cnst.OFFERING_DESCRIPTION,
            cnst.SOURCE_DESCRIPTION,
            cnst.PA_LEAD,
            cnst.START_DATE,
            cnst.END_DATE,
            cnst.MEAS_DETAIL_ID,
            cnst.EMERGING_TECHNOLOGIES_PFY,
            cnst.NTG_VERSION,
            cnst.EUL_VERSION,
            cnst.HOST_EUL_VERSION,
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
    if re.fullmatch("^.+\.xls[bms]$") is None:
        raise RuntimeError(f"Invalid Excel file: {file_name_ext}")

    df = pd.read_excel(file_path, sheet_name=None, keep_default_na=False)
    file_name = file_name_ext.rsplit(".", 1)[0]
    csv_path_parts = [_ROOT, "..", "tests", "permqaqc" "resources", f"{file_name}.csv"]
    csv_path = os.path.join(*csv_path_parts)
    df[list(df.keys())[0]].to_csv(csv_path, index=False)


def merge_dicts(dict1: dict, dict2: dict) -> dict:
    merged_dict = deepcopy(dict1)
    for key, val in dict2.items():
        if key in merged_dict:
            if type(val) != type(merged_dict[key]):
                raise ValueError("Cannot merge dicts of different types")

            if isinstance(val, dict):
                merged_dict[key] = merge_dicts(merged_dict[key], val)
            elif isinstance(val, Iterable):
                merged_dict[key] = type(val)([*merged_dict[key], *val])
            else:
                merged_dict = [merged_dict[key], val]
        else:
            merged_dict[key] = val

    return merged_dict


class MeasureTestCase(ut.TestCase):
    tool: PermutationQAQC | None = None

    def tearDown(self) -> None:
        self.tool = None

    def data_fail(self, cause: Literal["name", "tool"]) -> None:
        description = ""
        match cause:
            case "name":
                description = (
                    "No test case name specified, are you using the" " base class?"
                )
            case "tool":
                description = "Cannot run test without QA/QC tool"
            case other:
                description = other

        self.fail(description)

    def assert_errors(self, error_map: dict[str, dict[str, list[int]]]) -> None:
        for column, errors in error_map.items():
            existing_errors = self.tool.field_data.get_error_map(column=column)
            for severity, indexes in errors.items():
                actual_errors = set(
                    map(lambda val: val + 2, existing_errors[Severity[severity]])
                )

                if actual_errors != set(indexes):
                    err_msg = f"Incorrect errors in {column}"
                    missing_errors = set(indexes).difference(actual_errors)
                    if missing_errors != set():
                        err_msg += (
                            f"\n  Missing {severity} errors: {list(missing_errors)}"
                        )

                    extra_errors = actual_errors.difference(set(indexes))
                    if extra_errors != set():
                        err_msg += f"\n  Extra {severity} errors: {list(extra_errors)}"

                    self.fail(err_msg)

    def test_rearrange_columns(self) -> None:
        if self.tool is None:
            self.data_fail("tool")

        self.tool.rearrange_columns()
        columns = list(self.tool.permutations.data.columns)

        try:
            heul_index = columns.index(cnst.HOST_EUL_VERSION)
        except ValueError:
            self.fail(f"Missing the {cnst.HOST_EUL_VERSION} column")

        # remove measure specific permutations
        columns = columns[0 : heul_index + 1]

        self.assertEqual(
            len(columns),
            len(ValidationData.ordered_columns),
            msg=f"Missing cols: {list(set(ValidationData.ordered_columns).difference(columns))}",
        )
        for tool_column, ordered_column in zip(columns, ValidationData.ordered_columns):
            match ordered_column:
                case cnst.ETP_FLAG:
                    self.assertRegex(tool_column, rf"^{cnst.ETP_FLAG_RE}$")
                case _:
                    self.assertEqual(tool_column, ordered_column)

    def test_validate_data(self) -> None:
        self.tool.rearrange_columns()
        self.tool.validate_data()
        try:
            self.assert_errors(self.data_errors)
        except AttributeError:
            pass

    def test_validate_exclusions(self) -> None:
        self.tool.rearrange_columns()
        self.tool.validate_exclusions()
        try:
            self.assert_errors(self.exclusion_errors)
        except AttributeError:
            pass

    def test_validate_calculations(self) -> None:
        self.tool.rearrange_columns()
        self.tool.validate_calculations()
        try:
            self.assert_errors(self.calculation_errors)
        except AttributeError:
            pass

    def test_start(self) -> None:
        self.tool.start()
        try:
            self.assert_errors(self.all_errors)
        except AttributeError:
            pass


class LocalTestCase(MeasureTestCase):
    name: str | None = None

    @property
    def data_errors(self) -> dict[str, dict[str, list[int]]]:
        return self.get_errors("data_validation_errors.json")

    @property
    def exclusion_errors(self) -> dict[str, dict[str, list[int]]]:
        return self.get_errors("exclusion_validation_errors.json")

    @property
    def calculation_errors(self) -> dict[str, dict[str, list[int]]]:
        return self.get_errors("calculation_validation_errors.json")

    @property
    def all_errors(self) -> dict[str, dict[str, list[int]]]:
        errors = merge_dicts(self.data_errors, self.exclusion_errors)
        errors = merge_dicts(errors, self.calculation_errors)
        return errors

    def setUp(self) -> None:
        if self.name is None:
            self.data_fail("name")

        self.tool = tool = PermutationQAQC()
        file_path = resources.get_path(self.name, "permutations.csv")
        tool.set_permutations(file_path)

        global cnst
        cnst = self.tool.permutations.columns

    def get_path(self, file_name: str, exists: bool = True) -> str:
        if self.name is None:
            self.data_fail("name")

        return resources.get_path(self.name, file_name, exists=exists)

    def get_errors(self, file_name: str) -> dict[str, dict[str, list[int]]]:
        json_path = self.get_path(file_name)
        with open(json_path, "r") as fp:
            valid_errors = json.load(fp)

        return valid_errors


class EtrmTestCase(MeasureTestCase):
    measure_id: str | None = None

    def setUp(self) -> None:
        if self.measure_id is None:
            self.data_fail("measure id")

        self.tool = tool = PermutationQAQC()
        tool.set_permutations(self.measure_id, etrm_resources.get_api_key())

        global cnst
        cnst = self.tool.permutations.columns


class ComboTestCase(LocalTestCase):
    name = "combo_mat"


class SWAP006_03(EtrmTestCase):
    measure_id = "SWAP006-03"


def suite() -> ut.TestSuite:
    suite = ut.TestSuite()
    test_cases: list[MeasureTestCase] = [SWAP006_03]

    for test_case in test_cases:
        methods = get_test_methods(test_case)
        suite.addTests(methods)

    return suite


if __name__ == "__main__":
    runner = ut.TextTestRunner()
    runner.run(suite())
