import tkinter as tk
from typing import Literal

from src.app.views import View, ResultsView
from src.app.models import Model, ResultsModel
from src.app.controllers.base_controller import BaseController
from src.parser import ParserData
from src.permqaqc import FieldData


_BaseResultsController = BaseController[ResultsModel, ResultsView]


class ResultsController(_BaseResultsController):
    def __init__(self, model: Model, view: View):
        super().__init__(model, view)
        self._bind_controls()

    def _bind_controls(self) -> None:
        controls = self.view.controls_frame
        controls.close_btn.set_command(self.root_view.close)

    def _load_parser_data(self, data: ParserData) -> None:
        ...

    def _load_permqc_data(self, data: FieldData) -> None:
        ...

    def load_data(self, state: Literal["parser", "permqc"]) -> None:
        match state:
            case "parser":
                parser_data = self.root_model.progress.parser_data
                if parser_data is None:
                    raise tk.TclError("Missing required parser data")

                self._load_parser_data(parser_data)
            case "permqc":
                permqc_data = self.root_model.progress.permqc_data
                if permqc_data is None:
                    raise tk.TclError("Missing required permutation QA/QC data")

                self._load_permqc_data(permqc_data)
            case other:
                raise tk.TclError(F"Unknown state: {other}")
