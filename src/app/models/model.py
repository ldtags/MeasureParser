from typing import Type

from src.app.models._models import HomeModel, ResultsModel, ProgressModel, GenericModel


class Model:
    """Top level model of the MVC pattern.
    
    Controls all models of the application.
    """

    def __init__(self):
        self.home = HomeModel()
        self.progress = ProgressModel()
        self.results = ResultsModel()
        self.models: dict[Type[GenericModel], GenericModel] = {
            HomeModel: self.home,
            ProgressModel: self.progress,
            ResultsModel: self.results
        }

    def __getitem__(self, model: Type[GenericModel]) -> GenericModel:
        return self.models[model]
