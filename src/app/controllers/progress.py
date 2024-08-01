from __future__ import annotations
import os
import json
from typing import Callable, TypeVar

from src.app.views import View, HomePage, ResultsPage
from src.app.models import Model
from src.etrm.models import Measure
from src.etrm.connection import ETRMConnection
from src.parser import MeasureParser


_T = TypeVar('_T')
_DEC_TYPE = Callable[..., _T]


def parser_function(log: str | None=None) -> Callable[[_DEC_TYPE], _DEC_TYPE]:
    def decorator(func: _DEC_TYPE) -> _DEC_TYPE:
        def wrapper(self: ProgressController, *args, **kwargs):
            self.view.log_frame.add(log)
            value = func(self, *args, **kwargs)
            progress = self.view.controls_frame.progress_var.get()
            self.view.controls_frame.progress_var.set(progress + 100)
            return value
        return wrapper
    return decorator


class ProgressController:
    def __init__(self, model: Model, view: View):
        self.root = view.root
        self.root_view = view
        self.view = view.progress
        self.model = model
        self.__bind_controls()

    def get_etrm_measure(self) -> Measure:
        @parser_function(f'Retrieving measure {self.model.measure_id}')
        def get_measure(*args) -> Measure:
            connection = ETRMConnection(self.model.api_key)
            measure = connection.get_measure(self.model.measure_id)
            return measure

        measure = get_measure(self)
        return measure

    def get_json_measure(self) -> Measure:
        _, file_name = os.path.split(self.model.measure_file_path)
        @parser_function(f'Retrieving measure from {file_name}')
        def get_measure(*args) -> Measure:
            with open(self.model.measure_file_path, 'r') as fp:
                measure_json = json.load(fp)
            measure = Measure(measure_json, source='json')
            return measure

        measure = get_measure(self)
        return measure

    @parser_function('Validating parameters')
    def parse_parameters(self, parser: MeasureParser) -> None:
        parser.validate_parameters()

    @parser_function('Validating value tables')
    def parse_value_tables(self, parser: MeasureParser) -> None:
        parser.validate_tables()

    @parser_function('Validating exclusion tables')
    def parse_exclusion_tables(self, parser: MeasureParser) -> None:
        parser.validate_exclusion_tables()

    @parser_function('Validating permutations')
    def parse_permutations(self, parser: MeasureParser) -> None:
        parser.validate_permutations()

    @parser_function('Validating characterizations')
    def parse_characterizations(self, parser: MeasureParser) -> None:
        for characterization in parser.measure.characterizations:
            self.view.log_frame.add(f'Parsing {characterization.name}')
            parser.parse_characterization(characterization)

    @parser_function('Logging output')
    def log_output(self, parser: MeasureParser) -> None:
        parser.log_output(
            self.model.output_file_path,
            self.model.home.override_file
        )

    def parse(self) -> None:
        self.view.controls_frame.cont_btn.set_state('disabled')
        self.view.controls_frame.back_btn.set_state('disabled')
        self.view.controls_frame.progress_bar.config(maximum=701)

        if self.model.measure_source == 'etrm':
            measure = self.get_etrm_measure()
        elif self.model.measure_source == 'json':
            measure = self.get_json_measure()
        else:
            raise RuntimeError('Input validation failed')

        parser = MeasureParser(measure)
        self.parse_parameters(parser)
        self.parse_value_tables(parser)
        self.parse_exclusion_tables(parser)
        self.parse_permutations(parser)
        self.parse_characterizations(parser)
        self.log_output(parser)

        self.view.controls_frame.progress_bar.config(maximum=0)
        self.view.controls_frame.cont_btn.set_state('normal')
        self.view.controls_frame.back_btn.set_state('normal')

    def handle_back(self) -> None:
        self.root_view.show(HomePage.key)

    def handle_continue(self) -> None:
        self.root_view.show(ResultsPage.key)

    def __bind_controls(self) -> None:
        self.view.controls_frame.back_btn.set_command(self.handle_back)
        self.view.controls_frame.cont_btn.set_command(self.handle_continue)
