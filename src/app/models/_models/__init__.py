__all__ = ["HomeModel", "ResultsModel", "ProgressModel"]


from typing import TypeVar as _TypeVar

from src.app.models._models.home import HomeModel
from src.app.models._models.results import ResultsModel
from src.app.models._models.progress import ProgressModel


GenericModel = _TypeVar("GenericModel", HomeModel, ResultsModel, ProgressModel)
