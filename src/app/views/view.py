import os
from ctypes import windll
from typing import Type

from src.app.views.root import Root
from src.app.views._views import HomeView, ProgressView, ResultsView, GenericView
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
        self.home = HomeView(self.root.container, self.root)
        self.progress = ProgressView(self.root.container, self.root)
        self.results = ResultsView(self.root.container, self.root)
        self.views: dict[Type[GenericView], GenericView] = {
            HomeView: self.home,
            ProgressView: self.progress,
            ResultsView: self.results,
        }

    def __getitem__(self, view) -> GenericView:
        return self.views[view]

    def show(self, view: Type[GenericView]) -> None:
        try:
            self.views[view].show()
        except KeyError:
            raise GUIError(f"No view bound to the class {view} exists")

    def start(self) -> None:
        self.root.mainloop()

    def close(self) -> None:
        self.root.close()
