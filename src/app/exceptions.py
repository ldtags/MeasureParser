class GUIError(BaseException):
    message = 'An error occurred within the GUI'

    def __init__(self, message: str | None=None):
        """Base class for GUI related exceptions."""

        self.message = message or self.message
        super().__init__(self.message)


class ValidationError(GUIError):
    message = 'GUI data is invalid'

    def __init__(self, message: str | None=None):
        self.message = message or self.message
        super().__init__(self.message)
