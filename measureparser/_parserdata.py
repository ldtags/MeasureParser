'''Classes that store data from parsing eTRM measure JSON files'''

from dataclasses import dataclass


@dataclass
class GeneralValidationData():
    unexpected: list[str] = []
    missing: list[str] = []
    unordered: list[str] = []

@dataclass
class GeneralHeaderData():
    name: str
    tag: str

@dataclass
class IncorrectHeaderData(GeneralHeaderData):
    prev_level: int

@dataclass
class UncapitalizedNounData():
    name: str
    word: str

@dataclass
class ExtraSpaceData():
    name: str
    spaces: int

@dataclass
class CharacterizationData():
    punc_space: list[ExtraSpaceData] = []
    refr_space: list[ExtraSpaceData] = []
    capitalization: list[UncapitalizedNounData] = []
    inv_header: list[GeneralHeaderData] = []
    init_header: list[GeneralHeaderData] = []
    inc_header: list[IncorrectHeaderData] = []

@dataclass
class InvalidPermutationData():
    reporting_name: str
    mapped_name: str
    valid_names: list[str] = []

@dataclass
class PermutationData():
    invalid: list[InvalidPermutationData] = []
    unexpected: list[str] = []

@dataclass
class MissingValueTableColumnData():
    table_name: str
    column_name: str

@dataclass
class InvalidValueTableColumnUnitData():
    table_name: str
    column_name: str
    mapped_unit: str
    correct_unit: str

@dataclass
class ValueTableColumnData():
    missing: list[MissingValueTableColumnData] = []
    invalid_unit: list[InvalidValueTableColumnUnitData] = []

@dataclass
class NonSharedValueTableData(GeneralValidationData):
    column: ValueTableColumnData = ValueTableColumnData()

@dataclass
class SharedValueTableData(GeneralValidationData):
    pass

@dataclass
class ValueTableData():
    shared: SharedValueTableData = SharedValueTableData()
    nonshared: NonSharedValueTableData = NonSharedValueTableData()

@dataclass
class ExclusionTableData():
    whitespace: list[str] = []
    hyphen: list[str] = []

@dataclass
class ParameterData(GeneralValidationData):
    nonshared: list[str] = []

@dataclass
class ParserData():
    parameter: ParameterData = ParameterData()
    exclusion_table: ExclusionTableData = ExclusionTableData()
    value_table: ValueTableData = ValueTableData()
    permutation: PermutationData = PermutationData()
    characterization: CharacterizationData = CharacterizationData()