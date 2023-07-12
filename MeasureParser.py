import sys
import json
import ParameterNames
import ValueTableNames
from MeasureObjects import Measure, SharedParameter, SharedValueTable, ValueTable
from typing import Optional, TextIO
try:
    from types import SimpleNamespace as Namespace
except ImportError:
    from argparse import Namespace


# defines the type of measure that the given measure satisfies
# returns nothing and does not modify any data, use for debugging
def defineMeasureTypes(measure: Measure) -> None:
    if measure.hasDEERVersion():
        print('is DEER measure')

    if measure.isAROrAOEMeasure():
        print('MAT = AR and/or AOE')

    if measure.isNCOrNRMeasure():
        print('MAT = NC and/or NR')

    if measure.isDefGSIAMeasure():
        print('is a default GSIA measure')

    if measure.isSectorDefaultMeasure():
        print('is a sector default measure')

    if measure.isDeemedDeliveryTypeMeasure():
        print('is a deemed delivery type measure')

    if measure.isWENMeasure():
        print('is a WEN measure')

    if measure.isFuelSubMeasure():
        print('is fuel substitution measure')

    if measure.isInteractiveMeasure():
        print('is an interactive measure')


# Parameters:
#   @sharedTables - a dict mapping all value tables to their respective api_name
#   @tableNames - a list of table names to check the measures value tables against
#
# validates that all shared value tables represented in @tableNames are found in @sharedTables
def validateSharedTableExistence(measure: Measure,
                                 tableNames: list[str]) -> None:
    for table in tableNames:
        if not measure.containsSharedTable(table):
            print(f'MISSING SHARED TABLE - {table}')


# Parameters:
#   @valueTables - a dict mapping all value tables to their respective api_name
#   @tableNames - a list of table names to check the measures value tables against
#
# validates that all value tables represented in @tableNames are found in @valueTables
def validateValueTableExistence(measure: Measure,
                                tableNames: list[str]) -> None:
    for table in tableNames:
        if not measure.containsValueTable(table):
            print(f'MISSING TABLE - {table}')


# Parameters:
#   @sharedParams - a dict mapping all measure parameters to their
#                       respective names
#   @paramNames - a list of parameter names to check the measure
#                     parameters against
#
# validates that all parameters represented in @paramNames are
#      found in @sharedParams
def validateParamExistence(measure: Measure,
                           paramNames: list[str]) -> None:
    for param in paramNames:
        if not measure.containsParam(param):
            print(f'MISSING PARAM - {param}')


def validateParamOrder(measure: Measure,
                       orderedParams: list[str]) -> None:
    for param in measure.params:
        if param.order \
                != (orderedParams.index(param.version.version_string) + 1):
            print('parameters are out of order')
            return None
        

def validateValueTableOrder(measure: Measure,
                            orderedTables: list[str]) -> None:
    for table in measure.valueTables:
        if table.order != (orderedTables.index(table.apiName) + 1):
            print('non-shared value tables are out of order')
            return None
        

def validateSharedTableOrder(measure: Measure,
                             orderedTables: list[str] ) -> None:
    for table in measure.sharedTables:
        if table.order \
                != (orderedTables.index(table.version.version_string) + 1):
            print('shared value tables are out of order')
            return None
        

def checkParams(measure: Measure,
                orderedParams: list[str]) -> list[SharedParameter]:
    unknown: list[SharedParameter] = []
    for param in measure.params:
        if param.version.version_string not in orderedParams:
            unknown.append(param)

    for param in unknown:
        measure.params.remove(param)


def filterInterParams(measure: Measure,
                      orderedParams: list[str]) -> list[str]:
    if not measure.containsParam('LightingType'):
        orderedParams.remove('LightingType')

    return orderedParams


def filterInterValueTables(measure: Measure,
                           orderedTables: list[str]) -> list[str]:
    if not measure.containsValueTable('IEApplicability'):
        orderedTables.remove('IEApplicability')

    return orderedTables


def filterInterSharedTables(measure: Measure,
                            orderedTables: list[str]) -> list[str]:
    if not measure.containsSharedTable('commercialInteractiveEffects'):
        orderedTables.remove('commercialInteractiveEffects')

    if not measure.containsSharedTable('residentialInteractiveEffects'):
        orderedTables.remove('residentialInteractiveEffects')

    return orderedTables

def filter_list(ordered_list: list[str],
                all_items: list[str],
                flag: str) -> list[str]:
    return list(filter(lambda item: all_items[item] != flag,
                       ordered_list))

