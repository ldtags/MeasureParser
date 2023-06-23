import json, sys
import ParameterNames, ValueTableNames
from MeasureObjects import SharedParameter, ValueTable, SharedValueTable


# Parameters:
#   @param - a JSON object that represents a measure parameter
#
# returns a SharedParameter object built from the representation in @param
#   returns None if any fields are missing or empty
def buildSharedParameter( param ) -> SharedParameter:
    try:
        order = param['order']
        version = param['version']['version_string']
        labels = param['active_labels']
    except:
        print( f'shared parameter missing required field(s) \n\t {param}' )
        return None
    
    if ( order == None or version == None or labels == None ):
        print( f'shared parameter missing required data \
              \n\t order: {order}\n\t version: {version}\n\t active labels: {labels}' )
        return None

    try:
        version = version.split('-')[0]
    except:
        print( f'version string incorrectly formatted - {version}' )
        return None

    return SharedParameter( order, version, labels )


# Parameters:
#   @measure - a JSON file that represents a given measure
#
# returns a dict mapping all measure params in @measure to their respective name
#   returns None if there is no 'shared_determinant_refs' field
#       or if no measure parameters are found
def getSharedParameters( measure ) -> dict[str, SharedParameter]:
    try:
        sharedRefs = measure['shared_determinant_refs']
    except:
        print( 'shared_determinant_refs not found' )
        return None

    if sharedRefs == None:
        print( 'shared_determinant_refs is empty' )
        return None
    
    paramDict = {}
    params = list( map( lambda param: buildSharedParameter( param ), sharedRefs ) )
    for param in params:
        paramDict[param.version] = param
    return paramDict


# Parameters:
#   @table - a JSON object that represents a value table
#
# returns a ValueTable object built from the representation in @table
#   returns None if any fields are missing
def buildValueTable( table ) -> ValueTable:
    try:
        name = table['name']
        apiName = table['api_name']
        tableType = table['type']
        description = table['description']
        order = table['order']
        determinants = table['determinants']
        columns = table['columns']
        values = table['values']
        refs = table['reference_refs']
    except:
        print( 'table is missing required fields' )
        return None

    if ( name == None or apiName == None or tableType == None
            or order == None or determinants == None
            or columns == None or values == None or refs == None ):
        print( f'value table missing required data \
               \n\t name: {name}\n\t api name: {apiName}\n\t type: {tableType} \
               \n\t description: {description}\n\t order: {order} \
               \n\t determinants: {determinants} \n\t columns: {columns} \
               \n\t values: {values}\n\t refs: {refs}' )
        
    return ValueTable( name, apiName, tableType, description,
                       order, determinants, columns, values, refs )


# Parameters:
#   @measure - a JSON file that represents a given measure
#
# returns a dict mapping all value tables in @measure to their respective api_name
#   returns None if there is no 'value_tables' field or if no value tables are found
def getValueTables( measure ) -> dict[str, ValueTable]:
    try:
        tables = measure['value_tables']
    except:
        print( 'value_tables not found' )
        return None

    if tables == None:
        print( 'value_tables is empty' )
        return None
    
    tableDict = {}
    tables = list( map( lambda table: buildValueTable( table ), tables ) )
    for table in tables:
        tableDict[table.apiName] = table
    return tableDict


def buildSharedTable( table ) -> SharedValueTable:
    try:
        order = table['order']
        version = table['version']['version_string']
    except:
        print( 'shared table is missing required fields' )
        return None
    
    if ( order == None or version == None ):
        print( f'shared parameter missing required data \
              \n\t order: {order}\n\t version: {version}' )
        return None
    
    try:
        version = version.split('-')[0]
    except:
        print( f'version string incorrectly formatted - {version}' )
        return None
    
    return SharedValueTable( order, version )


def getSharedTables( measure ) -> dict[str, SharedValueTable]:
    try:
        tables = measure['shared_lookup_refs']
    except:
        print( 'shared_lookup_refs not found' )
        return None
    
    tableDict = {}
    tables = list( map( lambda table: buildSharedTable( table ), tables ) )
    for table in tables:
        tableDict[table.version] = table
    return tableDict


# Parameters:
#   @params - a dict mapping all measure parameters to their respective names
#
# checks the labels of the version param to determine if the
#   measure is a DEER measure
#
# returns true if the measure is a DEER measure
#   otherwise returns false
def isDeerMeasure( params : dict[str, SharedParameter] ) -> bool:
    try:
        version = params['version']
    except:
        print( 'measure is incorrectly formatted' )
        return False

    for label in version.labels:
        if 'DEER' in label:
            return True

    return False


