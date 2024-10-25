from __future__ import annotations
import os
import json
import time
from typing import Callable, TypeVar, Literal

from src.app.enums import MeasureSource
from src.app.views import View
from src.app.models import Model
from src.etrm.models import Measure
from src.etrm.connection import ETRMConnection
from src.parser import MeasureParser
from src.parser.logger import MeasureDataLogger
from src.parser.parserdata import ParserData
from src.permqaqc import PermutationQAQC


_T = TypeVar('_T')
_DEC_TYPE = Callable[..., _T]
_DEC_WRAPPER_TYPE = Callable[[_DEC_TYPE], _DEC_TYPE]


def make_progress_decorator() -> Callable[[str | None], _DEC_TYPE]:
    registry: dict[str, _DEC_TYPE] = {}
    def arg_wrapper(log: str | None=None) -> _DEC_WRAPPER_TYPE:
        def decorator(func: _DEC_TYPE) -> _DEC_TYPE:
            registry[func.__name__] = func
            def wrapper(self: ProgressController, *args, **kwargs) -> _T:
                self.view.log_frame.add(log)
                value = func(self, *args, **kwargs)
                progress = self.view.controls_frame.progress_var.get()
                self.view.controls_frame.progress_var.set(progress + 100)
                return value
            return wrapper
        return decorator
    arg_wrapper.all = registry
    return arg_wrapper


parser_function = make_progress_decorator()
permqc_function = make_progress_decorator()


class ProgressController:
    def __init__(self, model: Model, view: View):
        self.root = view.root
        self.root_view = view
        self.view = view.progress
        self.model = model
        self.parser = ParserController(self.model, self.root_view)
        self.permqc = PermQcController(self.model, self.root_view)
        self.__bind_controls()

    def handle_back(self) -> None:
        self.root_view.home.show()

    def handle_continue(self) -> None:
        # self.root_view.results.show()
        self.root_view.close()

    def run_process(self, process: Literal['parser', 'permqc']) -> None:
        _proc = None
        match process:
            case "parser":
                _proc = self.parser.parse
            case "permqc":
                _proc = self.permqc.qa_qc_permutations
            case other:
                raise RuntimeError(f"Unknown process: {other}")

        self.view.controls_frame.cont_btn.set_state('disabled')
        self.view.controls_frame.back_btn.set_state('disabled')
        _proc()
        self.view.controls_frame.back_btn.set_state('normal')
        self.view.controls_frame.cont_btn.set_state('normal')

    def __bind_controls(self) -> None:
        self.view.controls_frame.back_btn.set_command(self.handle_back)
        self.view.controls_frame.cont_btn.set_command(self.handle_continue)


class ParserController:
    def __init__(self, model: Model, view: View):
        self.root = view.root
        self.root_view = view
        self.view = view.progress
        self.model = model

    @parser_function('Logging measure details')
    def log_measure_details(self, _logger: MeasureDataLogger) -> None:
        _logger.log_measure_details()

    @parser_function('Logging parameter data')
    def log_parameter_data(self, _logger: MeasureDataLogger) -> None:
        _logger.log_parameter_data()

    @parser_function('Logging exclusion table data')
    def log_exclusion_table_data(self, _logger: MeasureDataLogger) -> None:
        _logger.log_exclusion_table_data()

    @parser_function('Logging value table data')
    def log_value_table_data(self, _logger: MeasureDataLogger) -> None:
        _logger.log_value_table_data()

    @parser_function('Logging value tables')
    def log_value_tables(self, _logger: MeasureDataLogger) -> None:
        _logger.log_value_tables()

    @parser_function('Logging calculations')
    def log_calculations(self, _logger: MeasureDataLogger) -> None:
        _logger.log_calculations()

    @parser_function('Logging permutations')
    def log_permutations(self, _logger: MeasureDataLogger) -> None:
        _logger.log_permutations()

    @parser_function('Logging characterization data')
    def log_characterization_data(self, _logger: MeasureDataLogger) -> None:
        _logger.log_characterization_data()

    @parser_function('Logging output')
    def log_output(self,
                   file_path: str,
                   data: ParserData,
                   measure: Measure
                  ) -> None:
        out_dir, file_name = os.path.split(file_path)
        if not os.path.exists(out_dir):
            raise RuntimeError(
                f'Invalid File Path: directory {out_dir} does not exist'
            )

        if os.path.exists(file_path) and not self.model.home.override_file:
            raise RuntimeError(
                f'Invalid File Path: a file named {file_name} already'
                f' exists at {out_dir}'
            )

        with MeasureDataLogger(measure, file_path, data) as _logger:
            self.log_measure_details(_logger)
            self.log_parameter_data(_logger)
            self.log_exclusion_table_data(_logger)
            self.log_value_table_data(_logger)
            self.log_value_tables(_logger)
            self.log_calculations(_logger)
            if self.model.home.validate_permutations:
                self.log_permutations(_logger)
            self.log_characterization_data(_logger)

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

    def get_etrm_measure(self) -> Measure:
        @parser_function(f'Retrieving measure {self.model.measure_id}')
        def get_measure(*args) -> Measure:
            connection = ETRMConnection(self.model.api_key)
            measure = connection.get_measure(self.model.measure_id)
            return measure

        start = time.time()
        measure = get_measure(self)
        end = time.time()
        self.view.log_frame.add(
            f'Retrieved measure {measure.version_id} in {end - start:.4f}'
            ' secomds'
        )
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

    def parse(self) -> None:
        progress_max = len(parser_function.all) * 100
        if not self.model.home.validate_permutations:
            progress_max -= 200
        self.view.controls_frame.progress_bar.config(maximum=progress_max + 1)

        try:
            if self.model.measure_source == MeasureSource.ETRM:
                measure = self.get_etrm_measure()
            elif self.model.measure_source == MeasureSource.JSON:
                measure = self.get_json_measure()
            else:
                self.view.log_frame.add(
                    text='Input validation failed, no measure source detected',
                    fg='#ff0000'
                )
                return
        except Exception as err:
            self.view.log_frame.add(
                text=str(err),
                fg='#ff0000'
            )
            return

        start = time.time()
        try:
            parser = MeasureParser(measure)
            self.parse_parameters(parser)
            self.parse_value_tables(parser)
            self.parse_exclusion_tables(parser)
            if self.model.home.validate_permutations:
                self.parse_permutations(parser)
            self.parse_characterizations(parser)
            self.log_output(
                self.model.output_file_path,
                parser.data,
                parser.measure
            )
        except Exception as err:
            if os.path.exists(self.model.output_file_path):
                os.remove(self.model.output_file_path)
            self.view.log_frame.add(
                text=str(err),
                fg='#ff0000'
            )
        else:
            end = time.time()
            self.view.log_frame.add(
                f'Parsing finished in {end - start:.4f} seconds'
            )
            self.model.parser_data = parser.data
        finally:
            self.view.controls_frame.progress_bar.config(maximum=0)


class PermQcController:
    def __init__(self, model: Model, view: View):
        self.root = view.root
        self.root_view = view
        self.view = view.progress
        self.model = model

    def qa_qc_permutations(self) -> None:
        ...
