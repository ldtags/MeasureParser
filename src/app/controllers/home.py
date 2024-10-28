import re
import os
import sys
import tkinter as tk
from typing import Callable, Literal

from src.app.types import MeasureSourceState
from src.app.views import View, HomeView, home
from src.app.models import Model, HomeModel
from src.app.exceptions import ValidationError, GUIError
from src.app.controllers.base_controller import BaseController
from src.etrm import sanitizers, patterns
from src.etrm.exceptions import ETRMRequestError, UnauthorizedError, ETRMConnectionError
from src.config import app_config


_BaseHomeController = BaseController[HomeModel, HomeView]


def sanitize_file_path(file_path: str, exists: bool = True, _dir: bool = False) -> str:
    file_path = os.path.normpath(file_path)
    if exists and not os.path.exists(file_path):
        raise ValidationError("File does not exist")

    if not exists and os.path.exists(file_path):
        raise ValidationError("File already exists")

    if not _dir and not os.path.isfile(file_path):
        raise ValidationError("File is not a regular file")

    if _dir and not os.path.isdir(file_path):
        raise ValidationError("File is not a directory")

    if exists and not _dir:
        try:
            os.access(file_path, os.R_OK)
        except OSError:
            raise ValidationError("Insufficient file permissions")

    return file_path


def sanitize_file_name(file_name: str, ext: str | None = None) -> str:
    parts = os.path.split(file_name)
    file_name = parts[-1]
    if ext is not None:
        _name, _ext = os.path.splitext(file_name)
        if _ext == "":
            file_name = f"{_name}{ext}"
        elif _ext != ext:
            file_name = f"{file_name}{ext}"

    return file_name


class HomeController(_BaseHomeController):
    def __init__(
        self, model: Model, view: View, start_func: Callable[[tk.Event | None], None]
    ) -> None:
        BaseController.__init__(self, model, view)
        self.start_func = start_func
        self.source_controller = SourceController(model, view)
        self.output_controller = OutputController(model, view)
        self.controls_controller = ControlsController(model, view, start_func)
        self.source_frames = [
            self.view.parser_container.source_frame,
            self.view.perm_qc_container.source_frame
        ]

        self._update_view()
        self._update_model()
        self._bind_events()

    def _update_view(self) -> None:
        """Sets default options in the view.

        Default option states are retrieved from the app config.

        Use when the home page is shown.
        """

        if self.model.remember_me:
            api_key = app_config.api_key
            for source_frame in self.source_frames:
                source_frame.etrm_frame.api_key_entry.set_text(api_key)
                source_frame.etrm_frame.api_key_entry.set_text(api_key)
                source_frame.etrm_frame.rm_var.set(1)

    def _update_model(self) -> None:
        """Sets default options in the model."""

        self.model.view_state = self.view.state
        self.model.source_states["parser"] = "local"
        self.model.source_states["permqc"] = "local"

    def _on_tab_selection(self, event: tk.Event | None = None) -> None:
        tab_id = self.view.notebook.select()
        if not isinstance(tab_id, str):
            return

        container_path = tab_id.split("!")
        if container_path == []:
            return

        container = container_path[-1]
        match container:
            case "parsercontainer":
                self.view._state = "parser"
                self.model.view_state = "parser"
            case "permqccontainer":
                self.view._state = "permqc"
                self.model.view_state = "permqc"
            case other:
                raise tk.TclError(f"Unknown page: {other}")

    def _bind_events(self) -> None:
        self.view.notebook.bind("<<NotebookTabChanged>>", self._on_tab_selection)


