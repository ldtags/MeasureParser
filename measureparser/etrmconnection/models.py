from datetime import datetime

from .._dbservice import (
    get_all_characterization_names
)


class Characterization:
    def __init__(self, name: str, content: str):
        self.name = name
        self.content = content


def _characterization_factory(measure_dict: dict) -> dict[str, Characterization]:
    char_dict: dict[str, Characterization] = {}
    for char_name in get_all_characterization_names():
        content: str | None = measure_dict.get(char_name)
        if content == None:
            m_name: str = measure_dict.get('MeasureName')
            print(f'Characterization {char_name} is missing a mapping in measure {m_name}')
        char_dict[char_name] = Characterization(char_name, content)
    return char_dict


class Measure:
    def __init__(self, measure_dict: dict):
        self.primary_key: int = measure_dict.get('pk')
        self.id: str = measure_dict.get('MeasureID')
        self.version_id: str = measure_dict.get('MeasureVersionID')
        self.name: str = measure_dict.get('MeasureName')
        self.use_category: str = measure_dict.get('UseCategory')
        self.source_desc: str = measure_dict.get('SourceDesc')
        self.pa_lead: str = measure_dict.get('PALead')
        self.start_date: str = measure_dict.get('StartDate')
        self.end_date: str | None = measure_dict.get('EndDate')
        self.status: str = measure_dict.get('Status')
        self.cover_sheet_file: str = measure_dict.get('MeasurePackageCoverSheetFile')
        self.characterizations: dict[str, Characterization] = _characterization_factory(measure_dict)
        self.updated_at: datetime = measure_dict.get('updated_at')
