class DatabaseError(Exception):
    def __init__(self, message: str | None):
        self.message = message or 'Database error has occurred.'


class DatabaseConnectionError(DatabaseError):
    def __init__(self, message: str | None = None):
        """General error for database connection exceptions.

        Uses a default message if `message == None`.
        """

        if message != None:
            self.message = message

        super().__init__(self.message)


class DatabaseContentError(DatabaseError):
    message = 'an unexpected database content error has occurred'

    def __init__(self, message: str | None=None):
        """General error for database content exceptions.

        Uses a default message if `message == None`.
        """

        if message != None:
            self.message = message

        super().__init__(self.message)
