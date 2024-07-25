from src.etrm.models import Measure


class HomeModel:
    def __init__(self):
        self.output_path: str | None = None
        self.measure: Measure | None = None
