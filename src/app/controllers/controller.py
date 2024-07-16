from src.app.models import Model
from src.app.views import View
from src.app.views.home import HomePage
from src.app.controllers.home import HomeController


class Controller:
    def __init__(self):
        self.model = Model()
        self.view = View()
        self.home = HomeController(self.model, self.view)

    def start(self):
        self.view.show(HomePage.key)
        self.view.start()
