import re
import os
import json
import tkinter as tk
from typing import Callable

from src import utils
from src.app.enums import Result, SUCCESS, FAILURE
from src.app.views import View
from src.app.models import Model
from src.etrm.models import Measure
from src.config import app_config


class HomeController:
    def __init__(self,
                 model: Model,
                 view: View,
                 start_func: Callable[[], None]):
        self.root = view.root
        self.root_view = view
        self.view = view.home
        self.model = model
        self.start_func = start_func
        self.__bind_output()
        self.__bind_controls()
        self.__set_defaults()

    def validate_file_name(self, text: str) -> bool:
        pattern = re.compile(f'^.*{re.escape(".")}txt$')
        return re.fullmatch(pattern, text) is not None

    def __bind_output_validations(self) -> None:
        view = self.view.output_frame
        fname_reg = self.root.register(self.validate_file_name)
        fname_entry = view.options_frame.fname_entry
        fname_entry.config(
            validate='key',
            validatecommand=(fname_reg, '%P')
        )

    def handle_override_file(self) -> None:
        checkbox_options = self.view.output_frame.checkbox_options
        state = checkbox_options.override_file.get()
        self.model.home.override_file = state

    def __bind_checkbox_options(self) -> None:
        checkbox_options = self.view.output_frame.checkbox_options
        checkbox_options.override_file.check_box.config(
            command=self.handle_override_file
        )

    def __bind_output(self) -> None:
        self.__bind_output_validations()
        self.__bind_checkbox_options()

    def close(self) -> None:
        self.root.destroy()

    def validate_measure_sources(self) -> Result:
        view = self.view.source_frame
        file_path = view.source_frame.json_frame.file_entry.get()
        api_key = view.source_frame.etrm_frame.api_key_entry.get()
        measure_id = view.source_frame.etrm_frame.measure_entry.get()

        if not (file_path != '' or (api_key != '' and measure_id != '')):
            view.print_err('* Required')
            return FAILURE

        if file_path != '' and (api_key != '' and measure_id != ''):
            view.print_err('Select only one measure source')
            return FAILURE

        if file_path != '':
            if not os.path.exists(file_path):
                view.print_err('File does not exist')
                return FAILURE
    
            with open(file_path, 'r') as fp:
                measure_json = json.load(fp)
                if not utils.is_etrm_measure(measure_json):
                    view.print_err('Invalid measure JSON file')

        view.clear_err()
        return SUCCESS

    def validate_output_path(self) -> str | None:
        view = self.view.output_frame.options_frame
        output_path = view.outdir_entry.get()
        if output_path == '':
            view.print_error(
                type='directory',
                err='* Required'
            )
            return None

        if not os.path.exists(output_path):
            view.print_error(
                type='directory',
                err=f'Folder does not exist'
            )
            return None

        view.outdir_err_var.set(' ')
        return output_path

    def validate_output_file_name(self,
                                  output_path: str | None=None
                                 ) -> str | None:
        view = self.view.output_frame.options_frame
        file_name = view.fname_entry.get()
        if file_name == '.txt':
            view.print_error(
                type='file',
                err='* Required'
            )
            return None

        if output_path is None:
            return None

        file_path = os.path.join(output_path, file_name)
        if os.path.exists(file_path) and not self.model.home.override_file:
            view.print_error(
                type='file',
                err=f'The file {file_path} already exists'
            )
            return None

        view.file_err_var.set(' ')
        return file_name

    def validate_output_options(self) -> None:
        output_path = self.validate_output_path()
        file_name = self.validate_output_file_name(output_path)

        if output_path is None or file_name is None:
            return FAILURE

        self.model.output_file_path = os.path.join(output_path, file_name)
        return SUCCESS

    def set_measure(self) -> Measure:
        view = self.view.source_frame.source_frame
        file_path = view.json_frame.file_entry.get()
        if file_path != '':
            self.model.measure_source = 'json'
            self.model.measure_file_path = file_path
            return

        api_key = view.etrm_frame.api_key_entry.get()
        measure_id = view.etrm_frame.measure_entry.get()
        if api_key != '' and measure_id != '':
            self.model.measure_source = 'etrm'
            self.model.set_api_key(api_key)
            self.model.set_measure(measure_id)
            return

        raise RuntimeError('Measure source validation failed')

    def start(self) -> None:
        output_res = self.validate_measure_sources()
        source_res = self.validate_output_options()

        if output_res != SUCCESS or source_res != SUCCESS:
            return

        self.set_measure()
        self.start_func()

    def __bind_controls(self) -> None:
        view = self.view.controls_frame
        view.close_btn.set_command(self.close)
        view.start_btn.set_command(self.start)

    def __set_defaults(self) -> None:
        checkbox_options = self.view.output_frame.checkbox_options
        if app_config.override_file:
            checkbox_options.override_file.check_box.select()
        else:
            checkbox_options.override_file.check_box.deselect()
