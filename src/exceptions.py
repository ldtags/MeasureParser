class ParserError(Exception):
    """Common base class for Measure Parser exceptions."""

    def __init__(self, message: str | None = None):
        self.message = message or 'Measure Parser exception occurred.'

        super().__init__(self.message)


class MeasureFormatError(ParserError):
    """Error class for missing required fields."""

    def __init__(self, message: str | None = None, field: str | None = None):
        self.message = message or 'Measure is formatted incorrectly.'
        self.field = field or 'measure'

        super().__init__(self.message)


class MeasureContentError(ParserError):
    """Error class for invalid data within fields."""

    def __init__(self, message: str | None = None, name: str | None = None):
        self.message = message or 'Measure contains invalid data.'
        self.name = name or 'unknown'

        super().__init__(self.message)


class RequiredContentError(MeasureContentError):
    """Error class for missing data within fields."""

    def __init__(self, message: str | None = None, name: str | None = None):
        self.message = message or 'Measure is missing required data.'

        super().__init__(self.message, name)


class InvalidFileError(ParserError):
    def __init__(self,
                 message: str | None = None,
                 file_name: str | None = None):
        if message != None:
            self.message = message
        elif file_name != None:
            if '\\' in file_name:
                file_name = file_name[file_name.rindex('\\') + 1:]
            self.message = f'{file_name} is not a valid eTRM measure JSON file'
        else:
            self.message = 'the input file is not a valid eTRM measure JSON file'
        super().__init__(self.message)
