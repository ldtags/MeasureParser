import pandas as pd
import logging
import numbers
import datetime as dt
from typing import TypeVar, Callable, ParamSpec, Concatenate, overload, Any

from src.exceptions import ParserError
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

    try:
        float(val)
        return True
    except ValueError:
        return False


def is_zero(val) -> bool:
    """Determines if `val` is a number with the value of 0.

    Use as a callback function for filtering DataFrames.
    """

    if not is_number(val):
        return False

    if float(val) != 0:
        return False

    return True


def is_positive(val) -> bool:
    """Determines if `val` is a positive number.

    Use as a callback function for filtering DataFrames.
    """

    if not is_number(val):
        return False

    if float(val) <= 0:
        return False

    return True


def is_negative(val) -> bool:
    """Determines if `val` is a negative number.

    Use as a callback function for filtering DataFrames.
    """

    if not is_number(val):
        return False

    if float(val) >= 0:
        return False

    return True


def is_greater_than(val, gt: numbers.Number) -> bool:
    """Determines if `val` is a number greater than `gt`.

    Use as a callback function for filtering DataFrames.
    """

    if not is_number(val):
        return False

    if float(val) <= gt:
        return False

    return True


def is_less_than(val, lt: numbers.Number) -> bool:
    """Determines if `val` is a number less than `lt`.

    Use as a callback function for filtering DataFrames.
    """

    if not is_number(val):
        return False

    if float(val) >= lt:
        return False

    return True


def occurs_before(checked_date: str | None, base_date: str) -> bool:
    """Determines if `checked_date` occurs before `base_date`.

    Date Formats:
        `checked_date`: YYYY/MM/DD
        `base_date`:    YYYY-MM-DD

    Date formats were determined by the formats stored in the
    eTRM and local database.

    Use as a callback function for filtering DataFrames.
    """

    if checked_date is None:
        return False

    return dt.datetime.strptime(
        checked_date,
        r'%Y/%m/%d'
    ) < dt.datetime.strptime(
        base_date,
        r'%Y-%m-%d'
    )


