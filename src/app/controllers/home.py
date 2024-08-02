import re
import os
import json
import tkinter as tk
from typing import Callable

from src import utils
from src.app.enums import (
    Result,
    SUCCESS,
    FAILURE,
    MeasureSource
)
from src.app.views import View
from src.app.models import Model
from src.etrm import sanitizers, patterns
from src.etrm.exceptions import (
    ETRMRequestError,
    UnauthorizedError,
    ETRMConnectionError
)
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
        # self.source_controller = SourceController(model, view)
        # self.output_controller = OutputController(model, view)
        # self.controls_controller = ControlsController(model, view, start_func)
        # self.__update_view()

    def __update_view(self) -> None:
        """Sets default options in the view.

        Default option states are retrieved from the app config.

        Use when the home page is shown.
        """
    
        checkbox_options = self.view.output_frame.checkbox_options
        if app_config.override_file:
            checkbox_options.override_file.set(True)
        else:
            checkbox_options.override_file.set(False)


class SourceController:
    def __init__(self, model: Model, view: View):
        self.root = view.root
        self.root_view = view
        self.view = view.home
        self.model = model
        self.__bind_entry_validations()

    def validate_api_key_entry(self, text: str) -> bool:
        if text == '':
            return True

        re_match = re.search(patterns.VERSION_WHITELIST, text)
        if re_match is None:
            return True
        return False

    def disable_etrm_source(self, text: str) -> bool:
        source = self.view.source_frame
        if text != '':
            source.etrm_frame.measure_entry.disable()
        else:
            source.etrm_frame.measure_entry.enable()
        return True

    def disable_json_source(self, text: str) -> bool:
        if not self.validate_api_key_entry(text):
            return False

        source = self.view.source_frame
        checkboxes = self.view.output_frame.checkbox_options
        is_placeholder = source.etrm_frame.measure_entry.is_placeholder
        if text == '' or is_placeholder:
            source.json_frame.file_entry.enable()
            checkboxes.validate_permutations.config(
                state=tk.NORMAL,
                cursor='hand2'
            )
        else:
            source.json_frame.file_entry.disable()
            checkboxes.validate_permutations.config(
                state=tk.DISABLED,
                cursor='arrow'
            )
        return True

    def __bind_entry_validations(self) -> None:
        sources = self.view.source_frame
        json_reg = self.root.register(self.disable_etrm_source)
        sources.json_frame.file_entry.set_validator(
            validate='key',
            command=(json_reg, r'%P')
        )

        etrm_reg = self.root.register(self.disable_json_source)
        sources.etrm_frame.measure_entry.set_validator(
            validate='key',
            command=(etrm_reg, r'%P')
        )


class OutputController:
    def __init__(self, model: Model, view: View):
        self.root = view.root
        self.root_view = view
        self.view = view.home
        self.model = model
        self.__bind_entry_validations()
        self.__bind_events()

    def validate_file_name(self, text: str) -> bool:
        pattern = re.compile(f'^.*{re.escape(".")}txt$')
        return re.fullmatch(pattern, text) is not None

    def __bind_entry_validations(self) -> None:
        fname_reg = self.root.register(self.validate_file_name)
        self.view.output_frame.options_frame.fname_entry.set_validator(
            validate='key',
            command=(fname_reg, '%P')
        )

    def handle_override_file(self) -> None:
        checkbox_options = self.view.output_frame.checkbox_options
        state = checkbox_options.override_file.get()
        self.model.home.override_file = state

    def handle_validate_permutations(self) -> None:
        checkbox_options = self.view.output_frame.checkbox_options
        state = checkbox_options.validate_permutations.get()
        self.model.home.validate_permutations = state

    def __bind_events(self) -> None:
        checkbox_options = self.view.output_frame.checkbox_options
        checkbox_options.override_file.check_box.config(
            command=self.handle_override_file
        )
        checkbox_options.validate_permutations.check_box.config(
            command=self.handle_validate_permutations
        )


