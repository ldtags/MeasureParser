class SharedParameter:
    def __init__( self, order : int, version : str, labels : list[str] ):
        self.order : int = order
        self.version : str = version
        self.labels : list[str] = labels

class ValueTable:
    def __init__( self, name : str, apiName : str, type : str, description : str, order : int, determinants : list, columns : list, values : list[str], refs : list ):
        self.name : str = name
        self.apiName : str = apiName
        self.type : str = type
        self.description : str = description
        self.order : int = order
        self.determinants : list = determinants
        self.columns : list = columns
        self.values : list[str] = values
        self.refs : list = refs

class SharedValueTable:
    def __init__( self, order : int, version : str ):
        self.order : int = order
        self.version : str = version

class Measure:
    def __init__( self, measure ):
        try:
            self.owner = measure['owned_by_user']
            self.determinants = measure['determinants']
            self.sharedDeterminants = measure['shared_determinant_refs']
            self.sharedLookup = measure['shared_lookup_refs']
            self.valueTables = measure['value_tables']
            self.calculations = measure['calculations']
            self.exclusionTables = measure['exclusion_tables']
            self.dsAdditionalFields = measure['ds_additional_fields']
            self.users = measure['users']
            self.references = measure['references']
            self.id = measure['MeasureID']
            self.versionID = measure['MeasureVersionID']
            self.name = measure['MeasureName']
            self.useCategory = measure['UseCategory']
            self.paLead = measure['PALead']
            self.startDate = measure['StartDate']
            self.endDate = measure['EndDate']
            self.status = measure['Status']
            self.packageCoverSheetFile = measure['MeasurePackageCoverSheetFile']
            self.characterizationSourceFile = measure['CharacterizationSourceFile']
            self.techSummary = measure['TechnologySummary']
            self.caseDescription = measure['MeasureCaseDescription']
            self.baseCaseDescription = measure['BaseCaseDescription']
            self.codeRequirements = measure['CodeRequirements']
            self.programRequirements = measure['ProgramRequirements']
            self.programExclusions = measure['ProgramExclusions']
            self.dataCollectionRequirements = measure['DataCollectionRequirements']
            self.electricSavings = measure['ElectricSavings_kWh']
            self.peakElectricDemandReduction = measure['PeakElectricDemandReduction_kW']
            self.gasSavings = measure['GasSavings_Therms']
            self.lifecycle = measure['LifeCycle']
            self.baseCaseMaterialCost = measure['BaseCaseMaterialCost_DollarPerUnit']
            self.measureCaseMaterialCost = measure['MeasureCaseMaterialCost_DollarPerUnit']
            self.baseCaseLaborCost = measure['BaseCaseLaborCost_DollarPerUnit']
            self.measureCaseLaborCost = measure['MeasureCaseLaborCost_DollarPerUnit']
            self.netToGross = measure['NetToGross']
            self.grossSavingsInstallationAdjustment = measure['GrossSavingsInstallationAdjustment']
            self.nonEnergyImpacts = measure['NonEnergyImpacts']
            self.deerDifferencesAnalysis = measure['DEERDifferencesAnalysis']
            self.offeringID = measure['OfferingID']
            self.baseCaseFirst = measure['BaseCase1st']
            self.baseCaseSecond = measure['BaseCase2nd']
            self.description = measure['MeasDescription']
            self.preDesc = measure['PreDesc']
            self.stdDesc = measure['StdDesc']
            self.appType = measure['MeasAppType']
            self.bldgType = measure['BldgType']
            self.bldgVint = measure['BldgVint']
            self.bldgLoc = measure['BldgLoc']
            self.normUnit = measure['NormUnit']
            self.sector = measure['Sector']
            self.paType = measure['PAType']
            self.pa = measure['PA']
            self.unitKwFirstBaseline = measure['UnitkW1stBaseline']
            self.unitKwHFirstBaseline = measure['UnitkWh1stBaseline']
            self.unitThermFirstBaseline = measure['UnitTherm1stBaseline']
            self.unitKwSecondBaseline = measure['UnitkW2ndBaseline']
            self.unitKwHSecondBaseline = measure['UnitkWh2ndBaseline']
            self.unitThermSecondBaseline = measure['UnitTherm2ndBaseline']
            self.unitLabCostFirstBaseline = measure['UnitLabCost1stBaseline']
            self.unitMatCostFirstBaseline = measure['UnitMatCost1stBaseline']
            self.unitMeasureCostFirstBaseline = measure['UnitMeaCost1stBaseline']
            self.unitMeasureLabCost = measure['UnitMeasLabCost']
            self.unitMeasureMaterialCost = measure['UnitMeasMatCost']
            self.unitLabCostSecondBaseline = measure['UnitLabCost2ndBaseline']
            self.unitMatCostSecondBaseline = measure['UnitMatCost2ndBaseline']
            self.unitMeasureCostSecondBaseline = measure['UnitMeaCost2ndBaseline']
            self.locCostAdj = measure['LocCostAdj']
            self.eulId = measure['EUL_ID']
            self.eulYrs = measure['EUL_Yrs']
            self.rulId = measure['RUL_ID']
            self.rulYrs = measure['RUL_Yrs']
            self.lifeFirstBaseline = measure['Life1stBaseline']
            self.lifeSecondBaseline = measure['Life2ndBaseline']
            self.uecKwBaseOne = measure['UECkWBase1']
            self.uecKwHBaseOne = measure['UECkWhBase1']
            self.uecThermBaseOne = measure['UECThermBase1']
            self.uecKwBaseTwo = measure['UECkWBase2']
            self.uecKwHBaseTwo = measure['UECkWhBase2']
            self.uecThermBaseTwo = measure['UECThermBase2']
            self.uecKwMeasure = measure['UECkWMeas']
            self.uecKwHMeasure = measure['UECkWhMeas']
            self.uecThermMeasure = measure['UECThermMeas']
            self.deliveryType = measure['DeliveryType']
            self.ntgId = measure['NTG_ID']

        except:
            print( 'measure missing required information' )