from typing import Type

from src.app import views
from src.app.models import Model
from src.app.views import View, HomeView, GenericView
from src.app.controllers.home import HomeController
from src.app.controllers.progress import ProgressController
from src.app.controllers.results import ResultsController


class Controller:
    def __init__(self) -> None:
        self.model = Model()
        self.view = View()
        self.home = HomeController(self.model, self.view, self.start_process)
        self.progress = ProgressController(self.model, self.view)
        self.results = ResultsController(self.model, self.view)

    def start(self, api_key: str | None=None, measure_id: str | None=None) -> None:
        if api_key is not None:
            self.model.home.api_key = api_key

        if measure_id is not None:
            self.model.home.measure_id = measure_id

        self.show(HomeView)
        self.view.start()

    def show(self, view: Type[GenericView]) -> None:
        match view:
            case views.HomeView:
                self.home._update_view()

        self.view.show(view)

    def start_process(self) -> None:
        self.view.progress.show()
        self.view.progress.update()
        self.progress.run_process(self.view.home.state)
