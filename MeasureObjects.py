from MeasureExceptions import (
    RequiredParameterError,
    VersionFormatError,
    ParameterFormatError,
    ValueTableFormatError,
    SharedTableFormatError,
    MeasureFormatError
)

try:
    from types import SimpleNamespace as Namespace
except ImportError:
    from argparse import Namespace

class Version:
    def __init__(self, version):
        try:
            if version.version_string.index('-') != -1:
                self.version_string = version.version_string.split('-')[0]
            else:
                self.version_string = version.version_string
        except:
            raise VersionFormatError()

class SharedParameter:
    def __init__(self, param):
        try:
            self.order: int = param.order
            self.version: Version = Version(param.version)
            self.labels: list[str] = param.active_labels
        except:
            raise ParameterFormatError()

class ValueTable:
    def __init__(self, valueTable):
        try:
            self.name: str = valueTable.name
            self.apiName: str = valueTable.api_name
            self.type: str = valueTable.type
            self.description: str = valueTable.description
            self.order: int = valueTable.order
            self.determinants: list = valueTable.determinants
            self.columns: list = valueTable.columns
            self.values: list[str] = valueTable.values
            self.refs: list = valueTable.reference_refs
        except:
            raise ValueTableFormatError()

class SharedValueTable:
    def __init__(self, sharedTable):
        try:
            self.order: int = sharedTable.order
            self.version: Version = Version(sharedTable.version)
        except:
            raise SharedTableFormatError()

