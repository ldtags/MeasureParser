import os
from typing import Type
from ctypes import windll

from src.app.views.root import Root
from src.app.views.pages import *
from src.app.widgets import Page
from src.app.exceptions import (
    GUIError
)


# fixes blurry text on Windows 10
if os.name == 'nt':
    windll.shcore.SetProcessDpiAwareness(1)


class View:
    """Top level view class for the MVC pattern.

    Controls all views of the application.
    """

    def __init__(self):
        self.root = Root()
        self.main = MainPage(self.root.container, self.root)
        self.home = HomePage(self.root.container, self.root)
        self.progress = ProgressPage(self.root.container, self.root)
        self.results = ResultsPage(self.root.container, self.root)

        self.pages: dict[Type[Page], Page] = {
            MainPage: self.main,
            HomePage: self.home,
            ProgressPage: self.progress,
            ResultsPage: self.results
        }

    def show(self, page: Type[Page]) -> None:
        try:
            self.pages[page].show()
        except KeyError:
            raise GUIError(f'The page {str(page)} does not exist')

    def set_api_key(self, api_key: str) -> None:
        # etrm_frame = self.home.source_frame.source_frame.etrm_frame
        # etrm_frame.api_key_entry.set_text(api_key)
        pass

    def set_measure(self, measure_id: str) -> None:
        # etrm_frame = self.home.source_frame.source_frame.etrm_frame
        # etrm_frame.measure_entry.set_text(measure_id)
        pass

    def start(self) -> None:
        self.root.mainloop()

    def close(self) -> None:
        self.root.destroy()
