class Version:
    def __init__( self, version_string : str ):
        self.version_string = version_string

class SharedParameter:
    def __init__( self, param ):
        try:
            self.order : int = param.order
            self.version : Version = param.version
            self.labels : list[str] = param.active_labels
        except Exception as err:
            print( f'parameter missing required fields - {err}' )

class ValueTable:
    def __init__( self, valueTable ):
        try:
            self.name : str = valueTable.name
            self.apiName : str = valueTable.api_name
            self.type : str = valueTable.type
            self.description : str = valueTable.description
            self.order : int = valueTable.order
            self.determinants : list = valueTable.determinants
            self.columns : list = valueTable.columns
            self.values : list[str] = valueTable.values
            self.refs : list = valueTable.reference_refs
        except Exception as err:
            print( f'value table missing required fields - {err}' )

class SharedValueTable:
    def __init__( self, sharedTable ):
        try:
            self.order : int = sharedTable.order
            self.version : Version = sharedTable.version
        except Exception as err:
            print( f'shared value table missing required fields - {err}' )

class Measure:
    def __init__( self, measure ):
        try:
            self.owned_by_user : str = measure.owned_by_user
            self.params : list[SharedParameter] = list( map( lambda param : SharedParameter( param ), measure.shared_determinant_refs ) )
            self.sharedTables : list[SharedValueTable] = list( map( lambda table : SharedValueTable( table ), measure.shared_lookup_refs ) )
            self.valueTables : list[ValueTable] = list( map( lambda table : ValueTable( table ), measure.value_tables ) )
        except Exception as err:
            print( f'measure missing required fields - {err}' )

    def containsParam( self, paramName : str ) -> bool:
        paramNames = map( lambda param : param.version.version_string.split( '-' )[0], self.params )
        return paramName in paramNames
    
    def getParam( self, paramName : str ) -> SharedParameter:
        for param in self.params:
            if param.version.version_string.split( '-' )[0] == paramName:
                return param
        return None
    
    def containsTable( self, tableName : str ) -> bool:
        sharedTables = map( lambda table : table.version.version_string.split( '-' )[0], self.sharedTables )
        valueTables = map( lambda table : table.apiName, self.valueTables )
        return tableName in sharedTables or tableName in valueTables
    
    def getValueTable( self, tableName : str ) -> ValueTable:
        for table in self.valueTables:
            if table.apiName == tableName:
                return table
        return None
    
    def getSharedTable( self, tableName : str ) -> SharedValueTable:
        for table in self.sharedTables:
            if table.version.version_string.split( '-' )[0] == tableName:
                return table
        return None
    

    # Parameters:
    #   @params - a dict mapping all measure parameters to their respective names
    #
    # checks the labels of the version param to determine if the
    #   measure is a DEER measure
    #
    # returns true if the measure is a DEER measure
    #   otherwise returns false
    def isDeerMeasure( self ) -> bool:
        version = self.getParam( 'version' )
        if version == None:
            print( 'measure is missing the version parameter' )
            return False

        for label in version.labels:
            if 'DEER' in label:
                return True

        return False
    

    def isWENMeasure( self ) -> bool:
        wenParam = self.getParam( 'waterMeasureType' )
        wenTable = self.getSharedTable( 'waterEnergyIntensity' )
        if wenParam == None or wenTable == None:
            if ( wenParam == None ) ^ ( wenTable == None ):
                print( 'WEN measure detected but required data is missing - ' \
                    + ('Water Energy Intensity Parameter' if wenTable \
                        else 'Water Energy Intensity Value Table') )
            return False
        return True


    # Parameters:
    #   @params - a dict mapping all measure parameters to their respective names
    #
    # checks the labels of the DelivType param to determine if either
    #   DnDeemDI is in the labels or DnDeemed and UpDeemed are in the labels
    #
    # returns true if any of the labels are found
    #   otherwise returns false
    def isDeemedDeliveryTypeMeasure( self ) -> bool:
        deliveryType = self.getParam( 'DelivType' )
        if deliveryType == None:
            print( 'measure is incorrectly formatted' )
            return False

        return 'DnDeemDI' in deliveryType.labels \
            or ( 'DnDeemed' in deliveryType.labels and 'UpDeemed' in deliveryType.labels )
    

    def isFuelSubMeasure( self ) -> bool:
        measImpctType = self.getParam( 'MeasImpactType' )
        if measImpctType == None:
            print( 'measure is missing the MeasImpactType parameter' )
            return False
            
        for label in measImpctType.labels:
            if 'FuelSub' in label:
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
    def isSectorDefaultMeasure( self ) -> bool:
        sector = self.getParam( 'Sector' )
        ntgId = self.getParam( 'NTGID' )
        if sector == None or ntgId == None:
            print( 'measure is missing required parameters' )
            return False

        sectors = list( map( lambda sector : sector + '-Default', sector.labels ) )
        for sector in sectors:
            for id in ntgId.labels:
                if sector in id:
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
    def isDefGSIAMeasure( self ) -> bool:
        version = self.getParam( 'GSIAID' )
        if version == None:
            print( 'measure is missing the GSIAID parameter' )
            return False

        for label in version.labels:
            if 'Def-GSIA' in label:
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
    def isAROrAOEMeasure( self ) -> bool:
        version = self.getParam( 'MeasAppType' )
        if version == None:
            print( 'measure is missing the MeasAppType parameter' )
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
    def isNCOrNRMeasure( self ) -> bool:
        version = self.getParam( 'MeasAppType' )
        if version == None:
            print( 'measure is missing the MeasAppType parameter' )
            return False

        for label in version.labels:
            if 'NC' in label or 'NR' in label:
                return True

        return False
    

    def isInteractiveMeasure( self ) -> bool:
        lightingType = self.getParam( 'LightingType' )
        interactiveEffctApp = self.getValueTable( 'IEApplicability' )
        commercialEffects = self.getSharedTable( 'commercialInteractiveEffects' )
        residentialEffects = self.getSharedTable( 'residentialInteractiveEffects' )

        if lightingType and ( commercialEffects or residentialEffects ):
            return True
        elif lightingType or ( commercialEffects or residentialEffects ) or interactiveEffctApp:
            print( 'Measure is incorrectly formatted, missing required interactive effect data' )

        return False