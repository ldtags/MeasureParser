class MeasureFormatError(Exception):
    def __init__(self, message='measure is missing required fields'):
        self.message: str = message
        super().__init__(self.message)


class ParameterFormatError(Exception):
    def __init__(self, message='parameter is missing required fields'):
        self.message: str = message
        super().__init__(self.message)


class ValueTableFormatError(Exception):
    def __init__(self, message='non-shared value table is missing required fields'):
        self.message: str = message
        super().__init__(self.message)


class SharedTableFormatError(Exception):
    def __init__(self, message='shared value table is missing required fields'):
        self.message: str = message
        super().__int__(self.message)

        
class VersionFormatError(Exception):
    def __init__(self, message='version is missing required fields'):
        self.message: str = message
        super().__init__(self.message)

class PermutationFormatError(Exception):
    def __init__(self, message='permutation is missing required information'):
        self.message: str = message
        super().__init__(self.message)
        
class UnknownPermutationError(Exception):
    def __init__(self, message: str, name: str):
        self.name: str = name
        self.message: str = message if message != None \
            else f'the permutation, {name}, is unknown'
        super().__init__(self.message)
        
class ColumnFormatError(Exception):
    def __init__(self, message='column is missing required information'):
        self.message: str = message
        super().__init__(self.message)
        
class CalculationFormatError(Exception):
    def __init__(self, message='calculation is missing required information'):
        self.message: str = message
        super().__init__(self.message)

class RequiredParameterError(Exception):
    def __init__(self, message: str, name: str):
        self.message: str = message if message != None \
            else 'measure is missing a required parameter' \
                + (f' - {name}' if name != None else '')
        super().__init__(self.message)
        
class RequiredCharacterizationError(Exception):
    def __init__(self, message: str, name: str):
        self.message: str = message if message != None \
            else 'measure is missing a required characterization' \
                + (f' - {name}' if name != None else '')
        super().__init__(self.message)

class RequiredPermutationError(Exception):
    def __init__(self, message: str, name: str):
        self.message: str = message if message != None \
            else 'measure is missing a required permutation' \
                + (f' - {name}' if name != None else '')
        super().__init__(self.message)