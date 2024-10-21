import os
from ctypes import windll

from src.app.views.root import Root
from src.app.views.home import HomePage
from src.app.views.progress import ProgressPage
from src.app.views.results import ResultsPage
from src.app.widgets import Page
from src.app.exceptions import GUIError


# fixes blurry text on Windows 10
if os.name == "nt":
    windll.shcore.SetProcessDpiAwareness(1)


class View:
    """Top level view class for the MVC pattern.

    Controls all views of the application.
    """

    def __init__(self):
        self.root = Root()
        self.home = HomePage(self.root.container, self.root)
        self.progress = ProgressPage(self.root.container, self.root)
        self.results = ResultsPage(self.root.container, self.root)

        self.pages: dict[str, Page] = {
            HomePage.key: self.home,
            ProgressPage.key: self.progress,
            ResultsPage.key: self.results,
        }

    def show(self, page_name: str) -> None:
        try:
            self.pages[page_name].show()
        except KeyError:
            raise GUIError(f"No page named {page_name} exists")

    def set_api_key(self, api_key: str) -> None:
        etrm_frame = self.home.source_frame.source_frame.etrm_frame
        etrm_frame.api_key_entry.set_text(api_key)

    def set_measure(self, measure_id: str) -> None:
        etrm_frame = self.home.source_frame.source_frame.etrm_frame
        etrm_frame.measure_entry.set_text(measure_id)

    def start(self) -> None:
        self.root.mainloop()

    def close(self) -> None:
        self.root.destroy()