def occurs_after(checked_date: str | None, base_date: str) -> bool:
    """Determines if `checked_date` occurs after `base_date`.

    Date Formats:
        `checked_date`: YYYY/MM/DD
        `base_date`:    YYYY-MM-DD

    Date formats were determined by the formats stored in the
    eTRM and local database.

    Use as a callback function for filtering DataFrames.
    """

    if checked_date is None:
        return False

    return dt.datetime.strptime(
        checked_date,
        r'%Y/%m/%d'
    ) > dt.datetime.strptime(
        base_date,
        r'%Y-%m-%d'
    )


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
        self.__field_data: FieldData | None = None
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
        self.__field_data = FieldData(self.__permutations.headers)

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
    def field_data(self) -> FieldData | None:
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
            et_flag_col.name = et_flag_col_name

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
            if func is not None:
                validator = df[col_name].apply(func)
            else:
                if value is None:
                    validator = (df[col_name].isna() | df[col_name].eq(''))
                elif isinstance(value, list):
                    for i, _value in enumerate(value):
                        if _value is None:
                            value[i] = pd.NA
                    validator = df[col_name].isin(value) 
                else:
                    validator = df[col_name].eq(value)

            if negate:
                check_col = df[col_name].loc[~validator]
            else:
                check_col = df[col_name].loc[validator]

            for index in check_col.index:
                try:
                    row_index = int(index)
                except ValueError as e:
                    logger.error(str(e))
                    continue

                self.field_data.add(
                    column=col_name,
                    description=description,
                    severity=severity,
                    y=row_index
                )

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

        df = self.permutations.data
        valid_fbc = ['Existing', 'Standard Practice', 'None']
        invalid = df[
            ~df[cnst.FIRST_BASELINE_CASE].isin(valid_fbc)
        ][cnst.FIRST_BASELINE_CASE]
        for index, value in invalid.items():
            if value == '':
                description = 'Value cannot be blank'
            else:
                description = (
                    f'Value ({value}) must be either \"Existing\",'
                    ' \"Standard Practice\" or \"None\"'
                )

            self.field_data.add(
                column=cnst.FIRST_BASELINE_CASE,
                description=description,
                y=int(index)
            )

    @qa_qc_method
    def validate_second_baseline_case(self) -> None:
        """Validates data fields within the `Second Baseline Case` column.

        Field is flagged if:
            - field is not \'Standard Practice\' or \'None\' (critical)
        """

        df = self.permutations.data
        valid_sbc = ['Standard Practice', 'None']
        invalid = df[
            ~df[cnst.SECOND_BASELINE_CASE].isin(valid_sbc)
        ][cnst.SECOND_BASELINE_CASE]
        for index, value in invalid.items():
            if value == '':
                description = 'Value cannot be blank'
            else:
                description = (
                    f'Value ({value}) must be either \"Standard'
                    ' Practice\" or \"None\"'
                )

            self.field_data.add(
                column=cnst.SECOND_BASELINE_CASE,
                description=description,
                y=int(index)
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
        self.validate_second_baseline_case()
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
        cost_cols = [
            cnst.FIRST_BASELINE_LC,
            cnst.FIRST_BASELINE_MC
        ]
        for col_name in cost_cols:
            invalid = df[
                ~df[cnst.MEASURE_APPLICATION_TYPE].isin(['NR', 'NC'])
                    & ~df[col_name].eq('0')
            ][col_name]
            for index, value in invalid.items():
                self.field_data.add(
                    column=col_name,
                    description=f'Non NC/NR value ({value}) must be 0',
                    y=int(index)
                )

            invalid = df[
                df[cnst.MEASURE_APPLICATION_TYPE].isin(['NC', 'NR'])
                    & ~df[col_name].apply(is_number)
            ][col_name]
            for index, value in invalid.items():
                if value == '':
                    description = 'Value cannot be empty'
                else:
                    description = f'Value ({value}) must be a number'

                self.field_data.add(
                    column=col_name,
                    description=description,
                    y=int(index)
                )

            numeric_df = df[
                df[col_name].apply(is_number)
            ]
            invalid = numeric_df[
                numeric_df[cnst.MEASURE_APPLICATION_TYPE].isin(['NR', 'NC'])
                    & (numeric_df[col_name].astype(float) < 0)
            ][col_name]
            for index, value in invalid.items():
                self.field_data.add(
                    column=col_name,
                    description=f'NC/NR value ({value}) cannot be negative',
                    y=int(index)
                )

    @qa_qc_method
    def validate_first_baseline_mtc(self) -> None:
        """Validates data fields within the `Measure Total Cost 1st Baseline`
        column.

        Field is flagged if:
            - field is not a number (critical)
            - field is less than or equal to 0 (minor)
        """

        df = self.permutations.data

        self.check_columns(
            cnst.FIRST_BASELINE_MTC,
            func=is_number,
            negate=True,
            description='Value must be a number'
        )

        self.check_columns(
            cnst.FIRST_BASELINE_MTC,
            severity=Severity.MINOR,
            func=is_positive,
            negate=True,
            df=df[df[cnst.FIRST_BASELINE_MTC].apply(is_number)],
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
            func=lambda val: not is_number(val) or is_negative(val),
            description='Value must be a non-negative number'
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
            func=lambda val: not is_number(val) or is_negative(val),
            description='Value must be a non-negative number'
        )

        non_zero_vals = df[
            df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')
                & ~df[cnst.SECOND_BASELINE_LC].eq(0)
        ]
        if non_zero_vals.empty:
            self.field_data.add(
                column=cnst.SECOND_BASELINE_LC,
                description='All values are zero',
                severity=Severity.MINOR
            )

        non_zero_vals = df[
            df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')
                & ~df[cnst.SECOND_BASELINE_MC].eq(0)
        ]
        if non_zero_vals.empty:
            self.field_data.add(
                column=cnst.SECOND_BASELINE_MC,
                description='All values are zero',
                severity=Severity.MINOR
            )

        self.check_columns(
            cnst.SECOND_BASELINE_LC,
            cnst.SECOND_BASELINE_MC,
            df=df[~df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')],
            func=is_zero,
            negate=True,
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
            func=is_number,
            negate=True,
            description='Value must be a number'
        )

        self.check_columns(
            cnst.SECOND_BASELINE_MTC,
            severity=Severity.MINOR,
            df=df[
                df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')
                    & df[cnst.SECOND_BASELINE_MTC].apply(is_number)
            ],
            func=is_positive,
            negate=True,
            description='Value must be a positive number'
        )

        self.check_columns(
            cnst.SECOND_BASELINE_MTC,
            df=df[
                ~df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')
                    & df[cnst.SECOND_BASELINE_MTC].apply(is_number)
            ],
            func=is_zero,
            negate=True,
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

        df = self.permutations.data
        valid_eul_ids = db.get_eul_ids()
        invalid = df[
            ~df[cnst.EUL_ID].isin(valid_eul_ids)
        ][cnst.EUL_ID]
        for index, value in invalid.items():
            if value == '':
                description = 'Field cannot be blank'
            else:
                description = f'Invalid EUL ID: {value}'

            self.field_data.add(
                column=cnst.EUL_ID,
                description=description,
                y=int(index)
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
            func=lambda val: not (is_number(val) and is_positive(val)),
            description='Value must be a positive number'
        )

        df = self.permutations.data
        invalid = df[
            ~df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')
                & ~df[cnst.EUL_YEARS].eq(df[cnst.FIRST_BASELINE_LIFE_CYCLE])
        ][cnst.EUL_YEARS]
        for index, value in invalid.items():
            correct_value = df.loc[index, cnst.FIRST_BASELINE_LIFE_CYCLE]
            self.field_data.add(
                column=cnst.EUL_YEARS,
                description=f'Invalid EUL Year: {value} must be {correct_value}',
                y=int(index)
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
        for index, value in invalid.items():
            eul_year = df.loc[index, cnst.EUL_YEARS]
            self.field_data.add(
                column=cnst.RUL_YEARS,
                description=f'Invalid RUL Year: {value} must be less than {eul_year}',
                y=int(index)
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
                val not in deliv_types
            ),
            description='Value is not a valid delivery type'
        )

        df = self.permutations.data

        late_deliv_types = df.loc[
            df.apply(
                lambda row: (
                    occurs_after(
                        deliv_types[row[cnst.DELIV_TYPE]][0]
                            if row[cnst.DELIV_TYPE] in deliv_types
                            else None,
                        row[cnst.START_DATE]
                    )
                ),
                axis=1
            )
        ][cnst.DELIV_TYPE]
        for index in late_deliv_types.index:
            self.field_data.add(
                column=cnst.DELIV_TYPE,
                description='Delivery type cannot start after the measure\'s'
                    ' start date',
                y=int(index)
            )

        early_deliv_types = df.loc[
            df.apply(
                lambda row: (
                    occurs_before(
                        deliv_types[row[cnst.DELIV_TYPE]][1]
                            if row[cnst.DELIV_TYPE] in deliv_types
                            else None,
                        row[cnst.START_DATE]
                    )
                ),
                axis=1
            )
        ][cnst.DELIV_TYPE]
        for index in early_deliv_types.index:
            self.field_data.add(
                column=cnst.DELIV_TYPE,
                description='Delivery type cannot end before the measure\'s'
                    ' start date',
                y=int(index)
            )

    @qa_qc_method
    def validate_ntg_id(self) -> None:
        """Validates data fields within the `Net to Gross Ratio ID` column.

        Field is flagged if:
            - field is not a valid NTG ID (critical)
        """

        exclusion_map = db.get_exclusion_map(
            key_name=cnst.SECTOR,
            mapped_name=cnst.NTG_ID
        )

        valid_ids = []
        for id_set in exclusion_map.values():
            valid_ids.extend(list(id_set))

        df = self.permutations.data
        invalid = df[
            ~df[cnst.NTG_ID].isin(valid_ids)
        ][cnst.NTG_ID]
        for index, value in invalid.items():
            if value == '':
                description = 'Field cannot be blank'
            else:
                description = f'Invalid NTG ID: {value}'

            self.field_data.add(
                column=cnst.GSIA_ID,
                description=description,
                y=int(index)
            )

    @qa_qc_method
    def validate_gsia_id(self) -> None:
        """Validates data fields within the `GSIA ID` column.

        Field is flagged if:
            - field is not a valid GSIA ID (critical)
        """

        exclusion_map = db.get_exclusion_map(
            key_name=cnst.SECTOR,
            mapped_name=cnst.GSIA_ID
        )

        valid_ids = []
        for id_set in exclusion_map.values():
            valid_ids.extend(list(id_set))

        df = self.permutations.data
        invalid = df[
            ~df[cnst.GSIA_ID].isin(valid_ids)
        ][cnst.GSIA_ID]
        for index, value in invalid.items():
            if value == '':
                description = 'Field cannot be blank'
            else:
                description = f'Invalid GSIA ID: {value}'

            self.field_data.add(
                column=cnst.GSIA_ID,
                description=description,
                y=int(index)
            )

    @qa_qc_method
    def validate_ntg_value(self) -> None:
        """Validates data fields within the `NTG Value` column.

        Field is flagged if:
            - field is less than 0 or greater than 1 (critical)
        """

        self.check_columns(
            *cnst.NTG_VALUE_COLS,
            func=lambda val: (
                not is_number(val)
                    or not is_positive(val)
                    or is_greater_than(val, 1)
            ),
            description='Value must be > 0 and <= 1'
        )

    @qa_qc_method
    def validate_gsia_value(self) -> None:
        """Validates data fields within the `GSIA Value` column.

        Field is flagged if:
            - field is less than 0 or greater than 1 (critical)
        """

        self.check_columns(
            cnst.GSIA_VALUE,
            func=lambda val: (
                not is_number(val)
                    or not is_positive(val)
                    or is_greater_than(val, 1)
            ),
            description='Value must be > 0 and <= 1'
        )

    @qa_qc_method
    def validate_restricted_permutation(self) -> None:
        """Validates data fields within the `Restructed Permutation` column.

        Field is flagged if:
            - field is not 0 or 1 (critical)
        """

        self.check_columns(
            cnst.RESTRICTED_PERMUTATION,
            func=lambda val: val != '0' and val != '1',
            description='Value must be either a 0 or 1'
        )

    @qa_qc_method
    def validate_upstream_flag(self) -> None:
        """Validates data fields within the `Upstream Flag (True / False)`
        column.

        Field is flagged if:
            - field is blank when measure is < PY2026
            - field is not blank when measure is >= PY2026
        """

        df = self.permutations.data
        invalid = df[
            df.apply(
                lambda row: (
                    dt.datetime.strptime(
                        row[cnst.START_DATE],
                        r'%Y-%m-%d'
                    ) >= dt.datetime(
                        year=2026,
                        month=1,
                        day=1
                    )
                ),
                axis=1
            ) & (
                ~df[cnst.UPSTREAM_FLAG].eq('')
            )
        ][cnst.UPSTREAM_FLAG]
        for index in invalid.index:
            self.field_data.add(
                column=cnst.UPSTREAM_FLAG,
                description='Value must be blank',
                y=int(index)
            )

        invalid = df[
            df.apply(
                lambda row: (
                    dt.datetime.strptime(
                        row[cnst.START_DATE],
                        r'%Y-%m-%d'
                    ) < dt.datetime(
                        year=2026,
                        month=1,
                        day=1
                    )
                ),
                axis=1
            ) & (
                df[cnst.UPSTREAM_FLAG].eq('')
            )
        ][cnst.UPSTREAM_FLAG]
        for index in invalid.index:
            self.field_data.add(
                column=cnst.UPSTREAM_FLAG,
                description='Value cannot be blank',
                y=int(index)
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
        invalid = df[
            ~df[cnst.VERSION_SOURCE].eq('')
                & ~df[cnst.VERSION_SOURCE].isin(valid_version_sources)
        ][cnst.VERSION_SOURCE]
        for index, value in invalid.items():
            self.field_data.add(
                column=cnst.VERSION_SOURCE,
                description=f'Invalid Version Source: {value}',
                y=int(index)
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
            value=['', 'Indoor', 'Outdoor'],
            negate=True,
            description='Value must be either blank, \"Indoor\" or'
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
            invalid = df[
                ~df[cnst.WATER_MEASURE_TYPE].eq('')
                    & ~df[col_name].apply(is_number)
            ][col_name]
            for index in invalid.index:
                self.field_data.add(
                    column=col_name,
                    description='Value must be a number',
                    y=int(index)
                )

            numeric_df = df[df[col_name].apply(is_number)]
            invalid = numeric_df[
                numeric_df[cnst.WATER_MEASURE_TYPE].eq('')
                    & ~numeric_df[col_name].astype(float).eq(0)
            ][col_name]
            for index in invalid.index:
                self.field_data.add(
                    column=col_name,
                    description='Value must be 0',
                    y=int(index)
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
            invalid = df[
                df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')
                    & ~df[cnst.WATER_MEASURE_TYPE].eq('')
                    & ~df[col_name].apply(is_number)
            ][col_name]
            for index in invalid.index:
                self.field_data.add(
                    column=col_name,
                    description='Value must be a number',
                    y=int(index)
                )

            invalid = df[
                ~df[col_name].eq('0')
                    & (~df[cnst.MEASURE_APPLICATION_TYPE].eq('AR')
                        | df[cnst.WATER_MEASURE_TYPE].eq(''))
            ][col_name]
            for index in invalid.index:
                self.field_data.add(
                    column=col_name,
                    description='Value must be 0',
                    y=int(index)
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
            - Measure Application Type is NC/NR and field is blank
            (critical)
        """

        df = self.permutations.data
        self.check_columns(
            cnst.STD_TECH_ID,
            df=df[df[cnst.MEASURE_APPLICATION_TYPE].isin(['NC', 'NR'])],
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
            invalid = df[~df[col_name].isin(valid_tech_groups)][col_name]
            for index, value in invalid.items():
                if value == '':
                    description = 'Field cannot be blank'
                else:
                    description = (
                        f'Invalid tech group: {value}, must be one of'
                        f' {valid_tech_groups}'
                    )

                self.field_data.add(
                    column=col_name,
                    description=description,
                    y=int(index)
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
            invalid = df[~df[col_name].isin(valid_tech_types)][col_name]
            for index, value in invalid.items():
                if value == '':
                    description = 'Field cannot be blank'
                else:
                    description = (
                        f'Invalid tech type: {value}, must be one of'
                        f' {valid_tech_types}'
                    )

                self.field_data.add(
                    column=col_name,
                    description=description,
                    y=int(index)
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
            - field is not blank and field does not start with \'E\'
            (critical)
        """

        df = self.permutations.data
        etp_cols = df.filter(regex=('ETP Flag.*')).columns.to_list()
        if etp_cols == []:
            raise ParserError('Missing ETP Flag column')

        if len(etp_cols) > 1:
            raise ParserError(f'Ambiguous ETP Flag column: {etp_cols}')

        etp_flag = etp_cols[0]
        invalid = df[
            ~df[etp_flag].eq('')
                & ~df[etp_flag].str.startswith('E')
        ][etp_flag]
        for index, value in invalid.items():
            self.field_data.add(
                column=etp_flag,
                description=f'Invalid ETP Flag: {value} must not be blank and'
                    ' must start with \'E\'',
                y=int(index)
            )

    @qa_qc_method
    def validate_ie_factor(self) -> None:
        """Validates data fields within the `IE Factor` column.

        Field is flagged if:
            - field is not \'Yes\' or \'No\' (critical)
        """

        df = self.permutations.data
        invalid = df[~df[cnst.IE_FACTOR].isin(['Yes', 'No'])][cnst.IE_FACTOR]
        for index, value in invalid.items():
            if value == '':
                description = 'Field cannot be blank'
            else:
                description = (
                    f'Invalid IE Factor value: {value}, must be'
                    ' either \'Yes\' or \'No\''
                )

            self.field_data.add(
                column=cnst.IE_FACTOR,
                description=description,
                y=int(index)
            )

    @qa_qc_method
    def validate_ie_table_name(self) -> None:
        """Validates data fields within the `IE Table Name` column.

        Field is flagged if:
            - IE Factor is \'No\' and field is not \'NA\' (critical)
            - IE Factor is \'Yes\' and field is \'NA\' (critical)
        """

        df = self.permutations.data
        invalid = df[
            df[cnst.IE_FACTOR].eq('No') & ~df[cnst.IE_TABLE_NAME].eq('NA')
        ][cnst.IE_TABLE_NAME]
        for index, value in invalid.items():
            self.field_data.add(
                column=cnst.IE_TABLE_NAME,
                description=f'Invalid IE Table Name: {value} must be \'NA\'',
                y=int(index)
            )

        invalid = df[
            df[cnst.IE_FACTOR].eq('Yes')
                & df[cnst.IE_TABLE_NAME].eq('NA')
        ][cnst.IE_TABLE_NAME]
        for index, value in invalid.items():
            self.field_data.add(
                column=cnst.IE_TABLE_NAME,
                description=f'Invalid IE Table Name: {value} must be a table name',
                y=int(index)
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
        invalid = df[
            df[cnst.MEAS_IMPACT_TYPE].eq('Deem-DEER')
                & df[cnst.DEER_MEAS_ID].eq('')
        ][cnst.DEER_MEAS_ID]
        for index in invalid.index:
            self.field_data.add(
                column=cnst.DEER_MEAS_ID,
                description='Measure Impact Type is \"Deem-DEER\", so this'
                    ' value cannot be blank',
                y=int(index)
            )

        invalid = df[
            ~df[cnst.MEAS_IMPACT_TYPE].eq('Deem-DEER')
                & ~df[cnst.DEER_MEAS_ID].eq('')
        ][cnst.DEER_MEAS_ID]
        for index in invalid.index:
            self.field_data.add(
                column=cnst.DEER_MEAS_ID,
                description='Measure Impact Type is not \"Deem-DEER\", so this'
                    ' value must be blank',
                y=int(index)
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

        meas_impact_types = db.get_measure_impact_types()
        invalid = df[
            ~df[cnst.MEAS_IMPACT_TYPE].isin(meas_impact_types)
        ][cnst.MEAS_IMPACT_TYPE]
        for index, value in invalid.items():
            self.field_data.add(
                column=cnst.MEAS_IMPACT_TYPE,
                description=f'Invalid Measure Impact ID: {value}',
                y=int(index)
            )

        invalid = df[
            df.apply(
                lambda row: (
                    occurs_after(
                        meas_impact_types[row[cnst.MEAS_IMPACT_TYPE]][0]
                            if row[cnst.MEAS_IMPACT_TYPE] in meas_impact_types
                            else None,
                        row[cnst.START_DATE]
                    )
                ),
                axis=1
            )
        ][cnst.MEAS_IMPACT_TYPE]
        for index, value in invalid.items():
            self.field_data.add(
                column=cnst.MEAS_IMPACT_TYPE,
                description=f'Invalid Measure Impact ID: {value} starts'
                    ' after the measure\'s start date.',
                y=int(index)
            )

        invalid = df[
            df.apply(
                lambda row: (
                    occurs_before(
                        meas_impact_types[row[cnst.MEAS_IMPACT_TYPE]][1]
                            if row[cnst.MEAS_IMPACT_TYPE] in meas_impact_types
                            else None,
                        row[cnst.START_DATE]
                    )
                ),
                axis=1
            )
        ][cnst.MEAS_IMPACT_TYPE]
        for index, value in invalid.items():
            self.field_data.add(
                column=cnst.MEAS_IMPACT_TYPE,
                description=f'Invalid Measure Impact ID: {value} ends'
                    ' before the measure\'s start date.',
                y=int(index)
            )

    @qa_qc_method
    def validate_measure_detail_id(self) -> None:
        """Validates data fields within the `Measure Detail ID` column.

        Field is flagged if:
            - field contains a duplicate (critical)
        """

        df = self.permutations.data
        duplicates = [
            col
                for _, col 
                in df.groupby(cnst.MEAS_DETAIL_ID)
                if len(col) > 1
        ]
        if len(duplicates) > 0:
            dupe_df = pd.concat(duplicates)[cnst.MEAS_DETAIL_ID]
            for index, value in dupe_df.items():
                self.field_data.add(
                    column=cnst.MEAS_DETAIL_ID,
                    description=f'Duplicate value: {value}',
                    y=int(index)
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
                    self.field_data.add(
                        column=permutation,
                        description='Failed exclusion check',
                        severity=Severity.MINOR,
                        y=int(index)
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
