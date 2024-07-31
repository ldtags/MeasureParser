from typing import Literal

from src.app.models.home import HomeModel
from src.etrm import sanitizers


class Model:
    """Top level model of the MVC pattern.
    
    Controls all models of the application.
    """

    def __init__(self):
        self.home = HomeModel()
        self.api_key: str | None = None
        self.measure_id: str | None = None
        self.measure_source: Literal['etrm', 'json'] | None = None
        self.measure_file_path: str | None = None
        self.output_file_path: str | None = None

    def set_api_key(self, api_key: str) -> None:
        sanitized_key = sanitizers.sanitize_api_key(api_key)
        self.api_key = sanitized_key

    def set_measure(self, measure_id: str) -> None:
        sanitized_id = sanitizers.sanitize_measure_id(measure_id)
        self.measure_id = sanitized_id