class ControlsController:
    def __init__(self,
                 model: Model,
                 view: View,
                 start_func: Callable[[], None]):
        self.root = view.root
        self.root_view = view
        self.view = view.home
        self.model = model
        self.start_func = start_func
        self.__bind_events()

    def validate_measure_file(self, file_path: str) -> Result:
        _, file_name = os.path.split(file_path)
        try:
            with open(file_path, 'r+') as fp:
                measure_json = json.load(fp)
        except OSError as err:
            if err.errno == 13:
                self.view.source_frame.print_err(
                    f'Please close {file_name}'
                )
            else:
                self.view.source_frame.print_err(
                    f'An error occurred while reading {file_name}'
                )
            return FAILURE
        except json.JSONDecodeError:
            self.view.source_frame.print_err(
                f'An error occurred while decoding {file_name}'
            )
            return FAILURE

        if utils.is_etrm_measure(measure_json):
            return SUCCESS

        return FAILURE

    def set_json_measure(self) -> Result:
        file_path = self.view.source_frame.json_frame.file_entry.get()
        if file_path == '':
            return FAILURE

        dir_path, file_name = os.path.split(file_path)
        if not os.path.exists(file_path):
            err = f'No file named {file_name} exists'
            if dir_path != '':
                err += f' in {dir_path}'
            self.view.source_frame.json_frame.print_err(err)
            return FAILURE

        if not os.path.isfile(file_path):
            self.view.source_frame.json_frame.print_err(
                'Measure JSON file must be a file, not a folder'
            )
            return FAILURE

        result = self.validate_measure_file(file_path)
        if result == SUCCESS:
            self.model.measure_file_path = file_path
            self.model.measure_source = MeasureSource.JSON
            return SUCCESS

        self.view.source_frame.json_frame.print_err(
            f'File {file_name} is not a valid measure JSON file'
        )
        return FAILURE

    def set_etrm_measure(self) -> Result:
        etrm_frame = self.view.source_frame.etrm_frame
        api_key = etrm_frame.api_key_entry.get()
        measure_id = etrm_frame.measure_entry.get()
        if api_key == '' or measure_id == '':
            return FAILURE

        sanitized_key = None
        try:
            sanitized_key = sanitizers.sanitize_api_key(api_key)
        except UnauthorizedError:
            etrm_frame.print_err(
                err='Invalid API key',
                entry='api_key'
            )
        except ETRMConnectionError:
            self.view.source_frame.print_err(
                'An unexpected error occurred while validating the API key'
            )

        sanitized_id = None
        try:
            sanitized_id = sanitizers.sanitize_measure_id(measure_id)
        except ETRMRequestError:
            etrm_frame.print_err(
                err='Invalid measure ID',
                entry='measure'
            )
        except ETRMConnectionError:
            self.view.source_frame.print_err(
                'An unexpected error occurred while validating the measure ID'
            )

        if sanitized_key is not None and sanitized_id is not None:
            self.model.api_key = sanitized_key
            self.model.measure_id = sanitized_id
            self.model.measure_source = MeasureSource.ETRM
            return SUCCESS

        return FAILURE

    def get_measure_source(self) -> MeasureSource | None:
        """Returns the measure source and ensure mutual exclusion between
        sources.

        Returns `None` if mutual exclusion is violated or if required data is
        missing.
        """

        sources = self.view.source_frame
        file_path = sources.json_frame.file_entry.get()
        api_key = sources.etrm_frame.api_key_entry.get()
        measure_id = sources.etrm_frame.measure_entry.get()

        if file_path != '' and (api_key != '' or measure_id != ''):
            sources.print_err('Data should not be entered in both sources')
            return None

        if file_path != '':
            return MeasureSource.JSON

        if api_key != '' and measure_id != '':
            return MeasureSource.ETRM

        if api_key == '':
            sources.etrm_frame.print_err(
                err='* Required',
                entry='api_key'
            )
            return None

        if measure_id == '':
            sources.etrm_frame.print_err(
                err='* Required',
                entry='measure'
            )
            return None

        return None

    def set_measure(self) -> Result:
        """Validates and sets the measure source information in the model.

        Use when propogating measure source data before initializing the
        measure parsing process.
        """

        source = self.get_measure_source()
        if source is None:
            return FAILURE

        if source == MeasureSource.JSON:
            result = self.set_json_measure()
            return result

        if source == MeasureSource.ETRM:
            result = self.set_etrm_measure()
            return result

        self.view.source_frame.print_err('An unexpected error occurred')
        return FAILURE

    def get_output_dir_path(self) -> str | None:
        output_options = self.view.output_frame.options_frame
        dir_path = output_options.outdir_entry.get()
        if dir_path == '':
            output_options.print_err(
                err='* Required',
                entry='directory'
            )
            return None

        path, dir_name = os.path.split(dir_path)
        if not os.path.exists(dir_path):
            err = f'No folder named {dir_name} exists'
            if path != '':
                err += f' in {path}'
            output_options.print_err(err=err, entry='directory')
            return None

        if os.path.isfile(dir_path):
            output_options.print_err(
                err='Path must point to a folder, not a file',
                entry='directory'
            )
            return None

        return dir_path

    def get_output_file_name(self) -> str | None:
        output_options = self.view.output_frame.options_frame
        file_name = output_options.fname_entry.get()
        if file_name == '':
            output_options.print_err(
                err='* Required',
                entry='file'
            )
            return None

        return file_name

    def get_output_path(self) -> str | None:
        dir_path = self.get_output_dir_path()
        if dir_path is None:
            return None

        file_name = self.get_output_file_name()
        if file_name is None:
            return None

        output_options = self.view.output_frame.options_frame
        file_path = os.path.join(dir_path, file_name)
        if os.path.exists(file_path):
            if not self.model.home.override_file:
                output_options.print_err(
                    err=f'A file named {file_name} already exists in {dir_path}',
                    entry='file'
                )
                return None

            try:
                with open(file_path, 'r+'):
                    pass
            except OSError as err:
                if err.errno == 13:
                    output_options.print_err(
                        err=f'Please close {file_name}',
                        entry='file'
                    )
                else:
                    output_options.print_err(
                        err=f'Could not open {file_name}',
                        entry='file'
                    )
                return None

        self.model.output_file_path = file_path
        return file_path

    def update_model(self) -> None:
        checkboxes = self.view.output_frame.checkbox_options
        checkbox = checkboxes.validate_permutations
        if checkbox.state == tk.DISABLED:
            self.model.home.validate_permutations = False

    def start(self) -> None:
        """Starts the `start_func` method passed to this controller
        on initialization.

        Use when executing a method belonging to a separate controller.
        """

        self.update_model()

        output_path = self.get_output_path()
        if output_path is None:
            return

        result = self.set_measure()
        if result == FAILURE:
            return

        self.start_func()

    def __bind_events(self) -> None:
        """Binds events to widgets in the control frame."""

        view = self.view.controls_frame
        view.close_btn.set_command(self.root_view.close)
        view.start_btn.set_command(self.start)
