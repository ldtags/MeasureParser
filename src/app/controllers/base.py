from src.app.views import View
from src.app.models import Model


class BaseController:
    def __init__(self, model: Model, view: View):
        self.root = view.root
        self.root_view = view
        self.root_model = model
