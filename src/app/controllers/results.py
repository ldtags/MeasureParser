from src.app.views import View
from src.app.models import Model


class ResultsController:
    def __init__(self, model: Model, view: View):
        self.model = model
        self.root_view = view
        self.view = view.results
        self.__bind_controls()

    def __bind_controls(self) -> None:
        controls = self.view.controls_frame
        controls.close_btn.config(command=self.root_view.close)
