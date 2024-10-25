__all__ = ["HomeView", "ProgressView", "ResultsView", "GenericView"]


from typing import TypeVar as _TypeVar

from src.app.views._views.home import HomeView
from src.app.views._views.results import ResultsView
from src.app.views._views.progress import ProgressView


GenericView = _TypeVar("GenericView", HomeView, ResultsView, ProgressView)
