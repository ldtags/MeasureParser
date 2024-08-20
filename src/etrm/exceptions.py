class ETRMError(BaseException):
    def __init__(self, message: str | None=None):
        self.message = message or 'An eTRM package error occurred'
        BaseException.__init__(self)


class ETRMConnectionError(ETRMError):
    def __init__(self, message: str | None=None):
        ETRMError.__init__(
            self,
            message=message or 'An eTRM connection layer error occurred'
        )


class ETRMRequestError(ETRMConnectionError):
    def __init__(self, message: str | None=None):
        ETRMConnectionError.__init__(
            self,
            message=message or 'Request to the eTRM API failed'
        )


class ETRMResponseError(ETRMConnectionError):
    def __init__(self, message: str | None=None, status: int=500):
        self.status = status
        ETRMConnectionError.__init__(self, message=message or 'Server error')


class UnauthorizedError(ETRMRequestError):
    def __init__(self, message: str | None=None):
        ETRMRequestError.__init__(
            self,
            message=message or 'Unauthorized request'
        )


class SchemaError(ETRMError):
    def __init__(self, message: str | None=None):
        ETRMError.__init__(
            self,
            message=message or (
                'An error occurred while accessing the JSON schema'
            )
        )


class DatabaseError(ETRMError):
    def __init__(self, message: str | None):
        ETRMError.__init__(
            self,
            message=message or (
                'An error occurred while accessing the local database'
            )
        )