class SourceController(_BaseHomeController):
    def __init__(self, model: Model, view: View):
        super().__init__(model, view)
        self.api_key_reg = self.root.register(self.validate_api_key)
        self.measure_reg = self.root.register(self.validate_measure_id)
        self.source_frames = [
            self.view.parser_container.source_frame,
            self.view.perm_qc_container.source_frame
        ]

        self._apply_bindings()

    def _set_source_state(
        self, source_frame: home.MeasureSourceFrame, source_state: MeasureSourceState
    ) -> None:
        """Sets the source state of the current view to local or api."""

        source_frame.set_state(source_state)
        self.model.source_states[source_frame.view_state] = source_state

    def _set_remember_me(self, value: Literal[0, 1], api_key: str) -> None:
        match value:
            case 0:
                self.model.remember_me = False
            case 1:
                self.model.remember_me = True
                self.model.api_key = api_key
            case other:
                raise tk.TclError(f"Invalid checkbox value: {other}")

    def _bind_events(self, source_frame: home.MeasureSourceFrame) -> None:
        source_frame.json_rb.configure(
            command=lambda _=None: self._set_source_state(source_frame, "local")
        )

        source_frame.etrm_rb.configure(
            command=lambda _=None: self._set_source_state(source_frame, "api")
        )

        source_frame.etrm_frame.rm_checkbox.configure(
            command=lambda _=None: self._set_remember_me(
                source_frame.etrm_frame.rm_var.get(),
                source_frame.etrm_frame.api_key_entry.get()
            )
        )

    def validate_measure_id(self, text: str) -> bool:
        if text == "":
            return True

        re_match = re.search(patterns.VERSION_WHITELIST, text)
        if re_match is None:
            return True

        return False

    def validate_api_key(self, text: str) -> bool:
        if text == "":
            return True

        re_match = re.search(patterns.VERSION_WHITELIST, text)
        if re_match is None:
            return True

        return False

    def _bind_entry_validations(self, source_frame: home.MeasureSourceFrame) -> None:
        source_frame.etrm_frame.measure_entry.set_validator(
            validate="key", command=(self.measure_reg, r"%P")
        )

        source_frame.etrm_frame.api_key_entry.set_validator(
            validate="key", command=(self.api_key_reg, r"%P")
        )

    def _apply_bindings(self) -> None:
        for source_frame in self.source_frames:
            self._bind_entry_validations(source_frame)
            self._bind_events(source_frame)


class OutputController(_BaseHomeController):
    def __init__(self, model: Model, view: View):
        super().__init__(model, view)


class OptionsController(_BaseHomeController):
    def __init__(self, model: Model, view: View) -> None:
        super().__init__(model, view)

        self._bind_events(self.view.parser_container.options_frame)
        self._bind_events(self.view.perm_qc_container.options_frame)

    def handle_override_file(self, options_frame: home.OptionsFrame) -> None:
        self.model.override_file = options_frame.override_file.get()

    def _bind_events(self, options_frame: home.OptionsFrame) -> None:
        options_frame.override_file.check_box.configure(
            command=lambda: self.handle_override_file(options_frame)
        )


