import re

from src.app.views import View
from src.app.models import Model


class HomeController:
    def __init__(self, model: Model, view: View):
        self.root_model = model
        self.model = model.home
        self.root_view = view
        self.view = view.home
        self.root = view.root
        self.__bind_output()
        self.__bind_controls()

    def close(self):
        self.root.destroy()

    def validate_file_name(self, text: str) -> bool:
        pattern = re.compile(f'^.*{re.escape(".")}txt$')
        return re.fullmatch(pattern, text) is not None

    def __bind_output_validations(self):
        view = self.view.output_frame
        fname_reg = self.root.register(self.validate_file_name)
        fname_entry = view.options_frame.fname_entry
        fname_entry.config(
            validate='key',
            validatecommand=(fname_reg, '%P')
        )

    def __bind_output(self):
        self.__bind_output_validations()

    def __bind_controls(self):
        self.view.controls_frame.close_btn.set_command(self.close)
