from src.app.models import Model
from src.app.views import View
from src.app.controllers.home import HomeController
from src.app.controllers.progress import ProgressController
from src.app.controllers.results import ResultsController
from src.config import app_config


class Controller:
    def __init__(self):
        self.model = Model()
        self.view = View()
        self.home = HomeController(self.model, self.view, self.start_process)
        self.progress = ProgressController(self.model, self.view)
        self.results = ResultsController(self.model, self.view)

    def start(self) -> None:
        self.view.home.show()
        self.view.start()

    def start_process(self) -> None:
        self.view.progress.show()
        self.view.progress.update()
        self.progress.run_process(self.view.home.state)
