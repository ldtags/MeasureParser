from src.app.views import View
from src.app.models import Model
from src.app.controllers.base import BaseController
from src.etrm.models import Measure
from src.parser import MeasureParser


class ProgressController(BaseController):
    def __init__(self, model: Model, view: View):
        BaseController.__init__(self, model, view)

    def parse(self, measure: Measure, out_file: str) -> None:
        parser = MeasureParser()
        parser.parse(measure)
        parser.log_output(out_file)
