from src.app.types import HomeViewState, MeasureSourceState
from src.config import app_config


class HomeModel:
    def __init__(self):
        api_key = app_config.api_key

        self.override_file = app_config.override_file
        self._remember_me = api_key is not None
        self.view_state: HomeViewState = None
        self.source_states: dict[HomeViewState, MeasureSourceState] = {}
        self.measure_id: str | None = None
        self._api_key = api_key
        self.measure_file_path: str | None = None
        self.permutations_file_path: str | None = None
        self.output_file_path: str | None = None

    @property
    def remember_me(self) -> bool:
        return self._remember_me

    @remember_me.setter
    def remember_me(self, value: bool) -> None:
        if value == False:
            app_config.api_key = None

        self._remember_me = value

    @property
    def api_key(self) -> str | None:
        return self._api_key

    @api_key.setter
    def api_key(self, value: str | None) -> None:
        app_config.api_key = value
        self._api_key = value
