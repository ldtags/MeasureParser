import re
import pandas as pd
import logging
import numbers
import datetime as dt
from typing import TypeVar, Callable, ParamSpec, Concatenate, overload, Any

from src.etrm import db, sanitizers, constants as cnst
from src.etrm.models import PermutationsTable, Measure
from src.etrm.connection import ETRMConnection
from src.permqaqc.models import FieldData, Severity


logger = logging.getLogger(__name__)


_T = TypeVar('_T')
_P = ParamSpec('_P')


def is_number(val) -> bool:
    """Determines if `val` is a number.

    Use as a callback function for filtering DataFrames.
    """

    return isinstance(val, numbers.Number)


def is_zero(val) -> bool:
    """Determines if `val` is a number with the value of 0.

    Use as a callback function for filtering DataFrames.
    """

    if not is_number(val):
        return False

    if val != 0:
        return False

    return True


def is_positive(val) -> bool:
    """Determines if `val` is a positive number.

    Use as a callback function for filtering DataFrames.
    """

    if not is_number(val):
        return False

    if val <= 0:
        return False

    return True


def is_negative(val) -> bool:
    """Determines if `val` is a negative number.

    Use as a callback function for filtering DataFrames.
    """

    if not is_number(val):
        return False

    if val > 0:
        return False

    return True


def is_greater_than(val, gt: numbers.Number) -> bool:
    """Determines if `val` is a number greater than `gt`.

    Use as a callback function for filtering DataFrames.
    """

    if not is_number(val):
        return False

    if val <= gt:
        return False

    return True


def is_less_than(val, lt: numbers.Number) -> bool:
    """Determines if `val` is a number less than `lt`.

    Use as a callback function for filtering DataFrames.
    """

    if not is_number(val):
        return False

    if val >= lt:
        return False

    return True


def qa_qc_method(func: Callable[_P, _T]
                ) -> Callable[Concatenate['PermutationQAQC', _P], _T]:
    """Ensures that the QA/QC tool permutations have been set before the
    decorated method is executed.

    Use when writing a method that relies on the QA/QC tool's permutation
    data.
    """
    
    def wrapper(self: 'PermutationQAQC',
                *args: _P.args,
                **kwargs: _P.kwargs
               ) -> _T:
        if self.permutations is None:
            return None

        val = func(self, *args, **kwargs)
        return val
    return wrapper


