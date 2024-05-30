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

from .utils import (
    json_obj,
    resource_path,
    is_etrm_measure
)


_ROOT = os.path.abspath(os.path.dirname(__file__))