class Measure:
    def __init__(self, measure):
        try:
            self.owner: str = measure.owned_by_user
            self.params: list[SharedParameter] = list(
                map(lambda param: SharedParameter(param),
                    measure.shared_determinant_refs))
            self.sharedTables: list[SharedValueTable] = list(
                map(lambda table: SharedValueTable(table),
                    measure.shared_lookup_refs))
            self.valueTables: list[ValueTable] = list(
                map(lambda table: ValueTable(table),
                    measure.value_tables))
        except:
            raise MeasureFormatError()

    def containsParam(self, paramName: str) -> bool:
        paramNames = map(lambda param: param.version.version_string,
                         self.params)
        return paramName in paramNames
    
    def getParam(self, paramName : str) -> SharedParameter:
        for param in self.params:
            if param.version.version_string == paramName:
                return param
        return None
    
    def removeUnknownParams(self,
                            paramNames : list[str]
                           ) -> list[SharedParameter]:
        unkownParams: list[SharedParameter] = []
        for param in self.params:
            if param.version.version_string not in paramNames:
                unkownParams.append(param)

        for param in unkownParams:
            self.params.remove(param)

        for i in range(0, len(self.params)):
            self.params[i].order = i + 1

        return unkownParams
    
    def containsValueTable(self, tableName: str) -> bool:
        valueTables = map(lambda table: table.apiName, self.valueTables)
        return tableName in valueTables
    
    def getValueTable(self, tableName: str) -> ValueTable:
        for table in self.valueTables:
            if table.apiName == tableName:
                return table
        return None
    
    def removeUnkownValueTables(self,
                                tableNames : list[str]
                               ) -> list[ValueTable]:
        unkownTables : list[ValueTable] = []
        for table in self.valueTables:
            if table.apiName not in tableNames:
                unkownTables.append(table)

        for table in unkownTables:
            self.valueTables.remove(table)

        for i in range(0, len(self.valueTables)):
            self.valueTables[i].order = i + 1

        return unkownTables
    
    def containsSharedTable(self, tableName : str) -> bool:
        sharedTables = map(lambda table: table.version.version_string,
                           self.sharedTables)
        return tableName in sharedTables
    
    def getSharedTable(self, tableName : str) -> SharedValueTable:
        for table in self.sharedTables:
            if table.version.version_string == tableName:
                return table
        return None
    
    def removeUnkownSharedTables(self,
                                 tableNames : list[str]
                                ) -> list[SharedValueTable]:
        unkownTables: list[SharedValueTable] = []
        for table in self.sharedTables:
            if table.version.version_string not in tableNames:
                unkownTables.append(table)

        for table in unkownTables:
            self.sharedTables.remove(table)

        for i in range(0, len(self.sharedTables)):
            self.sharedTables[i].order = i + 1

        return unkownTables

    # Parameters:
    #   @params - a dict mapping all measure parameters to their
    #       respective names
    #
    # checks the labels of the version param to determine if the
    #   measure is a DEER measure
    #
    # returns true if the measure is a DEER measure
    #   otherwise returns false
    def hasDEERVersion(self) -> bool:
        version = self.getParam('version')
        if version == None:
            raise RequiredParameterError(name='Version')

        for label in version.labels:
            if 'DEER' in label:
                return True

        return False
    

    def isWENMeasure(self) -> bool:
        wenParam = self.getParam('waterMeasureType')
        wenTable = self.getSharedTable('waterEnergyIntensity')
        if wenParam == None or wenTable == None:
            if (wenParam == None) ^ (wenTable == None):
                raise Exception(
                    'WEN measure detected but required data is missing - ' \
                    + ('Water Energy Intensity Parameter' if wenTable \
                       else 'Water Energy Intensity Value Table'))
            return False
        return True


    # Parameters:
    #   @params - a dict mapping all measure parameters to their
    #       respective names
    #
    # checks the labels of the DelivType param to determine if either
    #   DnDeemDI is in the labels or DnDeemed and UpDeemed are in the
    #   labels
    #
    # returns true if any of the labels are found
    #   otherwise returns false
    def isDeemedDeliveryTypeMeasure(self) -> bool:
        deliveryType = self.getParam('DelivType')
        if deliveryType == None:
            raise RequiredParameterError(name='Delivery Type')

        return 'DnDeemDI' in deliveryType.labels \
            or ('DnDeemed' in deliveryType.labels
                and 'UpDeemed' in deliveryType.labels)
    

    def isFuelSubMeasure(self) -> bool:
        measImpctType = self.getParam('MeasImpactType')
        if measImpctType == None:
            raise RequiredParameterError(name='Measure Impact Type')
            
        for label in measImpctType.labels:
            if 'FuelSub' in label:
                return True

        return False
    

    # Parameters:
    #   @params - a dict mapping all measure parameters to their
    #       respective names
    #
    # checks the labels of the NTGID param to determine if the Net
    #   to Gross ID contains the default for each sector
    #
    # returns true if any of the param-specific sector defaults are
    #   in the NTGID labels, otherwise returns false
    def isSectorDefaultMeasure(self) -> bool:
        sector = self.getParam('Sector')
        if sector == None:
            raise RequiredParameterError(name='Sector')

        ntgId = self.getParam('NTGID')
        if ntgId == None:
            raise RequiredParameterError(name='Net to Gross Ratio ID')

        sectors = list(map(lambda sector: sector + '-Default',
                           sector.labels))
        for sector in sectors:
            for id in ntgId.labels:
                if sector in id:
                    return True

        return False
    

    def isResDefaultMeasure(self) -> bool:
        ntgId = self.getParam('NTGID')
        if ntgId == None:
            raise RequiredParameterError(name='Net to Gross Ratio ID')
        
        for id in ntgId.labels:
            if 'Res-Default>2' in id:
                return True
        return False
    

    # Parameters:
    #   @params - a dict mapping all measure parameters to their
    #       respective names
    #
    # checks the label of the GSIAID param to determine if the measure
    #   is a default GSIA measure
    #
    # returns true if the measure is a default GSIA measure
    #   otherwise returns false
    def isDefGSIAMeasure(self) -> bool:
        version = self.getParam('GSIAID')
        if version == None:
            raise RequiredParameterError(name='GSIA ID')

        for label in version.labels:
            if 'Def-GSIA' in label:
                return True

        return False
    

    # Parameters:
    #   @params - a dict mapping all measure parameters to their
    #       respective names
    #
    # checks the labels of the MeasAppType param to determine
    #   if the measure application type is AOE or AR
    #
    # returns true if the measure application type is AOE or AR
    #   otherwise returns false
    def isAROrAOEMeasure(self) -> bool:
        version = self.getParam('MeasAppType')
        if version == None:
            raise RequiredParameterError(name='Measure Application Type')

        for label in version.labels:
            if 'AOE' in label or 'AR' in label:
                return True

        return False


    # Parameters:
    #   @params - a dict mapping all measure parameters to their
    #       respective names
    #
    # checks the labels of the MeasAppType param to determine
    #   if the measure application type is NC or NR
    #
    # returns true if the measure application type is NC or NR
    #   otherwise returns false
    def isNCOrNRMeasure(self) -> bool:
        version = self.getParam('MeasAppType')
        if version == None:
            raise RequiredParameterError(name='Measure Application Type')

        for label in version.labels:
            if 'NC' in label or 'NR' in label:
                return True

        return False
    

    def isInteractiveMeasure(self) -> bool:
        lightingType = self.getParam('LightingType')
        interactiveEffctApp = self.getValueTable('IEApplicability')
        commercialEffects = self.getSharedTable(
            'commercialInteractiveEffects')
        residentialEffects = self.getSharedTable(
            'residentialInteractiveEffects')

        if lightingType and (commercialEffects or residentialEffects):
            return True
        elif (lightingType or (commercialEffects or residentialEffects)
              or interactiveEffctApp):
            raise MeasureFormatError(
                'Missing required information for interactive effects')

        return False