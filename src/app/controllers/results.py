from src.app.views import View
from src.app.models import Model


class ResultsController:
    def __init__(self, model: Model, view: View):
        self.model = model
        self.root_view = view
        self.view = view.results