class PermutationQAQC:
    def __init__(self):
        self.__permutations: PermutationsTable | None = None
        self.__column_data: dict[str, FieldData] = {}
        self.__field_data: list[list[FieldData]] = []
        self.__statewide_id: str | None = None
        self.__version_id: str | None = None
        self.measure: Measure | None = None

    @property
    def permutations(self) -> PermutationsTable:
        return self.__permutations

    @permutations.setter
    def permutations(self, permutations: PermutationsTable) -> None:
        self.__permutations = permutations
        self.__normalize_headers()
        self.__column_data = {
            column: FieldData()
                for column
                in self.__permutations.data.columns
        }

        height, width = self.__permutations.data.shape
        self.__field_data = [
            [FieldData() for _ in range(width)]
                for _
                in range(height)
        ]

        try:
            statewide_col = self.__permutations.data[cnst.STATEWIDE_MEASURE_ID]
            self.__statewide_id = str(statewide_col[0])
        except (KeyError, IndexError, ValueError):
            self.__statewide_id = None

        try:
            version_col = self.__permutations.data[cnst.MEASURE_VERSION_ID]
            self.__version_id = str(version_col[0])
        except (KeyError, IndexError, ValueError):
            self.__version_id = None

    @property
    def column_data(self) -> dict[str, FieldData]:
        return self.__column_data

    @property
    def field_data(self) -> list[list[FieldData]]:
        return self.__field_data

    @property
    def statewide_id(self) -> str | None:
        return self.__statewide_id

    @property
    def version_id(self) -> str | None:
        return self.__version_id

    def __normalize_headers(self) -> None:
        if self.permutations is None:
            return

        name_map = db.get_permutation_name_map()
        if self.permutations.source == 'etrm':
            logger.info('Normalizing and validating eTRM permutation headers')
            for header in self.permutations.headers:
                if header not in name_map:
                    logger.warning(f'Unmapped permutation: {header}')
            self.permutations.data.rename(columns=name_map)
        elif self.permutations.source == 'csv':
            logger.info('Validating CSV permutation headers')
            verbose_names = set(name_map.values())
            for header in self.permutations.headers:
                if header not in verbose_names:
                    logger.warning(f'Unmapped permutation: {header}')

    @overload
    def set_permutations(self, csv_path: str) -> None:
        ...

    @overload
    def set_permutations(self, measure_id: str, api_key: str) -> None:
        ...

    def set_permutations(self, input: str, api_key: str | None=None) -> None:
        def parse_args() -> PermutationsTable:
            if api_key is None:
                return PermutationsTable(input)
            connection = ETRMConnection(api_key)
            sanitized_id = sanitizers.sanitize_measure_id(input)
            permutations = connection.get_permutations(sanitized_id)
            return permutations

        permutations = parse_args()
        self.permutations = permutations

    @overload
    def set_measure(self, measure_id: str, api_key: str) -> None:
        ...

    @overload
    def set_measure(self, measure: Measure) -> None:
        ...

    def set_measure(self,
                    input: Measure | str,
                    api_key: str | None=None
                   ) -> None:
        def parse_args() -> Measure:
            if isinstance(input, Measure):
                return input
            assert api_key is not None
            connection = ETRMConnection(api_key)
            sanitized_id = sanitizers.sanitize_measure_id(input)
            measure = connection.get_measure(sanitized_id)
            return measure

        measure = parse_args()
        self.measure = measure

    @qa_qc_method
    def move_column(self,
                    name: str,
                    default: str | None=None,
                    offset: int=-1,
                    relative: str | None=None
                   ) -> None:
        logger.info(f'Moving {name}')

        df = self.permutations.data
        if relative:
            try:
                df[relative]
            except KeyError:
                logger.warning(f'Missing relative column {relative}')
                return
            assert relative in df.columns
            rel_index = df.columns.get_loc(relative)
            assert offset >= 0 - rel_index
            assert offset <= len(df.columns) - rel_index
            index = rel_index + offset
        else:
            assert offset >= -1 and offset <= len(df.columns)
            if offset == -1:
                index = len(df.columns)
            else:
                index = offset

        try:
            col = df.pop(name)
            logger.info(f'{name} found')
        except KeyError:
            logger.info(f'{name} is missing')
            if default is not None:
                height, _ = df.shape
                vals = [default] * height
            else:
                vals = []
            col = pd.Series(vals, name=name)

        _, width = df.shape
        if index > width:
            self.permutations.data = df.join(col)
        else:
            self.permutations.data = pd.concat(
                [
                    df.iloc[:, :index],
                    col,
                    df.iloc[:, index:]
                ],
                axis=1,
                sort=False
            )

    @qa_qc_method
    def move_emerging_tech_column(self) -> None:
        logger.info('Moving Emerging Technologies column')

        df = self.permutations.data
        et = df.filter(regex=(r'Emerging Technologies .*'))
        if et.empty:
            logger.info('No ET column found')
            et_col = pd.Series(name=cnst.EMERGING_TECHNOLOGIES_PFY)
        else:
            et_col_name = et.columns[0]
            logger.info(f'ET column <{et_col_name}> found')
            et_col = df.pop(et_col_name)
            et_col.name = cnst.EMERGING_TECHNOLOGIES_PFY

        self.permutations.data = df.join(et_col)

    @qa_qc_method
    def move_etp_flag_column(self) -> None:
        logger.info('Moving ETP Flag column')

        df = self.permutations.data
        et_flag = df.filter(regex=(r'ETP Flag.*'))
        if et_flag.empty:
            logger.info('No ETP Flag column found')
            et_flag_col = pd.Series(name=cnst.ETP_FLAG)
        else:
            et_flag_col_name = et_flag.columns[0]
            logger.info(f'ETP Flag column <{et_flag_col_name}> found')
            et_flag_col = df.pop(et_flag_col_name)
            et_flag_col.name = cnst.ETP_FLAG

        etp_fy_index = int(df.columns.get_loc(cnst.ETP_FIRST_YEAR))
        self.permutations.data = pd.concat(
            [
                df.iloc[:, :etp_fy_index],
                et_flag_col,
                df.iloc[:, etp_fy_index:]
            ],
            axis=1,
            sort=False
        )

    @qa_qc_method
    def move_measure_specific_columns(self) -> None:
        df = self.permutations.data
        try:
            pa_index = df.columns.get_loc(cnst.PROGRAM_ADMINISTRATOR)
        except KeyError:
            logger.error(f'{cnst.PROGRAM_ADMINISTRATOR} is missing')
            raise

        try:
            fbpedr_index = df.columns.get_loc(cnst.FIRST_BASELINE_PEDR)
        except KeyError:
            logger.error(f'{cnst.FIRST_BASELINE_PEDR} is missing')
            raise

        ms_cols = df.iloc[:, pa_index + 1:fbpedr_index]
        if ms_cols.empty:
            return

        for ms_col_name in ms_cols.columns:
            logger.info(f'Moving {ms_col_name} [measure specific]')
            col = df.pop(ms_col_name)
            self.permutations.data = df.join(col)

    @qa_qc_method
    def move_restricted_perm_column(self) -> None:
        df = self.permutations.data
        try:
            df[cnst.RESTRICTED_PERMUTATION]
            return
        except KeyError:
            self.move_column(
                cnst.RESTRICTED_PERMUTATION,
                offset=1,
                relative=cnst.GSIA_VALUE
            )

    @qa_qc_method
    def insert_columns(self,
                       index: int,
                       name: str,
                       *names: str,
                       vals: list | None=None
                      ) -> None:
        df = self.permutations.data
        for offset, _name in enumerate([name, *names]):
            logger.info(f'Inserting {_name}')
            try:
                df[_name]
                logger.info(f'{_name} is already mapped')
            except KeyError:
                self.permutations.data = pd.concat(
                    [
                        df.iloc[:, :index + offset],
                        pd.Series(vals or [], name=name),
                        df.iloc[:, index + offset:]
                    ],
                    axis=1,
                    sort=False
                )

    @qa_qc_method
    def add_water_savings_columns(self) -> None:
        df = self.permutations.data
        try:
            df[cnst.WATER_MEASURE_TYPE]
            return
        except KeyError:
            pass

        try:
            vs_index = df.columns.get_loc(cnst.VERSION_SOURCE)
        except KeyError:
            logger.warning(f'{cnst.VERSION_SOURCE} is missing')
            return

        self.insert_columns(
            vs_index + 1,
            cnst.WATER_MEASURE_TYPE, 
            *cnst.WS_COLS
        )

    @qa_qc_method
    def add_cet_columns(self) -> None:
        df = self.permutations.data
        try:
            df[cnst.ELECTRIC_BENEFITS]
            return
        except KeyError:
            pass

        try:
            vs_index = df.columns.get_loc(cnst.VERSION_SOURCE)
        except KeyError:
            logger.warning(f'Missing {cnst.VERSION_SOURCE}')
            return

        self.insert_columns(vs_index + 1, *cnst.CET_COLS)

    def rearrange_columns(self) -> None:
        self.move_column(
            cnst.FIRST_BASELINE_CASE,
            relative=cnst.MEASURE_APPLICATION_TYPE
        )
        self.move_column(
            cnst.SECOND_BASELINE_CASE,
            relative=cnst.MEASURE_APPLICATION_TYPE
        )
        self.move_emerging_tech_column()
        self.move_etp_flag_column()
        self.move_column(cnst.NTG_VERSION, default=cnst.NTG_DEFAULT)
        self.move_column(cnst.EUL_VERSION)
        self.move_column(cnst.HOST_EUL_VERSION)
        self.move_measure_specific_columns()
        self.move_restricted_perm_column()
        self.add_water_savings_columns()
        self.add_cet_columns()

    @qa_qc_method
    def check_columns(self,
                      column: str,
                      *columns: str,
                      df: pd.DataFrame | None=None,
                      value: str | int | float | list | None=None,
                      func: Callable[[Any], bool] | None=None,
                      negate: bool=False,
                      description: str='Invalid field',
                      severity: Severity=Severity.CRITICAL
                     ) -> None:
        """Checks each field of `column` and `columns` and flags the field
        with `severity` if the field value matches `value`.

        Parameters:
            - `column` is the name of the column being checked.

            - `*columns` supports checking several columns.

            - `df` is a pandas DataFrame that must have been indexed from
            this instances current permutation data. This DataFrame will
            be checked instead of the full permutations DataFrame.

            - `value` specifies the invalid value for each field. If `None`,
            empty fields will be flagged. If value is a list of values, the
            field will be flagged if it contains any of the values in the
            list.

            - `func` defines a function that takes in a pandas field value
            and returns a `bool` specifying if the value is valid or not.
            Including this parameter will override `value` and `negate_value`.

            - `negate` specifies if the field value will be flagged if it
            is a match. If `True`, field values that do not match will be
            flagged. If `False`, field values that match will be flagged.

            - `description` specifies the text description of the issue that
            will be included within the flag.

            - `severity` specifies the level of severity applied to fields
            that failed the data validation.
        """

        logger.info(f'Checking for blanks with {severity.value} severity')

        if df is None:
            df = self.permutations.data

        for col_name in [column, *columns]:
            logger.info(f'Checking for blanks in {col_name}')
            try:
                col_index = int(df.columns.get_loc(col_name))
            except KeyError:
                logger.warning(f'Missing column: {col_name}')
                continue
            except ValueError as e:
                logger.error(str(e))
                continue

            if func is not None:
                validator = df[col_name].apply(func)
            else:
                if value is None:
                    validator = df[col_name].isna()
                elif isinstance(value, list):
                    for i, _value in enumerate(value):
                        if _value is None:
                            value[i] = pd.NA
                    validator = df[col_name].isin(value) 
                else:
                    validator = df[col_name].eq(value)

            if negate:
                check_col = df[col_name].loc[validator]
            else:
                check_col = df[col_name].loc[~validator]

            for index in check_col.index:
                try:
                    row_index = int(index)
                except ValueError as e:
                    logger.error(str(e))
                    continue

                field_data = self.field_data[row_index][col_index]
                field_data.add((description, severity))

    @qa_qc_method
    def validate_basic_descriptions(self) -> None:
        """Validates data fields within the `Offering Description`,
        `First Base Case Description`, `Measure Case Description` and
        `Standard Description` columns.
        
        Field is flagged if it is blank.
        """

        self.check_columns(
            cnst.OFFERING_DESCRIPTION,
            cnst.FIRST_BASE_CASE_DESCRIPTION,
            cnst.MEASURE_CASE_DESCRIPTION,
            cnst.STANDARD_DESCRIPTION,
            description='Value cannot be blank'
        )

    @qa_qc_method
    def validate_existing_description(self) -> None:
        """Validates data fields within the `Existing Description` column.

        Field is flagged if:
            - Measure Application Type is AR and the field is blank (critical)
            - Measure Application Type is not AR and the field is blank
            (optional)

        CET validation only requires text description for AR.
        """

        df = self.permutations.data
        self.check_columns(
            cnst.EXISTING_DESCRIPTION,
            df=df[df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')],
            description='Value cannot be blank'
        )

        self.check_columns(
            cnst.EXISTING_DESCRIPTION,
            df=df[~df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')],
            severity=Severity.OPTIONAL,
            description='Value cannot be blank'
        )

    @qa_qc_method
    def validate_sbc_description(self) -> None:
        """Validates data fields within the `Second Base Case Description`
        column.

        Field is flagged if:
            - Measure Application Type is AR and field is blank (critical)
            - Measure Application Type is not AR and field is not blank
            (critical)
        """

        df = self.permutations.data
        self.check_columns(
            cnst.SECOND_BASE_CASE_DESCRIPTION,
            df=df[df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')],
            description='Value cannot be blank'
        )

        self.check_columns(
            cnst.SECOND_BASE_CASE_DESCRIPTION,
            df=df[~df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')],
            negate=True,
            description='Value must be blank'
        )

    @qa_qc_method
    def validate_first_baseline_case(self) -> None:
        """Validates data fields within the `First Baseline Case` column.

        Field is flagged if:
            - field is not \'Existing\', \'Standard Practice\' or \'None\'
            (critical)
        """

        self.check_columns(
            cnst.FIRST_BASELINE_CASE,
            value=['Existing', 'Standard Practice', 'None'],
            negate=True,
            description='Value must be either \'Existing\','
                '\'Standard Practice\' or \'None\''
        )

    @qa_qc_method
    def validate_second_baseline_case(self) -> None:
        """Validates data fields within the `Second Baseline Case` column.

        Field is flagged if:
            - field is not \'Standard Practice\' or \'None\' (critical)
        """

        self.check_columns(
            cnst.SECOND_BASELINE_CASE,
            value=['Standard Practice', 'None'],
            negate=True,
            description='Value must be either \"Standard Practice\" or'
                ' \"None\"'
        )

    @qa_qc_method
    def validate_bldg_vint(self) -> None:
        """Validates data fields within the `Building Vintage` column.

        Field is flagged if:
            - field is \'Any\' (critical)

        E-5221 requirement.
        """

        self.check_columns(
            cnst.BUILDING_VINTAGE,
            value='Any',
            description='Value cannot be \'Any\''
        )

    def validate_descriptions(self) -> None:
        self.validate_basic_descriptions()
        self.validate_existing_description()
        self.validate_sbc_description()
        self.validate_first_baseline_case()
        self.validate_bldg_vint()

    @qa_qc_method
    def validate_first_baseline_ues(self) -> None:
        """Validates data fields within the `First Baseline - Peak Electric
        Demand Reduction`, `First Baseline - Electric Savings` and `First
        Baseline - Gas Savings` columns.

        Field is flagged if:
            - field is not a number (critical)
        """

        self.check_columns(
            *cnst.FIRST_BASELINE_UES_COLS,
            func=lambda val: not is_number(val),
            description='Value must be a number'
        )

    @qa_qc_method
    def validate_second_baseline_ues(self) -> None:
        """Validates data fields within the `Second Baseline - Peak Electric
        Demand Reduction`, `Second Baseline - Electric Savings` and `Second
        Baseline - Gas Savings` columns.

        Field is flagged if:
            - Measure Application Type is AR and field is not a number
            (critical)
            - Measure Application Type is AR and field is not zero (critical)
        """

        df = self.permutations.data
        self.check_columns(
            *cnst.SECOND_BASELINE_UES_COLS,
            df=df[df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')],
            func=lambda val: not is_number(val),
            description='Value must be a number'
        )

        self.check_columns(
            *cnst.SECOND_BASELINE_UES_COLS,
            df=df[~df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')],
            func=lambda val: not is_zero(val),
            description='Value must be zero'
        )

    def validate_savings(self) -> None:
        self.validate_first_baseline_ues()
        self.validate_second_baseline_ues()

    @qa_qc_method
    def validate_first_baseline_costs(self) -> None:
        """Validates data fields within the `First Baseline - Labor
        Cost` and `First Baseline - Material Cost` columns.

        Field is flagged if:
            - Measure Application Type is NC/NR and field is less than 0
            (critical)
            - Measure Application Type is NC/NR and all fields are 0 (minor)
            - Measure Application Type is not NC/NR and field is not 0
            (critical)
        """

        df = self.permutations.data
        self.check_columns(
            cnst.FIRST_BASELINE_LC,
            cnst.FIRST_BASELINE_MC,
            df=df[df[cnst.MEASURE_APPLICATION_TYPE].isin(['NC', 'NR'])],
            func=is_negative,
            description='Value must be a non-negative number'
        )

        non_zero_vals = df[
            df[cnst.MEASURE_APPLICATION_TYPE].isin(['NC', 'NR'])
                & ~df[cnst.FIRST_BASELINE_LC].eq(0)
        ]
        if non_zero_vals.empty:
            self.column_data[cnst.FIRST_BASELINE_LC].add(
                'All values are zero',
                Severity.MINOR
            )

        non_zero_vals = df[
            df[cnst.MEASURE_APPLICATION_TYPE].isin(['NC', 'NR'])
                & ~df[cnst.FIRST_BASELINE_MC].eq(0)
        ]
        if non_zero_vals.empty:
            self.column_data[cnst.FIRST_BASELINE_MC].add(
                'All values are zero',
                Severity.MINOR
            )

        self.check_columns(
            cnst.FIRST_BASELINE_LC,
            cnst.FIRST_BASELINE_MC,
            df=df[~df[cnst.MEASURE_APPLICATION_TYPE].isin(['NC', 'NR'])],
            func=lambda val: not is_zero(val),
            description='Value must be zero'
        )

    @qa_qc_method
    def validate_first_baseline_mtc(self) -> None:
        """Validates data fields within the `Measure Total Cost 1st Baseline`
        column.

        Field is flagged if:
            - field is not a number (critical)
            - field is less than or equal to 0 (minor)
        """

        self.check_columns(
            cnst.FIRST_BASELINE_MTC,
            func=lambda val: not is_number(val),
            description='Value must be a number'
        )

        self.check_columns(
            cnst.FIRST_BASELINE_MTC,
            severity=Severity.MINOR,
            func=lambda val: not is_positive(val),
            description='Value must be a positive number'
        )

    @qa_qc_method
    def validate_measure_costs(self) -> None:
        """Validates data fields within the `Measure Labor Cost` and `Measure
        Material Cost` columns.

        Field is flagged if:
            - field is a negative number (critical)
        """

        self.check_columns(
            cnst.MEASURE_LABOR_COST,
            cnst.MEASURE_MATERIAL_COST,
            func=is_negative,
            description='Value must be a positive number'
        )

    @qa_qc_method
    def validate_second_baseline_costs(self) -> None:
        """Validates data fields within the `Second Baseline - Labor
        Cost` and `Second Baseline - Material Cost` columns.

        Field is flagged if:
            - Measure Application Type is AR and field is negative (critical)
            - Measure Application Type is AR and all fields are 0 (minor)
            - Measure Application Type is not AR and field is not 0
            (critical)
        """

        df = self.permutations.data
        self.check_columns(
            cnst.SECOND_BASELINE_LC,
            cnst.SECOND_BASELINE_MC,
            df=df[df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')],
            func=lambda val: not is_negative(val),
            description='Value must be a non-negative number'
        )

        non_zero_vals = df[
            df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')
                & ~df[cnst.SECOND_BASELINE_LC].eq(0)
        ]
        if non_zero_vals.empty:
            self.column_data[cnst.SECOND_BASELINE_LC].add(
                'All values are zero',
                Severity.MINOR
            )

        non_zero_vals = df[
            df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')
                & ~df[cnst.SECOND_BASELINE_MC].eq(0)
        ]
        if non_zero_vals.empty:
            self.column_data[cnst.SECOND_BASELINE_MC].add(
                'All values are zero',
                Severity.MINOR
            )

        self.check_columns(
            cnst.SECOND_BASELINE_LC,
            cnst.SECOND_BASELINE_MC,
            df=df[~df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')],
            func=lambda val: not is_zero(val),
            description='Value must be zero'
        )

    @qa_qc_method
    def validate_second_baseline_mtc(self) -> None:
        """Validates data fields within the `Measure Total Cost 2nd Baseline`
        column.

        Field is flagged if:
            - field is not a number (critical)
            - Measure Application Type is AR and field is not a positive number
            (critical)
            - Measure Application Type is not AR and field is not zero
            (critical)
        """

        df = self.permutations.data
        self.check_columns(
            cnst.SECOND_BASELINE_MTC,
            severity=Severity.MINOR,
            df=df[df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')],
            func=lambda val: not is_positive(val),
            description='Value must be a positive number'
        )

        self.check_columns(
            cnst.SECOND_BASELINE_MTC,
            df=df[~df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')],
            func=lambda val: not is_zero(val),
            description='Value must be zero'
        )

    def validate_costs(self) -> None:
        self.validate_first_baseline_costs()
        self.validate_first_baseline_mtc()
        self.validate_measure_costs()
        self.validate_second_baseline_costs()
        self.validate_second_baseline_mtc()

    @qa_qc_method
    def validate_eul_id(self) -> None:
        """Validates data fields in the `Effective Useful Life ID` column.

        Field is flagged if:
            - field is not a valid EUL ID (critical)
        """

        valid_eul_ids = db.get_eul_ids()
        self.check_columns(
            cnst.EUL_ID,
            func=lambda val: val not in valid_eul_ids,
            description='Invalid EUL ID'
        )

    @qa_qc_method
    def validate_eul_years(self) -> None:
        """Validates data fields in the `EUL Years` column.

        Field is flagged if:
            - field is not a positive number (critical)
            - Measure Application Type is not AR and field does not equal
            the First Baseline - Life Cycle field (critical)
        """

        self.check_columns(
            cnst.EUL_YEARS,
            func=lambda val: not is_positive(val),
            description='Value must be a positive number'
        )

        df = self.permutations.data
        col_index = int(df.columns.get_loc(cnst.EUL_YEARS))
        invalid = df[
            ~df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')
                & ~df[cnst.EUL_YEARS].eq(df[cnst.FIRST_BASELINE_LIFE_CYCLE])
        ][cnst.EUL_YEARS]
        for index, value in invalid.items():
            correct_value = df.loc[index, cnst.FIRST_BASELINE_LIFE_CYCLE]
            self.field_data[int(index)][col_index].add(
                f'Invalid EUL Year: {value} must be {correct_value}'
            )

    @qa_qc_method
    def validate_rul_id(self) -> None:
        """Validates data fields within the `Remaining Useful Life ID` column.

        Field is flagged if:
            - Measure Appliucation Type is AR/AOE and field is not a valid EUL
            ID (critical)
            - Measure Application Type is not AR/AOE and field is not blank
            (critical)
        """

        df = self.permutations.data
        valid_eul_ids = db.get_eul_ids()
        self.check_columns(
            cnst.RUL_ID,
            df=df[df[cnst.MEASURE_APPLICATION_TYPE].isin(['AR', 'AOE'])],
            func=lambda val: val not in valid_eul_ids,
            description='Value is not a valid EUL ID'
        )

        self.check_columns(
            cnst.RUL_ID,
            df=df[~df[cnst.MEASURE_APPLICATION_TYPE].isin(['AR', 'AOE'])],
            negate=True,
            description='Value must be blank'
        )

    @qa_qc_method
    def validate_rul_years(self) -> None:
        """Validates data fields within the `RUL Years` column.

        Field is flagged if:
            - Measure Application Type is AR and field is not a positive
            number (critical)
            - Measure Application Type is AR and field is not less than
            the EUL Years field (critical)
            - Measure Application Type is not AR and field is not zero
            (critical)
        """

        df = self.permutations.data
        self.check_columns(
            cnst.RUL_YEARS,
            df=df[df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')],
            func=lambda val: not is_positive(val),
            description='Value must be a positive number'
        )

        invalid = df[
            df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')
                & (df[cnst.RUL_YEARS] >= df[cnst.EUL_YEARS])
        ][cnst.RUL_YEARS]
        col_index = int(df.columns.get_loc(cnst.RUL_YEARS))
        for index, value in invalid.items():
            eul_year = df.loc[index, cnst.EUL_YEARS]
            self.field_data[int(index)][col_index].add(
                f'Invalid RUL Year: {value} must be less than {eul_year}'
            )

        self.check_columns(
            cnst.RUL_YEARS,
            df=df[~df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')],
            func=lambda val: not is_zero(val),
            description='Value must be zero'
        )

    @qa_qc_method
    def validate_first_baseline_lc(self) -> None:
        """Validates data fields within the `First Baseline - Life Cycle`
        column.

        Field is flagged if:
            - field is not a positive number (critical)
        """

        self.check_columns(
            cnst.FIRST_BASELINE_LIFE_CYCLE,
            func=lambda val: not is_positive(val),
            description='Value must be a positive number'
        )

    @qa_qc_method
    def validate_second_baseline_lc(self) -> None:
        """Validates data fields within the `Second Baseline - Life Cycle`
        column.

        Field is flagged if:
            - Measure Application Type is AR and field is not a positive
            number (critical)
            - Measure Application Type is not AR and field is not zero
            (critical)
        """

        df = self.permutations.data
        self.check_columns(
            cnst.SECOND_BASELINE_LIFE_CYCLE,
            df=df[df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')],
            func=lambda val: not is_positive(val),
            description='Value must be a positive number'
        )

        self.check_columns(
            cnst.SECOND_BASELINE_LIFE_CYCLE,
            df=df[~df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')],
            func=lambda val: not is_zero(val),
            description='Value must be zero'
        )

    def validate_life(self) -> None:
        self.validate_eul_id()
        self.validate_eul_years()
        self.validate_rul_id()
        self.validate_rul_years()
        self.validate_first_baseline_lc()
        self.validate_second_baseline_lc()

    @qa_qc_method
    def validate_first_baseline_uec(self) -> None:
        """Validates data fields in the `First Baseline - UEC kW`,
        `First Baseline - UEC kWh` and `First Baseline - UEC Therm` columns.

        Field is flagged if:
            - field is not a number (critical)
        """

        self.check_columns(
            *cnst.FIRST_BASELINE_UEC_COLS,
            func=lambda val: not is_number(val),
            description='Value must be a number'
        )

    @qa_qc_method
    def validate_measure_uec(self) -> None:
        """Validates data fields in the `Measure UEC kW`, `Measure UEC kWh`
        and `Measure UEC Therm` columns.

        Field is flagged if:
            - field is not a number (critical)
        """

        self.check_columns(
            *cnst.MEASURE_UEC_COLS,
            func=lambda val: not is_number(val),
            description='Value must be a number'
        )

    @qa_qc_method
    def validate_second_baseline_uec(self) -> None:
        """Validates data fields in the `Second Baseline - UEC kW`,
        `Second Baseline - UEC kWh` and `Second Baseline - UEC Therm` columns.

        Field is flagged if:
            - Measure Application Type is AR and field is not a number
            (critical)
            - Measure Application Type is not AR and field is not zero
            (critical)
        """

        df = self.permutations.data
        self.check_columns(
            *cnst.SECOND_BASELINE_UEC_COLS,
            df=df[df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')],
            func=lambda val: not is_number(val),
            description='Value must be a number'
        )

        self.check_columns(
            *cnst.SECOND_BASELINE_UEC_COLS,
            df=df[~df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')],
            func=lambda val: not is_zero(val),
            description='Value must be zero'
        )

    def validate_uec(self) -> None:
        self.validate_first_baseline_uec()
        self.validate_measure_uec()
        self.validate_second_baseline_uec()

    @qa_qc_method
    def validate_delivery_type(self) -> None:
        """Validates data fields within the `Delivery Type` column.

        Field is flagged if:
            - field is not a valid Delivery Type ID (critical)
            - field's Delivery Type's start date is after the measure's
            start date (critical)
            - field's Delivery Type's end date is before the measure's
            start date (critical)
        """

        deliv_types = db.get_delivery_types()
        self.check_columns(
            cnst.DELIV_TYPE,
            func=lambda val: (
                val not in set(map(lambda item: item[0], deliv_types))
            ),
            description='Value is not a valid delivery type'
        )

        df = self.permutations.data
        deliv_index = int(df.columns.get_loc(cnst.DELIV_TYPE))

        late_deliv_types = df.loc[
            df[cnst.DELIV_TYPE].isin(deliv_types)
                & (
                    df[cnst.DELIV_TYPE].apply(
                        lambda val: (
                            dt.datetime.strptime(
                                deliv_types[val][0],
                                r'%Y/%m/%d'
                            )
                        )
                    ) > df[cnst.START_DATE].apply(
                        lambda val: dt.datetime.strptime(val, r'%Y-%m-%d')
                    )
                )
        ][cnst.DELIV_TYPE]
        for index in late_deliv_types.index:
            self.field_data[int(index)][deliv_index].add(
                'Delivery type cannot start after the measure\'s start date'
            )

        early_deliv_types = df.loc[
            df[cnst.DELIV_TYPE].isin(deliv_types)
                & (
                    df[cnst.DELIV_TYPE].apply(
                        lambda val: (
                            deliv_types[val][1] is None
                                or dt.datetime.strptime(
                                    str(deliv_types[val][1]),
                                    r'%Y/%m/%d'
                                )
                        )
                    ) < df[cnst.START_DATE].apply(
                        lambda val: dt.datetime.strptime(val, r'%Y-%m-%d')
                    )
                )
        ][cnst.DELIV_TYPE]
        for index in early_deliv_types.index:
            self.field_data[int(index)][deliv_index].add(
                'Delivery type cannot end before the measure\'s start date'
            )

    @qa_qc_method
    def validate_ntg_id(self) -> None:
        """Validates data fields within the `Net to Gross Ratio ID` column.

        Field is flagged if:
            - field is not a valid NTG ID (critical)
        """

        df = self.permutations.data
        ntg_id_index = int(df.columns.get_loc(cnst.NTG_ID))
        sector_index = int(df.columns.get_loc(cnst.SECTOR))
        invalid_ntg_ids = df[
            df.apply(
                lambda row: (
                    row.iloc[ntg_id_index] in db.get_exclusions(
                        cnst.SECTOR, row.iloc[sector_index]
                    )
                ),
                axis=1
            )
        ]
        for index in invalid_ntg_ids.index:
            self.field_data[int(index)][ntg_id_index].add(
                'Invalid NTG ID'
            )

    @qa_qc_method
    def validate_gsia_id(self) -> None:
        """Validates data fields within the `GSIA ID` column.

        Field is flagged if:
            - field is not a valid GSIA ID (critical)
        """

        df = self.permutations.data
        gsia_id_index = int(df.columns.get_loc(cnst.GSIA_ID))
        sector_index = int(df.columns.get_loc(cnst.SECTOR))
        invalid_gsia_ids = df[
            df.apply(
                lambda row: (
                    row.iloc[gsia_id_index] in db.get_exclusions(
                        cnst.SECTOR, row.iloc[sector_index]
                    )
                ),
                axis=1
            )
        ]
        for index in invalid_gsia_ids.index:
            self.field_data[int(index)][gsia_id_index].add(
                'Invalid GSIA ID'
            )

    @qa_qc_method
    def validate_ntg_value(self) -> None:
        """Validates data fields within the `NTG Value` column.

        Field is flagged if:
            - field is less than 0 or greater than 1 (critical)
        """

        self.check_columns(
            *cnst.NTG_VALUE_COLS,
            func=lambda val: is_negative(val) or is_greater_than(val, 1),
            description='Value must be >= 0 or <= 1'
        )

    @qa_qc_method
    def validate_gsia_value(self) -> None:
        """Validates data fields within the `GSIA Value` column.

        Field is flagged if:
            - field is less than 0 or greater than 1 (critical)
        """

        self.check_columns(
            cnst.GSIA_VALUE,
            func=lambda val: is_negative(val) or is_greater_than(val, 1),
            description='Value must be >= 0 or <= 1'
        )

    @qa_qc_method
    def validate_restricted_permutation(self) -> None:
        """Validates data fields within the `Restructed Permutation` column.

        Field is flagged if:
            - field is not 0 or 1 (critical)
        """

        self.check_columns(
            cnst.RESTRICTED_PERMUTATION,
            func=lambda val: val != 0 or val != 1,
            description='Value must be either a 0 or 1'
        )

    @qa_qc_method
    def validate_upstream_flag(self) -> None:
        """Validates data fields within the `Upstream Flag (True / False)`
        column.

        Field is flagged if:
            - field is not valid for the Program Year (critical)
        """

        df = self.permutations.data
        us_flag_index = int(df.columns.get_loc(cnst.UPSTREAM_FLAG))
        deliv_type_index = int(df.columns.get_loc(cnst.DELIV_TYPE))
        invalid_us_flags = df[
            df.apply(
                lambda row: (
                    row.iloc[us_flag_index] in list(
                        map(
                            lambda val: (
                                True if val == '0'
                                    else False if val == '1'
                                    else pd.NA if val == ''
                                    else val
                            ),
                            db.get_exclusions(
                                cnst.DELIV_TYPE,
                                row.iloc[deliv_type_index]
                            )
                        )
                    )
                ),
                axis=1
            )
        ][cnst.UPSTREAM_FLAG]
        for index, value in invalid_us_flags.items():
            deliv_type = df.loc[index, cnst.DELIV_TYPE]
            self.field_data[int(index)][us_flag_index].add(
                f'Invalid Upstream Flag: {value} us not valid for'
                f' delivery type {deliv_type}'
            )

    @qa_qc_method
    def validate_version_source(self) -> None:
        """Validates data fields within the `Version Source` column.

        Field is flagged if:
            - field is blank (critical)
            - field is not a valid Version Source ID (critical)
        """

        self.check_columns(
            cnst.VERSION_SOURCE,
            description='Value cannot be blank'
        )

        df = self.permutations.data
        valid_version_sources = db.get_version_sources()
        invalid_version_sources = df[
            ~df[cnst.VERSION_SOURCE].isin(valid_version_sources)
        ][cnst.VERSION_SOURCE]
        vs_index = int(df.columns.get_loc(cnst.VERSION_SOURCE))
        for index in invalid_version_sources.index:
            self.field_data[int(index)][vs_index].add(
                f'Invalid value, must be one of {valid_version_sources}',
                Severity.CRITICAL
            )

    @qa_qc_method
    def validate_cet_cols(self) -> None:
        """Validates data fields within the `Electric Benefits`,
        `Gas Benefits`, `TRC Cost - No Administrative Cost`, `PAC Cost - 
        No Administrative Cost`, `TRC Ratio - No Administrative Cost`, `PAC
        Ratio - No Administrative Cost`, `Total System Benefit`, `Water Energy
        Benefits`, `Other Benefits` and `Other Costs` columns.

        Field is flagged if:
            - field is blank (critical)
        """

        self.check_columns(
            *cnst.CET_COLS,
            description='Value cannot be blank'
        )

    def validate_implementation(self) -> None:
        self.validate_delivery_type()
        self.validate_ntg_id()
        self.validate_gsia_id()
        self.validate_ntg_value()
        self.validate_gsia_value()
        self.validate_restricted_permutation()
        self.validate_upstream_flag()
        self.validate_version_source()
        self.validate_cet_cols()

    @qa_qc_method
    def validate_water_measure_type(self) -> None:
        """Validates data fields within the `Water Measure Type` column.

        Field is flagged if:
            - field is not blank, \'Indoor\' or \'Ourdoor\'
        """

        self.check_columns(
            cnst.WATER_MEASURE_TYPE,
            value=[None, 'Indoor', 'Outdoor'],
            negate=True,
            description='Value must be either \"Blank\", \"Indoor\" or'
                ' \"Outdoor\"'
        )

    @qa_qc_method
    def validate_first_baseline_ws(self) -> None:
        """Validates data fields within the `First Baseline - Water Savings`,
        `First Baseline - IOU Embedded Water Savings` and `First Baseline -
        Total Water Savings` columns.

        Field is flagged if:
            - Water Measure Type is \'Indoor\' or \'Outdoor\' and field is
            not a number (critical)
            - Water Measure Type is blank and field is not zero (critical)
        """

        df = self.permutations.data
        for col_name in cnst.FIRST_BASELINE_WS_COLS:
            col_index = int(df.columns.get_loc(col_name))
            invalid = df[
                ~df[cnst.WATER_MEASURE_TYPE].isna()
                    & ~df[col_name].str.isnumeric()
            ][col_name]
            for index in invalid.index:
                self.field_data[int(index)][col_index].add(
                    'Value must be a number'
                )

            invalid = df[
                df[cnst.WATER_MEASURE_TYPE].isna()
                    & ~df[col_name].eq(0)
            ][col_name]
            for index in invalid.index:
                self.field_data[int(index)][col_index].add(
                    'Value must be 0'
                )

    @qa_qc_method
    def validate_second_baseline_ws(self) -> None:
        """Validates data fields within the `Second Baseline - Water Savings`,
        `Second Baseline - IOU Embedded Water Savings` and `Second Baseline -
        Total Water Savings` columns.

        Field is flagged if:
            - Measure Application Type is AR, Water Measure Type is \'Indoor\'
            or \'Outdoor\' and field is not a number (critical)
            - Measure Application Type is AR, Water Measure Type is blank
            and field is not zero (critical)
            - Measure Application Type is not AR and field is not zero (critical)
        """

        df = self.permutations.data
        for col_name in cnst.SECOND_BASELINE_WS_COLS:
            col_index = int(df.columns.get_loc(col_name))
            invalid = df[
                df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')
                    & ~df[cnst.WATER_MEASURE_TYPE].isna()
                    & ~df[col_name].str.isnumeric()
            ][col_name]
            for index in invalid.index:
                self.field_data[int(index)][col_index].add(
                    'Value must be a number'
                )

            invalid = df[
                ~df[col_name].eq(0)
                    & (
                        ~df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')
                            | df[cnst.WATER_MEASURE_TYPE].isna()
                    )
            ][col_name]
            for index in invalid.index:
                self.field_data[int(index)][col_index].add(
                    'Value must be 0'
                )

    def validate_water_savings(self) -> None:
        self.validate_water_measure_type()
        self.validate_first_baseline_ws()
        self.validate_second_baseline_ws()

    @qa_qc_method
    def validate_meas_tech_id(self) -> None:
        """Validated data fields for the `Measure Tech Type` column.

        Field is flagged if:
            - field is blank (critical)
        """

        self.check_columns(
            cnst.MEAS_TECH_ID,
            description='Value cannot be blank'
        )

    @qa_qc_method
    def validate_pre_tech_id(self) -> None:
        """Validates data fields for the `Pre-Existing Tech Type` column.

        Field is flagged if:
            - Measure Application Type is not NC/NR and field is blank
            (critical)
        """

        df = self.permutations.data
        self.check_columns(
            cnst.PRE_TECH_ID,
            df=df[~df[cnst.MEASURE_APPLICATION_TYPE].isin(['NC', 'NR'])],
            description='Value cannot be blank'
        )

    @qa_qc_method
    def validate_std_tech_id(self) -> None:
        """Validates data fields for the `Standard Tech Type` column.

        Field is flagged if:
            - Measure Application Type is not NC/NR and field is blank
            (critical)
        """

        df = self.permutations.data
        self.check_columns(
            cnst.STD_TECH_ID,
            df=df[~df[cnst.MEASURE_APPLICATION_TYPE].isin(['NC', 'NR'])],
            description='Value cannot be blank'
        )

    @qa_qc_method
    def validate_tech_groups(self) -> None:
        """Validates data fields for the `Measure Tech Group`, `Pre-Existing
        Tech Group` and `Standard Tech Group` columns.

        Field is flagged if:
            - field is not a valid Tech Group ID (critical)
        """

        df = self.permutations.data
        valid_tech_groups = db.get_technology_groups()
        for col_name in cnst.TECH_GROUP_COLS:
            col_index = int(df.columns.get_loc(col_name))
            invalid = df[~df[col_name].isin(valid_tech_groups)][col_name]
            for index, value in invalid.items():
                self.field_data[int(index)][col_index].add(
                    f'Invalid tech group: {value}, must be one of'
                    f' {valid_tech_groups}'
                )

    @qa_qc_method
    def validate_tech_types(self) -> None:
        """Validates data fields for the `Measure Tech Type`, `Pre-Existing
        Tech Type` and `Standard Tech Type` columns.

        Field is flagged if:
            - field is not a valid Tech Type ID (critical)
        """

        df = self.permutations.data
        valid_tech_types = db.get_technology_types()
        for col_name in cnst.TECH_TYPE_COLS:
            col_index = int(df.columns.get_loc(col_name))
            invalid = df[~df[col_name].isin(valid_tech_types)][col_name]
            for index, value in invalid.items():
                self.field_data[int(index)][col_index].add(
                    f'Invalid tech type: {value}, must be one of'
                    f' {valid_tech_types}'
                )

    def validate_tech(self) -> None:
        self.validate_meas_tech_id()
        self.validate_pre_tech_id()
        self.validate_std_tech_id()
        self.validate_tech_groups()
        self.validate_tech_types()

    @qa_qc_method
    def validate_etp_flag(self) -> None:
        """Validates data fields for the `ETP Flag` column.

        Field is flagged if:
            - field is not blank or field does not start with \'E\'
            (critical)
        """

        df = self.permutations.data
        col_index = int(df.columns.get_loc(cnst.ETP_FLAG))
        invalid = df[
            df[cnst.ETP_FLAG].isna()
                | ~df[cnst.ETP_FLAG].str.startswith('E')
        ][cnst.ETP_FLAG]
        for index, value in invalid.items():
            self.field_data[int(index)][col_index].add(
                f'Invalid ETP Flag: {value} must not be blank and must start'
                ' with \'E\''
            )

    @qa_qc_method
    def validate_ie_factor(self) -> None:
        """Validates data fields within the `IE Factor` column.

        Field is flagged if:
            - field is not \'Yes\' or \'No\' (critical)
        """

        df = self.permutations.data
        ief_index = int(df.columns.get_loc(cnst.IE_FACTOR))
        invalid = df[~df[cnst.IE_FACTOR].isin(['Yes', 'No'])][cnst.IE_FACTOR]
        for index, value in invalid.items():
            self.field_data[int(index)][ief_index].add(
                f'Invalid IE Factor value: {value}, must be either \'Yes\''
                    ' or \'No\''
            )

    @qa_qc_method
    def validate_ie_table_name(self) -> None:
        """Validates data fields within the `IE Table Name` column.

        Field is flagged if:
            - IE Factor is \'No\' and field is not \'NA\' (critical)
            - IE Factor is \'Yes\' and field is \'NA\' (critical)
        """

        df = self.permutations.data
        col_index = int(df.columns.get_loc(cnst.IE_TABLE_NAME))
        invalid = df[
            df[cnst.IE_FACTOR].eq('No') & ~df[cnst.IE_TABLE_NAME].eq('NA')
        ][cnst.IE_TABLE_NAME]
        for index, value in invalid.items():
            self.field_data[int(index)][col_index].add(
                f'Invalid IE Table Name: {value} must be \'NA\''
            )

        invalid = df[
            df[cnst.IE_FACTOR].eq('Yes')
                & df[cnst.IE_TABLE_NAME].eq('NA')
        ][cnst.IE_TABLE_NAME]
        for index, value in invalid.items():
            self.field_data[int(index)][col_index].add(
                f'Invalid IE Table Name: {value} must be a table name'
            )

    @qa_qc_method
    def validate_deer_measure_id(self) -> None:
        """Validates data fields within the `DEER Measure ID` column.

        Field is flagged if:
            - Measure Impact Type is \"Deem-DEER\" and field is blank
            (critical)
            - Measure Impact Type is not \"Deem-DEER\" and field is not
            blank (critical)
        """

        df = self.permutations.data
        col_index = int(df.columns.get_loc(cnst.DEER_MEAS_ID))
        invalid = df[
            df[cnst.MEAS_IMPACT_TYPE].eq('Deem-DEER')
                & df[cnst.DEER_MEAS_ID].isna()
        ][cnst.DEER_MEAS_ID]
        for index in invalid.index:
            self.field_data[int(index)][col_index].add(
                'Value cannot be blank'
            )

        invalid = df[
            ~df[cnst.MEAS_IMPACT_TYPE].eq('Deem-DEER')
                & ~df[cnst.DEER_MEAS_ID].isna()
        ][cnst.DEER_MEAS_ID]
        for index in invalid.index:
            self.field_data[int(index)][col_index].add(
                'Value must be blank'
            )

    @qa_qc_method
    def validate_measure_impact_type(self) -> None:
        """Validates data fields within the `Measure Impact Type` column.

        Field is flagged if:
            - Not a valid ID (critical)
            - ID's start date is after the measure's start date (critical)
            - ID's expiration date is before the measure's start date
            (critical)
        """

        df = self.permutations.data
        col_index = int(df.columns.get_loc(cnst.MEAS_IMPACT_TYPE))
        ntg_version_index = int(df.columns.get_loc(cnst.NTG_VERSION))
        ntg_id_index = int(df.columns.get_loc(cnst.NTG_ID))
        ntg_id_exclusions = db.get_exclusion_map(
            cnst.NTG_ID,
            cnst.MEAS_IMPACT_TYPE
        )
        ntg_version_exclusions = db.get_exclusion_map(
            cnst.NTG_VERSION,
            cnst.MEAS_IMPACT_TYPE
        )
        invalid = df[
            df.apply(
                lambda row: (
                    row.iloc[col_index] in [
                        *ntg_version_exclusions[row.iloc[ntg_version_index]],
                        *ntg_id_exclusions[row.iloc[ntg_id_index]]
                    ]
                ),
                axis=1
            )
        ][cnst.MEAS_IMPACT_TYPE]
        for index, value in invalid.items():
            self.field_data[int(index)][col_index].add(
                f'Invalid Measure Impact ID: {value}'
            )

        meas_impact_types = db.get_measure_impact_types()
        invalid = df[
            df[cnst.MEAS_IMPACT_TYPE].apply(
                lambda val: (
                    dt.datetime.strptime(
                        meas_impact_types[val][0],
                        r'%Y/%m/%d'
                    )
                )
            ) > df[cnst.START_DATE].apply(
                lambda val: dt.datetime.strptime(val, r'%Y-%m-%d')
            )
        ][cnst.MEAS_IMPACT_TYPE]
        for index, value in invalid.items():
            self.field_data[int(index)][col_index].add(
                f'Invalid Measure Impact ID: {value} cannot start after'
                ' the measure.'
            )

        invalid = df[
            df[cnst.MEAS_IMPACT_TYPE].apply(
                lambda val: (
                    meas_impact_types[val][1] is None
                        or dt.datetime.strptime(
                            str(meas_impact_types[val][1]),
                            r'%Y/%m/%d'
                        )
                )
            ) < df[cnst.START_DATE].apply(
                lambda val: dt.datetime.strptime(val, r'%Y-%m-%d')
            )
        ][cnst.MEAS_IMPACT_TYPE]
        for index, value in invalid.items():
            self.field_data[int(index)][col_index].add(
                f'Invalid Measure Impact ID: {value} cannot end before'
                ' the measure starts.'
            )

    @qa_qc_method
    def validate_measure_detail_id(self) -> None:
        """Validates data fields within the `Measure Detail ID` column.

        Field is flagged if:
            - field contains a duplicate (critical)
        """

        df = self.permutations.data
        col_index = int(df.columns.get_loc(cnst.MEAS_DETAIL_ID))
        duplicates = [
            col
                for _, col 
                in df.groupby(cnst.MEAS_DETAIL_ID)
                if len(col) > 1
        ]
        if len(duplicates) > 0:
            dupe_df = pd.concat(duplicates)[cnst.MEAS_DETAIL_ID]
            for index, value in dupe_df.items():
                self.field_data[int(index)][col_index].add(
                    f'Duplicate value: {value}'
                )

    def validate_implementation_eligibility(self) -> None:
        self.validate_ie_factor()
        self.validate_ie_table_name()
        self.validate_deer_measure_id()
        self.validate_measure_impact_type()
        self.validate_measure_detail_id()

    def validate_data(self) -> None:
        """Check for (potential) incorrect data types/values in the
        permutation fields.
        """

        self.validate_descriptions()
        self.validate_savings()
        self.validate_costs()
        self.validate_life()
        self.validate_uec()
        self.validate_implementation()
        self.validate_water_savings()
        self.validate_tech()
        self.validate_etp_flag()
        self.validate_implementation_eligibility()

    @qa_qc_method
    def check_exclusions(self,
                         *permutations: str,
                         valid: bool=True
                        ) -> None:
        df = self.permutations.data.copy()
        df.fillna('None')
        exclusions = db.get_all_exclusions(*permutations, valid=valid)
        permutations = list(permutations)
        for index in df.index:
            row = list(df.loc[index, permutations])
            if (row not in exclusions) != valid:
                for permutation in permutations:
                    col_index = df.columns.get_loc(permutation)
                    self.field_data[int(index)][int(col_index)].add(
                        f'Failed exclusion check',
                        Severity.MINOR
                    )

    def validate_exclusions(self) -> None:
        """Validates that all field data pass exclusion checks."""

        self.check_exclusions(
            cnst.MEASURE_APPLICATION_TYPE,
            cnst.BUILDING_VINTAGE
        )
        self.check_exclusions(cnst.SECTOR, cnst.BUILDING_TYPE)
        self.check_exclusions(cnst.SECTOR, cnst.NTG_ID)
        self.check_exclusions(cnst.SECTOR, cnst.ELEC_IMPACT_PROFILE_ID)
        self.check_exclusions(cnst.SECTOR, cnst.GSIA_ID)
        self.check_exclusions(cnst.SECTOR, cnst.BUILDING_HVAC)
        self.check_exclusions(cnst.MEAS_IMPACT_TYPE, cnst.VERSION)
        self.check_exclusions(
            cnst.PROGRAM_ADMINISTRATOR_TYPE,
            cnst.BUILDING_LOCATION
        )
        self.check_exclusions(
            cnst.PROGRAM_ADMINISTRATOR_TYPE,
            cnst.PROGRAM_ADMINISTRATOR
        )
        self.check_exclusions(cnst.DELIV_TYPE, cnst.UPSTREAM_FLAG)
        self.check_exclusions(
            cnst.MEASURE_APPLICATION_TYPE,
            cnst.DELIV_TYPE,
            valid=False
        )
        self.check_exclusions(cnst.BUILDING_HVAC, cnst.DELIV_TYPE, valid=False)
        self.check_exclusions(cnst.BUILDING_TYPE, cnst.DELIV_TYPE, valid=False)
        self.check_exclusions(
            cnst.NTG_ID,
            cnst.NTG_VERSION,
            cnst.MEAS_IMPACT_TYPE
        )
        self.check_exclusions(
            cnst.NTG_ID,
            cnst.NTG_VERSION,
            cnst.MEASURE_APPLICATION_TYPE
        )
        self.check_exclusions(cnst.NTG_ID, cnst.NTG_VERSION, cnst.DELIV_TYPE)
        self.check_exclusions(cnst.EUL_ID, cnst.EUL_VERSION, cnst.USE_CATEGORY)
        self.check_exclusions(
            cnst.EUL_ID,
            cnst.EUL_VERSION,
            cnst.USE_SUB_CATEGORY
        )
        self.check_exclusions(
            cnst.EUL_ID,
            cnst.EUL_VERSION,
            cnst.TECH_GROUP
        )
        self.check_exclusions(
            cnst.EUL_ID,
            cnst.EUL_VERSION,
            cnst.TECH_TYPE
        )
        self.check_exclusions(
            cnst.MEASURE_APPLICATION_TYPE,
            cnst.FIRST_BASELINE_CASE
        )
        self.check_exclusions(
            cnst.MEASURE_APPLICATION_TYPE,
            cnst.SECOND_BASELINE_CASE
        )

    def start(self) -> None:
        self.rearrange_columns()
        self.validate_data()
        self.validate_exclusions()