# Parameters:
#   @params - a dict mapping all measure parameters to their respective names
#
# checks the labels of the MeasAppType param to determine
#   if the measure application type is AOE or AR
#
# returns true if the measure application type is AOE or AR
#   otherwise returns false
def isAROrAOEMeasure( params : dict[str, SharedParameter] ) -> bool:
    try:
        version = params['MeasAppType']
    except:
        print( 'measure is incorrectly formatted' )
        return False
    
    for label in version.labels:
        if 'AOE' in label or 'AR' in label:
            return True

    return False


# Parameters:
#   @params - a dict mapping all measure parameters to their respective names
#
# checks the labels of the MeasAppType param to determine
#   if the measure application type is NC or NR
#
# returns true if the measure application type is NC or NR
#   otherwise returns false
def isNCOrNRMeasure( params : dict[str, SharedParameter] ) -> bool:
    try:
        version = params['MeasAppType']
    except:
        print( 'measure is incorrectly formatted' )
        return False
    
    for label in version.labels:
        if 'NC' in label or 'NR' in label:
            return True

    return False


# Parameters:
#   @params - a dict mapping all measure parameters to their respective names
#
# checks the label of the GSIAID param to determine if the measure
#   is a default GSIA measure
#
# returns true if the measure is a default GSIA measure
#   otherwise returns false
def isDefGSIAMeasure( params : dict[str, SharedParameter] ) -> bool:
    try:
        version = params['GSIAID']
    except:
        print( 'measure is incorrectly formatted' )
        return False
    
    for label in version.labels:
        if 'Def-GSIA' in label:
            return True

    return False


# Parameters:
#   @params - a dict mapping all measure parameters to their respective names
#
# checks the labels of the NTGID param to determine if the Net to Gross ID
#   contains the default for each sector
#
# returns true if any of the param-specific sector defaults are in the NTGID labels
#   otherwise returns false
def isSectorDefaultMeasure( params : dict[str, SharedParameter] ) -> bool:
    try:
        sectors = list( map( lambda sector : sector + '-Default', params['Sector'].labels ) )
        ntgIds = params['NTGID'].labels
    except:
        print( 'measure is incorrectly formatted' )
        return False
    
    for sector in sectors:
        for ntgId in ntgIds:
            if sector in ntgId:
                return True

    return False


def isFuelSubMeasure( params : dict[str, SharedParameter] ) -> bool:
    try:
        measImpctType = params['MeasImpactType']
    except:
        print( 'measure is incorrectly formatted' )
        return False
    
    for label in measImpctType.labels:
        if 'FuelSub' in label:
            return True

    return False


def isWENMeasure( params : dict[str, SharedParameter],
                  sharedTables : dict[str, SharedValueTable] ) -> bool:
    try:
        wenParam = params['waterEnergyIntensity']
        wenTable = sharedTables['waterEnergyIntensity']
    except:
        if wenParam ^ wenTable:
            print( 'WEN measure detected but required data is missing - ' \
                + ('Water Energy Intensity Parameter' if wenTable \
                    else 'Water Energy Intensity Value Table') )
        return False

    return True


def isInteractiveMeasure( params : dict[str, SharedParameter],
                          tables : dict[str, ValueTable],
                          sharedTables : dict[str, SharedValueTable] ) -> bool:
    try:
        lightingType = params['lightingType']
    except:
        lightingType = None

    try:
        interactiveEffctApp = tables['IEApplicability']
    except:
        interactiveEffctApp = None

    try:
        commercialEffects = sharedTables['commercialInteractiveEffects']
    except:
        commercialEffects = None

    try:
        residentialEffects = sharedTables['residentialInteractiveEffects']
    except:
        residentialEffects = None

    if lightingType ^ ( commercialEffects or residentialEffects or interactiveEffctApp ):
        print( 'Measure is incorrectly formatted, missing required interactive effect data'  )

    return lightingType and ( commercialEffects or residentialEffects )


# Parameters:
#   @params - a dict mapping all measure parameters to their respective names
#
# checks the labels of the DelivType param to determine if either
#   DnDeemDI is in the labels or DnDeemed and UpDeemed are in the labels
#
# returns true if any of the labels are found
#   otherwise returns false
def isDeemedDeliveryTypeMeasure( params : dict[str, SharedParameter] ) -> bool:
    try:
        deliveryType = params['DelivType']
    except:
        print( 'measure is incorrectly formatted' )
        return False
    
    return 'DnDeemDI' in deliveryType.labels \
        or ( 'DnDeemed' in deliveryType.labels and 'UpDeemed' in deliveryType.labels )


