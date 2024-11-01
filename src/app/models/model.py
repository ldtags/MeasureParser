from typing import Type

from src.app.enums import MeasureSource
from src.app.models._models import HomeModel, ResultsModel, ProgressModel, GenericModel
from src.etrm import sanitizers
from src.parser.parserdata import ParserData


class Model:
    """Top level model of the MVC pattern.
    
    Controls all models of the application.
    """

    def __init__(self):
        self.home = HomeModel()
        self.progress = ProgressModel()
        self.results = ResultsModel()
        self.models: dict[Type[GenericModel], GenericModel] = {
            HomeModel: self.home,
            ProgressModel: self.progress,
            ResultsModel: self.results
        }

        self.__api_key: str | None = None
        self.__measure_id: str | None = None
        self.measure_source: MeasureSource | None = None
        self.measure_file_path: str | None = None
        self.output_file_path: str | None = None
        self.parser_data: ParserData | None = None

    def __getitem__(self, model: Type[GenericModel]) -> GenericModel:
        return self.models[model]

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
