import tkinter as tk
from typing import Literal

from src.app.views import View, ResultsView
from src.app.models import Model, ResultsModel
from src.app.controllers.base_controller import BaseController
from src.parser import ParserData


_BaseResultsController = BaseController[ResultsModel, ResultsView]


class ResultsController(_BaseResultsController):
    def __init__(self, model: Model, view: View):
        super().__init__(model, view)
        self._bind_controls()

    def _bind_controls(self) -> None:
        controls = self.view.controls_frame
        controls.close_btn.set_command(self.root_view.close)

    def _load_parser_data(self, data: ParserData) -> None:
        data = self.root_model.progress.parser_data
        if data is None:
            raise tk.TclError("Missing required parser data")

        self.view.show_frame("parser")

    def _load_permqc_data(self) -> None:
        data = self.root_model.progress.permqc_data
        if data is None:
            raise tk.TclError("Missing required permutation QA/QC data")

        permutations = self.root_model.progress.permqc_permutations
        if permutations is None:
            raise tk.TclError("Missing required permutation QA/QC permutations")

        self.view.permqc_frame.load_data(permutations.data, data)
        self.view.show_frame("permqc")

    def load_data(self, state: Literal["parser", "permqc"]) -> None:
        """Handles execution handoff to the specified data loading process.

        This function determines which results frame is shows on the results page.
        """

        match state:
            case "parser":
                self._load_parser_data()
            case "permqc":
                self._load_permqc_data()
            case other:
                raise tk.TclError(f"Unknown state: {other}")
