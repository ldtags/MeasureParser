import json, sys
import ParameterNames, ValueTableNames
from MeasureObjects import SharedParameter, ValueTable, SharedValueTable, Measure
try:
    from types import SimpleNamespace as Namespace
except ImportError:
    from argparse import Namespace


# defines the type of measure that the given measure satisfies
# returns nothing and does not modify any data, use for debugging
def defineMeasureTypes( measure : Measure ) -> None:
    if measure.isDeerMeasure():
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
        print( 'is interactive measure' )


def filterInterParams( params : dict[str, SharedParameter],
                       orderedParams : dict[str, str] ) -> dict[str, str]:
    try:
        params['LightingType']
    except:
        del orderedParams['LightingType']

    return orderedParams


def filterInterValueTables( tables : dict[str, ValueTable],
                            orderedTables : dict[str, str] ) -> dict[str, str]:
    try:
        tables['IEApplicability']
    except:
        del orderedTables['IEApplicability']

    return orderedTables


def filterInterSharedTables( tables : dict[str, SharedValueTable],
                             orderedTables : dict[str, str] ) -> dict[str, str]:
    try:
        tables['commercialInteractiveEffects']
    except:
        del orderedTables['commercialInteractiveEffects']

    try:
        tables['residentialInteractiveEffects']
    except:
        del orderedTables['residentialInteractiveEffects']

    return orderedTables


# Parameters:
#   @sharedTables - a dict mapping all value tables to their respective api_name
#   @tableNames - a list of table names to check the measures value tables against
#
# validates that all shared value tables represented in @tableNames are found in @sharedTables
def validateSharedTableExistence( sharedTables : dict[str, SharedValueTable],
                                  tableNames : list[str] ) -> None:
    for table in tableNames:
        if table not in sharedTables:
            print( f'MISSING SHARED TABLE - {table}' )


# Parameters:
#   @valueTables - a dict mapping all value tables to their respective api_name
#   @tableNames - a list of table names to check the measures value tables against
#
# validates that all value tables represented in @tableNames are found in @valueTables
def validateTableExistence( valueTables : dict[str, ValueTable],
                            tableNames : list[str] ) -> None:
    for table in tableNames:
        if table not in valueTables:
            print( f'MISSING TABLE - {table}' )


# Parameters:
#   @sharedParams - a dict mapping all measure parameters to their respective names
#   @paramNames - a list of parameter names to check the measure parameters against
#
# validates that all parameters represented in @paramNames are found in @sharedParams
def validateParamExistence( sharedParams : dict[str, SharedParameter],
                            paramNames : list[str] ) -> None:
    for param in paramNames:
        if param not in sharedParams:
            print( f'MISSING PARAM - {param}' )


def validateParamOrder( sharedParams : dict[str, SharedParameter],
                        orderedParams : list[str] ) -> None:
    params = list( sharedParams.values() )
    for param in params:
        if param.order != ( orderedParams.index( param.version ) + 1 ):
            print( 'parameters are out of order' )
            return None


def getOrderedLists( measure : Measure ) -> tuple[list[str], list[str], list[str]]:
    orderedParams = list( ParameterNames.ALL_PARAMS.keys() )
    orderedValTables = list( ValueTableNames.ALL_VALUE_TABLES.keys() )
    orderedShaTables = list( ValueTableNames.ALL_SHARED_TABLES.keys() )

    if not measure.isDeerMeasure():
        orderedParams = list( filter( lambda param: ParameterNames.ALL_PARAMS[param] != 'DEER', orderedParams ) )
        orderedValTables = list( filter( lambda table : ValueTableNames.ALL_VALUE_TABLES[table] != 'DEER', orderedValTables ) )
        orderedShaTables = list( filter( lambda table : ValueTableNames.ALL_SHARED_TABLES[table] != 'DEER', orderedShaTables ) )

    if measure.isDefGSIAMeasure():
        orderedParams = list( filter( lambda param: ParameterNames.ALL_PARAMS[param] != 'NGSIA', orderedParams ) )
        orderedShaTables = list( filter( lambda table : ValueTableNames.ALL_SHARED_TABLES[table] != 'NGSIA', orderedShaTables ) )
    else:
        orderedShaTables = list( filter( lambda table : ValueTableNames.ALL_SHARED_TABLES[table] != 'GSIA', orderedShaTables ) )

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
        orderedParams = filterInterParams(  )

    return orderedParams, orderedValTables, orderedShaTables


# Parameters:
#   @measure - a JSON file that represents a given measure
#
# Parses a given JSON file that outlines a given measure
# Parsing Specifications:
#   - Existence of required parameters and value tables (shared and non-shared)
#   - Correct order of parameters
#   - Correct order of value tables
def parseMeasure( measure : Measure ) -> None:
    defineMeasureTypes( measure.params, measure.sharedTables, measure.valueTables )
    orderedParams, orderedValTables, orderedShaTables = getOrderedLists( measure )
    print( '\nParams:' )
    print( orderedParams )
    print( '\nValue Tables:' )
    print( orderedValTables )
    print( '\nShared Tables:' )
    print( orderedShaTables )

    # validateParamExistence( params, orderedParams )
    # validateParamOrder( params, orderedParams )


# Parameters:
#   @filename - the name of a JSON measure file to be parsed
def main( filename : str ) -> None:
    print( f'\nparsing through measure file - {filename}\n' )
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
        print( f'\nfinished parsing through measure file - {filename}' )


if __name__ == '__main__':
    main( sys.argv[1] )