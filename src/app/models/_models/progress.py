from src.parser import ParserData
from src.permqaqc import FieldData


class ProgressModel:
    def __init__(self):
        self.parser_data: ParserData | None = None
        self.permqc_data: FieldData | None = None