# Parameters:
#   @sharedParams - a dict mapping all measure parameters to their respective names
#
# Returns a list of all parameters associated with the measure
def getAllParams( sharedParams : dict[str, SharedParameter],
                  sharedTables : dict[str, SharedValueTable] ) -> dict[str, str]:
    orderedParams = ParameterNames.ALL_PARAMS

    if not isDeerMeasure( sharedParams ):
        orderedParams = list( filter( lambda param: ParameterNames.ALL_PARAMS[param] != 'DEER', orderedParams ) )

    if not isAROrAOEMeasure( sharedParams ):
        orderedParams = list( filter( lambda param: ParameterNames.ALL_PARAMS[param] != 'MAT', orderedParams ) )

    if isDefGSIAMeasure( sharedParams ):
        orderedParams = list( filter( lambda param: ParameterNames.ALL_PARAMS[param] != 'NGSIA', orderedParams ) )

    if isSectorDefaultMeasure( sharedParams ):
        orderedParams = list( filter( lambda param: ParameterNames.ALL_PARAMS[param] != 'NTG', orderedParams ) )

    if not isWENMeasure( sharedParams, sharedTables ):
        orderedParams = list( filter( lambda param: ParameterNames.ALL_PARAMS[param] != 'WEN', orderedParams ) )

    if not isInteractiveMeasure(  ):
        orderedParams = list( filter( lambda param : ParameterNames.ALL_PARAMS[param] != 'INTER', orderedParams ) )

    return orderedParams


# defines the type of measure that the given measure satisfies
# returns nothing and does not modify any data, use for debugging
def defineMeasureTypes( sharedParams : dict[str, SharedParameter],
                        sharedTables : dict[str, SharedValueTable] ) -> None:
    if isDeerMeasure( sharedParams ):
        print( 'is DEER measure' )

    if isAROrAOEMeasure( sharedParams ):
        print( 'MAT = AR and/or AOE' )

    if isNCOrNRMeasure( sharedParams ):
        print( 'MAT = NC and/or NR' )

    if isDefGSIAMeasure( sharedParams ):
        print( 'is a default GSIA measure' )

    if isSectorDefaultMeasure( sharedParams ):
        print( 'is a sector default measure' )

    if isDeemedDeliveryTypeMeasure( sharedParams ):
        print( 'is a deemed delivery type measure' )

    if isWENMeasure( sharedParams, sharedTables ):
        print( 'is a WEN measure' )

    if isInteractiveMeasure(  ):
        print( 'is an interactive measure' )

    if isFuelSubMeasure( sharedParams ):
        print( 'is fuel substitution measure' )


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


def removeOrderedSubsets( params : list[SharedParameter],
                          orderedParams : list[str] ) -> list[SharedParameter]:
    ordered : list[SharedParameter] = []
    for i in range( 0, len( params ) - 1 ):
        nxt = params[i + 1]
        if nxt.version in orderedParams and orderedParams.index( params[i].version ) + 1 == orderedParams.index( nxt.version ):
            if params[i] not in ordered:
                ordered.append( params[i] )
                ordered.append( nxt )

    for param in ordered:
        params.remove( param )
    return params


def removeByPlacement( params : list[SharedParameter],
                       orderedParams : list[str] ) -> list[SharedParameter]:
    unordered : list[SharedParameter] = []
    for param in params:
        if param.version in orderedParams and param.order - len( unordered ) != orderedParams.index( param.version ):
            unordered.append( param )
    return unordered


def validateParamOrder( sharedParams : dict[str, SharedParameter],
                        orderedParams : list[str] ) -> None:
    params : list[SharedParameter] = removeOrderedSubsets( list( sharedParams.values() ), orderedParams )
    params = removeByPlacement( params, orderedParams )
    for param in params:
        print( f'PARAMETER OUT OF ORDER - {param.version}' )


# Parameters:
#   @measure - a JSON file that represents a given measure
#
# Parses a given JSON file that outlines a given measure
# Parsing Specifications:
#   - Existence of required parameters and value tables (shared and non-shared)
#   - Correct order of parameters
#   - Correct order of value tables
def parseMeasure( measure ) -> None:
    sharedParams : dict[str, SharedParameter] = getSharedParameters( measure )
    orderedParams : dict[str, str] = getAllParams( sharedParams )
    valueTables : dict[str, ValueTable] = getValueTables( measure )
    sharedTables : dict[str, SharedValueTable] = getSharedTables( measure )
    defineMeasureTypes( sharedParams )
    print('\n')
    validateParamExistence( sharedParams, orderedParams )
    validateParamOrder( sharedParams, orderedParams )


# Parameters:
#   @filename - the name of a JSON measure file to be parsed
def main( filename : str ) -> None:
    print( f'\nparsing through measure file - {filename}\n' )
    try:
        measureFile = open( filename, 'r' )
    except:
        print( f'ERROR: couldn\'t open file - {filename}' )
        return None
    parseMeasure( json.load( measureFile ) )
    print( f'\nfinished parsing through measure file - {filename}' )


if __name__ == '__main__':
    main( sys.argv[1] )