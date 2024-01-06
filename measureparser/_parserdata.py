'''Classes that store data from parsing eTRM measure JSON files'''

from dataclasses import dataclass, field


@dataclass
class GeneralValidationData:
    unexpected: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    unordered: list[str] = field(default_factory=list)

@dataclass
class GeneralHeaderData:
    name: str
    tag: str

@dataclass
class IncorrectHeaderData(GeneralHeaderData):
    prev_level: int

@dataclass
class UncapitalizedNounData:
    name: str
    word: str
    capitalized: str

@dataclass
class ExtraSpaceData:
    name: str
    spaces: int

@dataclass
class CharacterizationData:
    missing: list[str] = field(default_factory=list)
    punc_space: list[ExtraSpaceData] = field(default_factory=list)
    refr_space: list[ExtraSpaceData] = field(default_factory=list)
    capitalization: list[UncapitalizedNounData] \
        = field(default_factory=list)
    inv_header: list[GeneralHeaderData] = field(default_factory=list)
    init_header: list[GeneralHeaderData] = field(default_factory=list)
    inc_header: list[IncorrectHeaderData] = field(default_factory=list)

    def isEmpty(self) -> bool:
        return (self.missing == []
            and self.punc_space == []
            and self.refr_space == []
            and self.capitalization == []
            and self.inv_header == []
            and self.init_header == []
            and self.inc_header == [])

@dataclass
class InvalidPermutationData:
    reporting_name: str
    mapped_name: str
    valid_names: list[str] = field(default_factory=list)

@dataclass
class PermutationData:
    invalid: list[InvalidPermutationData] = field(default_factory=list)
    unexpected: list[str] = field(default_factory=list)

    def isEmpty(self) -> bool:
        return self.invalid == [] and self.unexpected == []

@dataclass
class MissingValueTableColumnData:
    table_name: str
    column_name: str

@dataclass
class InvalidValueTableColumnUnitData:
    table_name: str
    column_name: str
    mapped_unit: str
    correct_unit: str

@dataclass
class ValueTableColumnData:
    missing: list[MissingValueTableColumnData] = field(default_factory=list)
    invalid_unit: list[InvalidValueTableColumnUnitData] \
        = field(default_factory=list)

    def isEmpty(self) -> bool:
        return self.missing == [] and self.invalid_unit == []

@dataclass
class StdValueTableNameData:
    table_name: str
    correct_name: str

@dataclass
class NonSharedValueTableData(GeneralValidationData):
    invalid_name: list[StdValueTableNameData] = field(default_factory=list)
    column: ValueTableColumnData = field(default_factory=ValueTableColumnData)

@dataclass
class SharedValueTableData(GeneralValidationData):
    pass

@dataclass
class ValueTableData:
    shared: SharedValueTableData = field(default_factory=SharedValueTableData)
    nonshared: NonSharedValueTableData \
        = field(default_factory=NonSharedValueTableData)

@dataclass
class ExclusionTableData:
    whitespace: list[str] = field(default_factory=list)
    hyphen: list[str] = field(default_factory=list)

    def isEmpty(self) -> bool:
        return self.whitespace == [] and self.hyphen == []

@dataclass
class ParameterData(GeneralValidationData):
    nonshared: list[str] = field(default_factory=list)

@dataclass
class ParserData:
    parameter: ParameterData = field(default_factory=ParameterData)
    exclusion_table: ExclusionTableData \
        = field(default_factory=ExclusionTableData)
    value_table: ValueTableData = field(default_factory=ValueTableData)
    permutation: PermutationData = field(default_factory=PermutationData)
    characterization: CharacterizationData \
        = field(default_factory=CharacterizationData)