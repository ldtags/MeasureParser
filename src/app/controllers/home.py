from src.app.views import View
from src.app.models import Model


class HomeController:
    def __init__(self, model: Model, view: View):
        self.root_model = model
        self.model = model.home
        self.root_view = view
        self.view = view.home
        self.__bind()

    def close(self):
        self.root_view.root.destroy()

    def __bind(self):
        self.view.controls_frame.close_btn.set_command(self.close)
        