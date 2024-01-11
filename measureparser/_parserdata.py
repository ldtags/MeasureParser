'''Classes that store data from parsing eTRM measure JSON files'''

from dataclasses import dataclass, field


@dataclass
class GeneralValidationData:
    unexpected: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    unordered: list[str] = field(default_factory=list)


@dataclass
class SpacingData:
    leading: int = -1
    trailing: int = -1

    def is_empty(self) -> bool:
        return self.leading == -1 and self.trailing == -1


@dataclass
class SentenceSpacingData(SpacingData):
    sentence: str
    initial: bool = False


@dataclass
class TitleData:
    missing: bool = False
    spacing: SpacingData

    def is_empty(self) -> bool:
        return self.missing == False and self.spacing.is_empty()


@dataclass
class ReferenceTagData:
    spacing: SpacingData
    title: TitleData

    def is_empty(self) -> bool:
        return self.spacing.is_empty() and self.title.is_empty()


@dataclass
class ReferenceData:
    reference_map: dict[str, list[ReferenceTagData]] \
        = field(default_factory=dict)

    def get(self, title: str | None) -> list[ReferenceTagData]:
        if title == None:
            title == 'undefined'

        if self.reference_map.get(title) != None:
            return self.reference_map[title]

        self.reference_map[title] = []
        return self.reference_map[title]

    def is_empty(self) -> bool:
        return not self.reference_map


@dataclass
class InvalidHeaderData:
    tag: str
    prev_level: int


@dataclass
class CharacterizationData:
    missing: bool = False
    initial_header: str = 'h3'
    invalid_headers: list[InvalidHeaderData] = field(default_factory=list)
    references: ReferenceData
    sentences: list[SentenceSpacingData] = field(default_factory=list)

    def is_empty(self) -> bool:
        return (self.missing == False
            and self.initial_header == 'h3'
            and self.invalid_headers == []
            and self.references.is_empty()
            and self.sentences == [])


def characterization_dict() -> dict[str, CharacterizationData]:
    from measureparser._dbservice import get_all_characterization_names
    char_dict: [str, CharacterizationData] = {}
    for name in get_all_characterization_names():
        char_dict[name] = CharacterizationData()
    return char_dict


@dataclass
class InvalidPermutationData:
    reporting_name: str
    mapped_name: str
    valid_names: list[str] = field(default_factory=list)


@dataclass
class PermutationData:
    invalid: list[InvalidPermutationData] = field(default_factory=list)
    unexpected: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
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

    def is_empty(self) -> bool:
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

    def is_empty(self) -> bool:
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
    characterization: dict[str, CharacterizationData] \
        = field(default_factory=characterization_dict)