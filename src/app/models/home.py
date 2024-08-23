from src import etrm
from src.config import app_config


class HomeModel:
    def __init__(self):
        self.__api_key: str | None = None
        self.__measure_id: str | None = None
        self.json_path: str | None = None
        self.csv_path: str | None = None
        self.override_file = app_config.override_file
        self.validate_permutations = False
        self.qa_qc_permutations = False

    @property
    def api_key(self) -> str | None:
        return self.__api_key

    @api_key.setter
    def api_key(self, api_key: str | None) -> None:
        if api_key is None:
            self.__api_key = None
            return

        self.__api_key = etrm.sanitize_api_key(api_key)

    @property
    def measure_id(self) -> str | None:
        return self.__measure_id

    @measure_id.setter
    def measure_id(self, measure_id: str | None) -> None:
        if measure_id is None:
            self.__measure_id = measure_id
            return

        self.__measure_id = etrm.sanitize_measure_id(measure_id)
