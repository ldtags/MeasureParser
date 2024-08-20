from enum import Enum


class Result(Enum):
    SUCCESS = 0
    FAILURE = 1
    VALID = SUCCESS
    INVALID = FAILURE

SUCCESS = Result.SUCCESS
FAILURE = Result.FAILURE
VALID = Result.VALID
INVALID = Result.INVALID

class MeasureSource(Enum):
    JSON = 'json'
    ETRM = 'etrm'

JSON = MeasureSource.JSON
ETRM = MeasureSource.ETRM
