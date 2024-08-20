from src.config import app_config


class HomeModel:
    def __init__(self):
        self.override_file = app_config.override_file
        self.validate_permutations = False
        self.qa_qc_permutations = False
