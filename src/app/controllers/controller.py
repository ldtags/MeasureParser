from src.app.models import Model
from src.app.views import View
from src.app.views.home import HomePage
from src.app.controllers.home import HomeController
from src.app.controllers.progress import ProgressController


class Controller:
    def __init__(self):
        self.model = Model()
        self.view = View()
        self.home = HomeController(self.model,
                                   self.view,
                                   self.start_process)
        self.progress = ProgressController(self.model, self.view)

    def start(self) -> None:
        self.view.show(HomePage.key)
        self.view.start()

    def start_process(self) -> None:
        measure = self.model.home.measure
        if measure is None:
            return

        out_file = self.model.home.output_path
        if out_file is None:
            return

        self.progress.parse(measure, out_file)
