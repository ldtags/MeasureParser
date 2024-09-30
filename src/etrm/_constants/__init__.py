"""This sub-package contains constants used in the permutation QA/QC process.

The purpose of this package is to consolidate all permutation column names
into a single, easily accessible location that can be modified with minimal
detriment to the eTRM package.

This package is separated into two modules: reporting and verbose. The
reporting module contains the reporting names of each column. The verbose
module contains the verbose name of each module.

Use the reporting module when working with data obtained via the eTRM API.

Use the verbose module when working with data parsed from permutation CSV
files.

All column names found in each module are listed in order.

Constants not related to permutation columns must be placed in this file.
"""


__all__ = []


import src.etrm._constants.reporting as reporting
import src.etrm._constants.verbose as verbose