class ControlsController(_BaseHomeController):
    def __init__(self, model: Model, view: View, start_func: Callable[[], None]):
        super().__init__(model, view)
        self.start_func = start_func
        self._bind_events()

    def get_output_dir(self, output_frame: home.OutputFrame) -> str:
        dir_path = output_frame.dir_entry.get()
        if dir_path == "":
            raise ValidationError("* Required")

        return sanitize_file_path(dir_path, _dir=True)

    def get_output_file(self, output_frame: home.OutputFrame) -> str:
        file_name = output_frame.file_entry.get()
        if file_name == "":
            raise ValidationError("* Required")

        return sanitize_file_name(file_name)

    def update_output_model(self) -> None:
        match self.view.state:
            case "parser":
                output_frame = self.view.parser_container.output_frame
            case "permqc":
                output_frame = self.view.perm_qc_container.output_frame
            case other:
                raise RuntimeError(f"Invalid home view state: {other}")

        try:
            dir_path = self.get_output_dir(output_frame)
        except ValidationError as err:
            output_frame.print_err(str(err), "dir")
            raise

        try:
            file_name = self.get_output_file(output_frame)
        except ValidationError as err:
            output_frame.print_err(str(err), "file")
            raise

        self.model.output_file_path = os.path.normpath(
            os.path.join(dir_path, file_name)
        )

    def get_measure_id(self, source_frame: home.MeasureSourceFrame) -> str:
        measure_id = source_frame.etrm_frame.measure_entry.get()
        if measure_id == "":
            raise ValidationError("* Required")

        try:
            sanitized_id = sanitizers.sanitize_measure_id(measure_id)
        except (ETRMRequestError, ETRMConnectionError) as err:
            raise ValidationError(str(err))

        return sanitized_id

    def get_api_key(self, source_frame: home.MeasureSourceFrame) -> str:
        api_key = source_frame.etrm_frame.api_key_entry.get()
        if api_key == "":
            raise ValidationError("* Required")

        try:
            sanitized_key = sanitizers.sanitize_api_key(api_key)
        except (UnauthorizedError, ETRMConnectionError) as err:
            raise ValidationError(str(err))

        return sanitized_key

    def get_measure_file_path(self) -> str:
        source_frame = self.view.parser_container.source_frame
        file_path = source_frame.json_frame.file_entry.get()
        if file_path == "":
            raise ValidationError("* Required")

        file_path = sanitize_file_path(file_path)
        _, file_ext = os.path.splitext(file_path)
        if file_ext != ".json":
            raise ValidationError("File must be a JSON file")

        return file_path

    def update_parser_model(self) -> None:
        source_frame = self.view.parser_container.source_frame
        match source_frame.state:
            case "local":
                try:
                    measure_file_path = self.get_measure_file_path()
                    source_frame.clear_err()
                except ValidationError as err:
                    source_frame.print_err(str(err))
                    raise

                self.model.measure_file_path = measure_file_path
            case "api":
                try:
                    measure_id = self.get_measure_id(source_frame)
                    source_frame.clear_err("measure")
                except ValidationError as err:
                    source_frame.print_err(str(err), "measure")
                    raise

                try:
                    api_key = self.get_api_key(source_frame)
                    source_frame.clear_err("api_key")
                except ValidationError as err:
                    source_frame.print_err(str(err), "api_key")
                    raise

                self.model.measure_id = measure_id
                self.model.api_key = api_key
            case other:
                raise GUIError(f"Unknown home view state: {other}")

    def get_permutations_file_path(self) -> None:
        source_frame = self.view.perm_qc_container.source_frame
        file_path = source_frame.json_frame.file_entry.get()
        if file_path == "":
            raise ValidationError("* Required")

        file_path = sanitize_file_path(file_path)
        _, file_ext = os.path.splitext(file_path)
        if file_ext != ".csv":
            raise ValidationError("File must be a CSV file")

        return file_path

    def update_permqc_model(self) -> None:
        source_frame = self.view.perm_qc_container.source_frame
        match source_frame.state:
            case "local":
                try:
                    perm_file_path = self.get_permutations_file_path()
                    source_frame.clear_err()
                except ValidationError as err:
                    source_frame.print_err(str(err))
                    raise

                self.model.permutations_file_path = perm_file_path
            case "api":
                try:
                    measure_id = self.get_measure_id(source_frame)
                    source_frame.clear_err("measure")
                except ValidationError as err:
                    source_frame.print_err(str(err), "measure")
                    raise

                try:
                    api_key = self.get_api_key(source_frame)
                    source_frame.clear_err("api_key")
                except ValidationError as err:
                    source_frame.print_err(str(err), "api_key")
                    raise

                self.model.measure_id = measure_id
                self.model.api_key = api_key
            case other:
                raise GUIError(f"Unknown home view state: {other}")

    def update_model(self) -> None:
        """Updates the model with any relevant runtime content."""

        match self.view.state:
            case "parser":
                self.update_parser_model()
            case "permqc":
                self.update_permqc_model()

        self.update_output_model()

    def start(self) -> None:
        """Starts the `start_func` method passed to this controller
        on initialization.

        Use when executing a method belonging to a separate controller.
        """

        try:
            self.update_model()
        except ValidationError as err:
            print(str(err), file=sys.stderr)
            return

        self.start_func()

    def _bind_events(self) -> None:
        """Binds events to widgets in the control frame."""

        view = self.view.controls_frame
        view.close_btn.set_command(self.root_view.close)
        view.start_btn.set_command(self.start)
