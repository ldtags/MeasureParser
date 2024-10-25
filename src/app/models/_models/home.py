from src.app.types import HomeViewState, MeasureSourceState
from src.app.exceptions import ValidationError
from src.config import app_config


class HomeModel:
    def __init__(self):
        self.override_file = app_config.override_file
        self.validate_permutations = False
        self.qa_qc_permutations = False
        self.view_state: HomeViewState = None
        self.source_states: dict[HomeViewState, MeasureSourceState] = {}
        self.measure_id: str | None = None
        self.api_key: str | None = None
        self.measure_file_path: str | None = None
        self.permutations_file_path: str | None = None
        self.output_file_path: str | None = None
