import os
from ctypes import windll

from src.app.views.root import Root
from src.app.views.home import HomePage
from src.app.views.progress import ProgressPage
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
        self.home = HomePage(self.root.container, self.root)
        self.progress = ProgressPage(self.root.container, self.root)

        self.pages: dict[str, Page] = {
            HomePage.key: self.home,
            ProgressPage.key: self.progress
        }

    def show(self, page_name: str):
        try:
            self.pages[page_name].show()
        except KeyError:
            raise GUIError(f'No page named {page_name} exists')

    def start(self):
        self.root.mainloop()