"""Return a three-tuple containing ordered lists with ty
        1.  (shared/non-shared)
        2. 
docstring
"""
def get_ordered_list_tuple(measure: Measure
                       ) -> tuple[list[str], list[str], list[str]]:
    orderedParams = list(ParameterNames.ALL_PARAMS.keys())
    orderedValTables = list(ValueTableNames.ALL_VALUE_TABLES.keys())
    orderedShaTables = list(ValueTableNames.ALL_SHARED_TABLES.keys())

    try:
        if not measure.hasDEERVersion():
            orderedParams = filter_list(orderedParams,
                                        ParameterNames.ALL_PARAMS,
                                        'DEER')
            orderedValTables = filter_list(orderedValTables,
                                           ValueTableNames.ALL_VALUE_TABLES,
                                           'DEER')
            orderedShaTables = filter_list(orderedShaTables,
                                           ValueTableNames.ALL_SHARED_TABLES,
                                           'DEER')

        if not measure.isDefGSIAMeasure():
            orderedShaTables = filter_list(orderedShaTables,
                                           ValueTableNames.ALL_SHARED_TABLES,
                                           'NGSIA')
        else:
            orderedParams = filter_list(orderedParams,
                                        ParameterNames.ALL_PARAMS,
                                        'NGSIA')
            orderedShaTables = filter_list(orderedShaTables,
                                           ValueTableNames.ALL_SHARED_TABLES,
                                           'GSIA')

        if not measure.isAROrAOEMeasure():
            orderedParams = filter_list(orderedParams,
                                        ParameterNames.ALL_PARAMS,
                                        'MAT')
            orderedShaTables = filter_list(orderedShaTables,
                                           ValueTableNames.ALL_SHARED_TABLES,
                                           'ARAOE')
            orderedValTables = filter_list(orderedValTables,
                                           ValueTableNames.ALL_VALUE_TABLES,
                                           'NRNC+ARAOE')

        if not measure.isNCOrNRMeasure():
            orderedValTables = filter_list(orderedValTables,
                                           ValueTableNames.ALL_VALUE_TABLES,
                                           'NRNC+ARAOE')

        if not measure.isWENMeasure():
            orderedParams = filter_list(orderedParams,
                                        ParameterNames.ALL_PARAMS,
                                        'WEN')
            orderedShaTables = filter_list(orderedShaTables,
                                           ValueTableNames.ALL_SHARED_TABLES,
                                           'WEN')

        if measure.isSectorDefaultMeasure():
            orderedParams = filter_list(orderedParams,
                                        ParameterNames.ALL_PARAMS,
                                        'NTG')

        if measure.isResDefaultMeasure():
            orderedShaTables = filter_list(orderedShaTables,
                                           ValueTableNames.ALL_SHARED_TABLES,
                                           'RES_NDEF')
        else:
            orderedShaTables = filter_list(orderedShaTables,
                                           ValueTableNames.ALL_SHARED_TABLES,
                                           'RES-DEF')

        if not measure.isDeemedDeliveryTypeMeasure():
            orderedValTables = filter_list(orderedValTables,
                                           ValueTableNames.ALL_VALUE_TABLES,
                                           'DEEM')

        if not measure.isFuelSubMeasure():
            orderedValTables = filter_list(orderedValTables,
                                           ValueTableNames.ALL_VALUE_TABLES,
                                           'FUEL')

        if not measure.isInteractiveMeasure():
            orderedParams = filter_list(orderedParams,
                                        ParameterNames.ALL_PARAMS,
                                        'INTER')
            orderedShaTables = filter_list(orderedShaTables,
                                           ValueTableNames.ALL_SHARED_TABLES,
                                           'INTER')
            orderedValTables = filter_list(orderedValTables,
                                           ValueTableNames.ALL_VALUE_TABLES,
                                           'INTER')
        else:
            orderedParams = filterInterParams(measure, orderedParams)
            orderedShaTables \
                = filterInterSharedTables(measure, orderedShaTables)
            orderedValTables \
                = filterInterValueTables(measure, orderedValTables)
    except Exception as err:
        print(err)

    return (orderedParams, orderedValTables, orderedShaTables)


# Parameters:
#   @measure - a JSON file that represents a given measure
#
# Parses a given JSON file that outlines a given measure
# Parsing Specifications:
#   - Existence of required parameters and value tables (shared and non-shared)
#   - Correct order of parameters
#   - Correct order of value tables
def parseMeasure(measure: Measure, out: Optional[TextIO]) -> None:
    (orderedParams, orderedValTables, orderedShaTables) \
        = get_ordered_list_tuple(measure)

    defineMeasureTypes(measure)
    print('\nParams:')
    print(orderedParams)
    print('\nValue Tables:')
    print(orderedValTables)
    print('\nShared Tables:')
    print(orderedShaTables)

    print('\nUnknown Parameters/Tables:', file=out)
    print('    Params: ', list(
        map(lambda param: param.version.version_string,
            measure.removeUnknownParams(orderedParams))),
        file=out)
    print('    Non-Shared Value Tables: ', list(
        map(lambda table: table.apiName,
            measure.removeUnkownValueTables(orderedValTables))),
        file=out)
    print('    Shared Value Tables: ', list(
        map(lambda table: table.version.version_string,
            measure.removeUnkownSharedTables(orderedShaTables))),
        file=out)

    print('\nMissing Parameters/Tables:')
    validateParamExistence(measure, orderedParams)
    validateValueTableExistence(measure, orderedValTables)
    validateSharedTableExistence(measure, orderedShaTables)

    print('\nParameter/Table order:')
    validateParamOrder(measure, orderedParams)
    validateValueTableOrder(measure, orderedValTables)
    validateSharedTableOrder(measure, orderedShaTables)


# Parameters:
#   @filename - the name of a JSON measure file to be parsed
def main(filename: str) -> None:
    print(f'\nstarting to parse measure file - {filename}\n')
    
    with open(filename, 'r') as measureFile, \
         open('out.txt', 'w+') as out:
        measure: Measure = Measure(
            json.loads(measureFile.read(),
                       object_hook=lambda d: Namespace(**d)))
        parseMeasure(measure, out)

    print(f'\nfinished parsing measure file - {filename}')


if __name__ == '__main__':
    main(sys.argv[1])