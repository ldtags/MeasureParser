from src.app.models import Model
from src.app.views import View, HOME
from src.app.controllers.home import HomeController


class Controller:
    def __init__(self):
        self.model = Model()
        self.view = View()
        self.home = HomeController(self.model, self.view)

    def start(self):
        self.view.show(HOME)
        self.view.start()
