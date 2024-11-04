from src.app.types import HomeViewState
from src.parser import ParserData
from src.permqaqc import FieldData


class ResultsModel:
    def __init__(self):
        self._view: HomeViewState | None = None
        self._parser_data: ParserData | None = None
        self._permqc_data: FieldData | None = None

    @property
    def view(self) -> HomeViewState | None:
        """Read-only view property."""

        return self._view

    @property
    def parser_data(self) -> ParserData | None:
        return self._parser_data

    @parser_data.setter
    def parser_data(self, data: ParserData | None) -> None:
        if data is None:
            if self._view == "parser":
                self._view = None

            self._parser_data = None
        else:
            self._view = "parser"
            self._parser_data = data
            self._permqc_data = None

    @property
    def permqc_data(self) -> FieldData | None:
        return self._permqc_data

    @permqc_data.setter
    def permqc_data(self, data: FieldData | None) -> None:
        if data is None:
            if self._view == "permqc":
                self._view = None

            self._permqc_data = None
        else:
            self._view = "permqc"
            self._permqc_data = data
            self._parser_data = None
