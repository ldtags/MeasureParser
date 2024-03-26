'''eTRM Measure JSON Parser'''

__author__ = 'Liam Tangney'
__version__ = '1.1.0'
__all__ = ['parser']

import os

from .measure import (
    Measure,
    ValueTable,
    SharedValueTable,
    Parameter,
    SharedParameter,
    ExclusionTable,
    Calculation,
    Characterization,
    Permutation
)


_ROOT = os.path.abspath(os.path.dirname(__file__))
def get_path(filename: str, directory: str='resources') -> str:
    '''Returns an absolute path to a file in the package'''
    return os.path.join(_ROOT, directory, filename)