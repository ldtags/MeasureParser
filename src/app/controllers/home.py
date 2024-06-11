from src.app.views import View
from src.app.models import Model


class HomeController:
    def __init__(self, model: Model, view: View):
        self.root_model = model
        self.model = model.home
        self.root_view = view
        self.view = view.home
        self.__bind()

    def close(self):
        self.root_view.root.destroy()

    def open_json_entry(self):
        file_path = self.view.json_popup()

    def __bind(self):
        self.view.controls_frame.close_btn.set_command(self.close)
        source_frame = self.view.tabbed_page.measure_source_frame
        source_frame.selection_frame.json_btn.set_command(self.open_json_entry)
        