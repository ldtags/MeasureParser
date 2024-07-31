from typing import Literal

from src.app.models.home import HomeModel
from src.etrm import sanitizers
from src.parserdata import ParserData


class Model:
    """Top level model of the MVC pattern.
    
    Controls all models of the application.
    """

    def __init__(self):
        self.home = HomeModel()
        self.__api_key: str | None = None
        self.__measure_id: str | None = None
        self.measure_source: Literal['etrm', 'json'] | None = None
        self.measure_file_path: str | None = None
        self.output_file_path: str | None = None
        self.parser_data: ParserData | None = None

    @property
    def api_key(self) -> str | None:
        return self.__api_key

    @api_key.setter
    def api_key(self, api_key: str) -> None:
        sanitized_key = sanitizers.sanitize_api_key(api_key)
        self.__api_key = sanitized_key

    @property
    def measure_id(self) -> str | None:
        return self.__measure_id

    @measure_id.setter
    def measure_id(self, measure_id: str) -> None:
        sanitized_id = sanitizers.sanitize_measure_id(measure_id)
        self.__measure_id = sanitized_id

    def set_api_key(self, api_key: str) -> None:
        self.api_key = api_key

    def set_measure(self, measure_id: str) -> None:
        self.measure_id = measure_id
