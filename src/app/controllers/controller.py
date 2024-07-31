from src.app.models import Model
from src.app.views import View
from src.app.views.home import HomePage
from src.app.views.progress import ProgressPage
from src.app.controllers.home import HomeController
from src.app.controllers.progress import ProgressController
from src.etrm import sanitizers


class Controller:
    def __init__(self):
        self.model = Model()
        self.view = View()
        self.home = HomeController(self.model,
                                   self.view,
                                   self.start_process)
        self.progress = ProgressController(self.model, self.view)

    def start(self,
              api_key: str | None=None,
              measure_id: str | None=None
             ) -> None:
        if api_key is not None:
            sanitized_key = sanitizers.sanitize_api_key(api_key)
            self.model.set_api_key(sanitized_key)
            self.view.set_api_key(sanitized_key)

        if measure_id is not None:
            sanitized_id = sanitizers.sanitize_measure_id(measure_id)
            self.model.set_measure(sanitized_id)
            self.view.set_measure(sanitized_id)

        self.view.show(HomePage.key)
        self.view.start()

    def start_process(self) -> None:
        self.view.show(ProgressPage.key)
        self.view.progress.update()
        self.progress.parse()
