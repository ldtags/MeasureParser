import sys
import json
import ParameterNames
import ValueTableNames
from MeasureObjects import Measure, SharedParameter, SharedValueTable, ValueTable
try:
    from types import SimpleNamespace as Namespace
except ImportError:
    from argparse import Namespace


# defines the type of measure that the given measure satisfies
# returns nothing and does not modify any data, use for debugging
def defineMeasureTypes( measure : Measure ) -> None:
    if measure.hasDEERVersion():
        print( 'is DEER measure' )

    if measure.isAROrAOEMeasure():
        print( 'MAT = AR and/or AOE' )

    if measure.isNCOrNRMeasure():
        print( 'MAT = NC and/or NR' )

    if measure.isDefGSIAMeasure():
        print( 'is a default GSIA measure' )

    if measure.isSectorDefaultMeasure():
        print( 'is a sector default measure' )

    if measure.isDeemedDeliveryTypeMeasure():
        print( 'is a deemed delivery type measure' )

    if measure.isWENMeasure():
        print( 'is a WEN measure' )

    if measure.isFuelSubMeasure():
        print( 'is fuel substitution measure' )

    if measure.isInteractiveMeasure():
        print( 'is an interactive measure' )


# Parameters:
#   @sharedTables - a dict mapping all value tables to their respective api_name
#   @tableNames - a list of table names to check the measures value tables against
#
# validates that all shared value tables represented in @tableNames are found in @sharedTables
def validateSharedTableExistence( measure : Measure,
                                  tableNames : list[str] ) -> None:
    for table in tableNames:
        if not measure.containsSharedTable( table ):
            print( f'MISSING SHARED TABLE - {table}' )


# Parameters:
#   @valueTables - a dict mapping all value tables to their respective api_name
#   @tableNames - a list of table names to check the measures value tables against
#
# validates that all value tables represented in @tableNames are found in @valueTables
def validateValueTableExistence( measure : Measure,
                                 tableNames : list[str] ) -> None:
    for table in tableNames:
        if not measure.containsValueTable( table ):
            print( f'MISSING TABLE - {table}' )


# Parameters:
#   @sharedParams - a dict mapping all measure parameters to their respective names
#   @paramNames - a list of parameter names to check the measure parameters against
#
# validates that all parameters represented in @paramNames are found in @sharedParams
def validateParamExistence( measure : Measure,
                            paramNames : list[str] ) -> None:
    for param in paramNames:
        if not measure.containsParam( param ):
            print( f'MISSING PARAM - {param}' )


def validateParamOrder( measure : Measure,
                        orderedParams : list[str] ) -> None:
    for param in measure.params:
        if param.order != ( orderedParams.index( param.version.version_string ) + 1 ):
            print( 'parameters are out of order' )
            return None
        

def validateValueTableOrder( measure : Measure,
                             orderedTables : list[str] ) -> None:
    for table in measure.valueTables:
        if table.order != ( orderedTables.index( table.apiName ) + 1 ):
            print( 'non-shared value tables are out of order' )
            return None
        

def validateSharedTableOrder( measure : Measure,
                              orderedTables : list[str] ) -> None:
    for table in measure.sharedTables:
        if table.order != ( orderedTables.index( table.version.version_string ) + 1 ):
            print( 'shared value tables are out of order' )
            return None
        

def checkParams( measure: Measure,
                 orderedParams: list[str] ) -> list[SharedParameter]:
    unknown: list[SharedParameter] = []
    for param in measure.params:
        if param.version.version_string not in orderedParams:
            unknown.append( param )

    for param in unknown:
        measure.params.remove( param )


def filterInterParams( measure : Measure,
                       orderedParams : list[str] ) -> list[str]:
    if not measure.containsParam( 'LightingType' ):
        orderedParams.remove( 'LightingType' )

    return orderedParams


def filterInterValueTables( measure : Measure,
                            orderedTables : list[str] ) -> list[str]:
    if not measure.containsValueTable( 'IEApplicability' ):
        orderedTables.remove( 'IEApplicability' )

    return orderedTables


def filterInterSharedTables( measure : Measure,
                             orderedTables : list[str] ) -> list[str]:
    if not measure.containsSharedTable( 'commercialInteractiveEffects' ):
        orderedTables.remove( 'commercialInteractiveEffects' )

    if not measure.containsSharedTable( 'residentialInteractiveEffects' ):
        orderedTables.remove( 'residentialInteractiveEffects' )

    return orderedTables

"""Return a three-tuple containing ordered lists with ty
        1.  (shared/non-shared)
        2. 
docstring
"""

