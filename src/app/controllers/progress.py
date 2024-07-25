import json

from src.app.views import View
from src.app.models import Model
from src.etrm.models import Measure
from src.etrm.connection import ETRMConnection
from src.parser import MeasureParser


class ProgressController:
    def __init__(self, model: Model, view: View):
        self.root = view.root
        self.root_view = view
        self.view = view.progress
        self.model = model

    def get_measure(self) -> Measure:
        measure_file_path = self.model.measure_file_path
        if measure_file_path is not None:
            with open(self.model.measure_file_path, 'r') as fp:
                measure_json = json.load(fp)
            measure = Measure(measure_json)
            return measure

        api_key = self.model.api_key
        measure_id = self.model.measure_id
        if api_key is not None and measure_id is not None:
            connection = ETRMConnection(api_key)
            measure = connection.get_measure(measure_id)
            return measure

        raise RuntimeError('Measure source validation failed')

    def parse(self) -> None:
        measure = self.get_measure()
        parser = MeasureParser(measure)
        frame = self.view.log_frame

        frame.add('Validating parameters...')
        parser.validate_parameters()

        frame.add('Validating exclusion tables...')
        parser.validate_exclusion_tables()

        frame.add('Validating value tables...')
        parser.validate_tables()

        frame.add('Validating permutations...')
        parser.validate_permutations()

        frame.add('Validating characterizations...')
        parser.parse_characterizations()