def filter_list(target_list: list[str], )
def getOrderedListTuple(measure: Measure) -> tuple[list[str], list[str], list[str]]:
    orderedParams = list(ParameterNames.ALL_PARAMS.keys())
    orderedValTables = list(ValueTableNames.ALL_VALUE_TABLES.keys())
    orderedShaTables = list(ValueTableNames.ALL_SHARED_TABLES.keys())

    # TODO: add custom exception to measure type checking methods and handle it here
    if not measure.hasDEERVersion():
        orderedParams = list(
            filter(lambda param: ParameterNames.ALL_PARAMS[param] != 'DEER',
                   orderedParams))
        orderedValTables = list(
            filter(lambda table: ValueTableNames.ALL_VALUE_TABLES[table] != 'DEER',
                   orderedValTables))
        orderedShaTables = list(
            filter(lambda table: ValueTableNames.ALL_SHARED_TABLES[table] != 'DEER',
                   orderedShaTables))

    if not measure.isDefGSIAMeasure():
        orderedShaTables = list(
            filter(lambda table: ValueTableNames.ALL_SHARED_TABLES[table] != 'NGSIA',
                   orderedShaTables))
    else:
        orderedParams = list(
            filter(lambda param: ParameterNames.ALL_PARAMS[param] != 'NGSIA',
                   orderedParams))
        orderedShaTables = list(
            filter(lambda table: ValueTableNames.ALL_SHARED_TABLES[table] != 'GSIA',
                   orderedShaTables))

    if not measure.isAROrAOEMeasure():
        orderedParams = list( filter( lambda param: ParameterNames.ALL_PARAMS[param] != 'MAT', orderedParams ) )
        orderedShaTables = list( filter( lambda table : ValueTableNames.ALL_SHARED_TABLES[table] != 'ARAOE', orderedShaTables ) )
        orderedValTables = list( filter( lambda table : ValueTableNames.ALL_VALUE_TABLES[table] != 'NRNC+ARAOE', orderedValTables ) )
    
    if not measure.isNCOrNRMeasure:
        orderedValTables = list( filter( lambda table : ValueTableNames.ALL_VALUE_TABLES[table] != 'NRNC+ARAOE', orderedValTables ) )

    if not measure.isWENMeasure():
        orderedParams = list( filter( lambda param: ParameterNames.ALL_PARAMS[param] != 'WEN', orderedParams ) )
        orderedShaTables = list( filter( lambda table : ValueTableNames.ALL_SHARED_TABLES[table] != 'WEN', orderedShaTables ) )

    if measure.isSectorDefaultMeasure():
        orderedParams = list( filter( lambda param: ParameterNames.ALL_PARAMS[param] != 'NTG', orderedParams ) )

    if measure.isResDefaultMeasure():
        orderedShaTables = list( filter( lambda table : ValueTableNames.ALL_SHARED_TABLES[table] != 'RES-NDEF', orderedShaTables ) )
    else:
        orderedShaTables = list( filter( lambda table : ValueTableNames.ALL_SHARED_TABLES[table] != 'RES-DEF', orderedShaTables ) )

    if not measure.isDeemedDeliveryTypeMeasure():
        orderedValTables = list( filter( lambda table : ValueTableNames.ALL_VALUE_TABLES[table] != 'DEEM', orderedValTables ) )

    if not measure.isFuelSubMeasure():
        orderedValTables = list( filter( lambda table : ValueTableNames.ALL_VALUE_TABLES[table] != 'FUEL', orderedValTables ) )

    if not measure.isInteractiveMeasure():
        orderedParams = list( filter( lambda param: ParameterNames.ALL_PARAMS[param] != 'INTER', orderedParams ) )
        orderedShaTables = list( filter( lambda table : ValueTableNames.ALL_SHARED_TABLES[table] != 'INTER', orderedShaTables ) )
        orderedValTables = list( filter( lambda table : ValueTableNames.ALL_VALUE_TABLES[table] != 'INTER', orderedValTables ) )
    else:
        orderedParams = filterInterParams( measure, orderedParams )
        orderedShaTables = filterInterSharedTables( measure, orderedShaTables )
        orderedValTables = filterInterValueTables( measure, orderedValTables )

    return ( orderedParams, orderedValTables, orderedShaTables )


# Parameters:
#   @measure - a JSON file that represents a given measure
#
# Parses a given JSON file that outlines a given measure
# Parsing Specifications:
#   - Existence of required parameters and value tables (shared and non-shared)
#   - Correct order of parameters
#   - Correct order of value tables
def parseMeasure( measure: Measure ) -> None:
    defineMeasureTypes( measure )
    ( orderedParams, orderedValTables, orderedShaTables ) = getOrderedListTuple( measure )

    print( '\nParams:' )
    print( orderedParams )
    print( '\nValue Tables:' )
    print( orderedValTables )
    print( '\nShared Tables:' )
    print( orderedShaTables )

    print( '\nUnknown Parameters/Tables:' )
    unkownParams = measure.removeUnknownParams( orderedParams )
    print( '    Params: ', list( map( lambda param: param.version.version_string, unkownParams ) ) )
    unknownValTables = measure.removeUnkownValueTables( orderedValTables )
    print( '    Non-Shared Value Tables: ', list( map( lambda table: table.apiName, unknownValTables ) ) )
    unknownShaTables = measure.removeUnkownSharedTables( orderedShaTables )
    print( '    Shared Value Tables: ', list( map( lambda table: table.version.version_string, unknownShaTables ) ) )

    print( '\nMissing Parameters/Tables:' )
    validateParamExistence( measure, orderedParams )
    validateValueTableExistence( measure, orderedValTables )
    validateSharedTableExistence( measure, orderedShaTables )

    print( '\nParameter/Table order:' )
    validateParamOrder( measure, orderedParams )
    validateValueTableOrder( measure, orderedValTables )
    validateSharedTableOrder( measure, orderedShaTables )


# Parameters:
#   @filename - the name of a JSON measure file to be parsed
def main( filename: str ) -> None:
    print( f'\nstarting to parse measure file - {filename}\n' )
    try:
        measureFile = open( filename, 'r' )
    except OSError:
        print( f'ERROR: couldn\'t open file - {filename}' )
        return None
    
    try:
        parseMeasure( Measure( json.loads( measureFile.read(), object_hook=lambda d: Namespace(**d) ) ) )
    except OSError:
        print( f'ERROR: couldn\'t read file - {filename}' )
    finally:
        measureFile.close()
        
    
    with open( filename, 'r' ) as measureFile, \
         open(  )
    
    
    print( f'\nfinished parsing measure file - {filename}' )


if __name__ == '__main__':
    main( sys.argv[1] )