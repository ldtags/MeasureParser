ALL_PERMUTATIONS = {
    'OfferingID': {
        'verbose': 'Offering ID',
        'validity': 'offerId__ID'
    },
    'BaseCase1st': {
        'verbose': 'First Base Case Description',
        'validity': 'measOffer__descBase1'
    },
    'BaseCase2nd': {
        'verbose': 'Second Base Case',
        'validity': 'Null__Blank',
        'conditional': [('measOffer__descBase2', 'MAT-AR')]
    },
    'MeasDescription': {
        'verbose': 'Measure Case Description',
        'validity': 'measOffer__descMeas'
    },
    'PreDesc': {
        'verbose': 'Existing Description',
        'validity': 'description__Ex'
    },
    'StdDesc': {
        'verbose': 'Standard Description',
        'validity': 'description__Std'
    },
    'MeasAppType': {
        'verbose': 'Measure Application Type',
        'validity': 'p.MeasAppType__label'
    },
    'BldgType': {
        'verbose': 'Building Type',
        'validity': 'p.BldgType__label'
    },
    'BldgVint': {
        'verbose': 'Building Vintage',
        'validity': 'p.BldgVint__label'
    },
    'BldgLoc': {
        'verbose': 'Building Location',
        'validity': 'p.BldgLoc__label'
    },
    'NormUnit': {
        'verbose': 'Normalized Unit',
        'validity': 'p.NormUnit__label'
    },
    'Sector': {
        'verbose': 'Sector',
        'validity': 'p.Sector__label'
    },
    'PAType': {
        'verbose': 'Program Administrator Type',
        'validity': 'p.PAType__label'
    },
    'PA': {
        'verbose': 'Program Administrator',
        'validity': 'p.PA__label'
    },
    'UnitkW1stBaseline': {
        'verbose': 'First Baseline - Peak Electric Demand Reduction'
    },
    'UnitkWh1stBaseline': {
        'verbose': 'First Baseline - Electric Savings'
    },
    'UnitTherm1stBaseline': {
        'verbose': 'First Baseline - Gas Savings'
    },
    'UnitkW2ndBaseline': {
        'verbose': 'Second Baseline - Peak Electric Demand Reduction'
    },
    'UnitkWh2ndBaseline': {
        'verbose': 'Second Baseline - Electric Savings'
    },
    'UnitTherm2ndBaseline': {
        'verbose': 'Second Baseline - Gas Savings'
    },
    'UnitLabCost1stBaseline': {
        'verbose': 'First Baseline - Labor Cost'
    },
    'UnitMatCost1stBaseline': {
        'verbose': 'First Baseline - Material Cost'
    },
    'UnitMeaCost1stBaseline': {
        'verbose': 'Measure Total Cost 1st Baseline',
        'validity': 'incrCost'
    },
    'UnitMeasLabCost': {
        'verbose': 'Measure - Labor Cost'
    },
    'UnitMeasMatCost': {
        'verbose': 'Measure - Material Cost'
    },
    'UnitLabCost2ndBaseline': {
        'verbose': 'Second Baseline - Labor Cost'
    },
    'UnitMatCost2ndBaseline': {
        'verbose': 'Second Baseline - Material Cost'
    },
    'UnitMeaCost2ndBaseline': {
        'verbose': 'Measure Total Cost 2nd Baseline'
    },
    'LocCostAdj': {
        'verbose': 'Locational Cost Adjustment ID',
        'validity': 'p.CostAdjustType__label'
    },
    'EUL_ID': {
        'verbose': 'Effective Useful Life ID',
        'validity': 'p.EULID__label'
    },
    'EUL_Yrs': {
        'verbose': 'EUL Years'
    },
    'RUL_ID': {
        'verbose': 'RUL Years'
    },
    'Life1stBaseline': {
        'verbose': 'First Baseline - Life Cycle'
    },
    'Life2ndBaseline': {
        'verbose': 'Second Baseline - Life Cycle'
    },
    'UECkWBase1': {
        'verbose': 'First Baseline - UEC KW'
    },
    'UECkWhBase1': {
        'verbose': 'First Baseline - UEC KWH'
    },
    'UECThermBase1': {
        'verbose': 'First Baseline - UEC Therm'
    },
    'UECkWBase2': {
        'verbose': 'Second Baseline - UEC KW'
    },
    'UECkWhBase2': {
        'verbose': 'Second Baseline - UEC KWH'
    },
    'UECThermBase2': {
        'verbose': 'Second Baseline - UEC Therm'
    },
    'UECkWMeas': {
        'verbose': 'Measure UEC KW'
    },
    'UECkWhMeas': {
        'verbose': 'Measure UEC KWH'
    },
    'UECThermMeas': {
        'verbose': 'Measure UEC Therm'
    },
    'DeliveryType': {
        'verbose': 'Delivery Type',
        'validity': 'p.DelivType__label'
    },
    'NTG_ID': {
        'verbose': 'Net to Gross Ratio ID',
        'validity': 'p.NTGID__label'
    },
    'NTGRkWh': {
        'verbose': 'NTG KWH'
    },
    'NTGRkW': {
        'verbose': 'NTG KW'
    },
    'NTGRTherm': {
        'verbose': 'NTG Therms'
    },
    'NTGRCost': {
        'verbose': 'NTGR Cost'
    },
    'GSIA_ID': {
        'verbose': 'GSIA ID',
        'validity': 'p.GSIAID__label'
    },
    'GSIA': {
        'verbose': 'GSIA Value',
        'validity': 'GSIA_default__GSIA_value'
    },
    'E3MeaElecEndUseShape': {
        'verbose': 'Electric Impact Profile ID',
        'validity': 'p.electricImpactProfileID__label'
    },
    'E3GasSavProfile': {
        'verbose': 'Gas Impact Profile ID',
        'validity': 'p.GasImpactProfileID__label'
    },
    'UnitGasInfraBens': {
        'verbose': 'Unit Gas Infrastructure Benefits',
        'validity': 'Null__ZeroDollars'
    },
    'UnitRefrigCosts': {
        'verbose': 'Unit Refrigerant Costs'
    },
    'UnitRefrigBens': {
        'verbose': 'Unit Refrigerant Benefits'
    },
    'UnitMiscCosts': {
        'verbose': 'Unit Miscellaneous Costs',
        'validity': 'Null__ZeroDollars'
    },
    'MiscCostsDesc': {
        'verbose': 'Miscellaneous Cost Description',
        'validity': 'Null__Blank'
    },
    'UnitMiscBens': {
        'verbose': 'Unit Miscellaneous Benefits',
        'validity': 'Null__ZeroDollars'
    },
    'MiscBensDesc': {
        'verbose': 'Miscellaneous Benefits Description',
        'validity': 'Null__Blank'
    },
    'MarketEffectsBenefits': {
        'verbose': 'Market Effects Benefits',
        'validity': 'Null__BlankNumber'
    },
    'MarketEffectsCosts': {
        'verbose': 'Market Effects Costs',
        'validity': 'Null__BlankNumber'
    },
    'MeasInflation': {
        'verbose': 'Measure Inflation',
        'validity': 'Null__BlankNumber'
    },
    'CombustionType': {
        'verbose': 'Combustion Type',
        'validity': 'Null__Blank'
    },
    'MeasImpactCalcType': {
        'verbose': 'Measure Impact Calculation Type',
        'validity': 'p.MeasImpactCalcType__label'
    },
    'Upstream_Flag': {
        'verbose': 'Upstream Flag (True / False)',
        'validity': 'Null__false',
        'conditional': [('upstreamFlag__upstreamFlag', 'DVY-UD')]
    },
    'Version': {
        'verbose': 'Version',
        'validity': 'p.version__label'
    },
    'VersionSource': {
        'verbose': 'Version Source'
    },
    'WaterUse': {
        'verbose': 'Water Measure Type',
        'validity': 'Null__Blank',
        'conditional': [('p.waterMeasureType__label', 'WMT')]
    },
    'UnitGalWater1stBaseline': {
        'verbose': 'First Baseline - Water Savings'
    },
    'UnitGalWater2ndBaseline': {
        'verbose': 'Second Baseline - Water Savings'
    },
    'UnitkWhIOUWater1stBaseline': {
        'verbose': 'First Baseline - IOU Embedded Water Energy Savings'
    },
    'UnitkWhIOUWater2ndBaseline': {
        'verbose': 'Second Baseline - IOU Embedded Water Energy Savings'
    },
    'UnitkWhTotalWater1stBaseline': {
        'verbose': 'First Baseline - Total Embedded Water Energy Savings'
    },
    'UnitkWhTotalWater2ndBaseline': {
        'verbose': 'Second Baseline - Total Embedded Water Energy Savings'
    },
    'MeasTechID': {
        'verbose': 'Measure Technology ID'
    },
    'PreTechID': {
        'verbose': 'Pre-Existing Technology ID'
    },
    'StdTechID': {
        'verbose': 'Standard Technology ID'
    },
    'TechGroup': {
        'verbose': 'Technology Group',
        'validity': 'p.TechGroup__label'
    },
    'PreTechGroup': {
        'verbose': 'Pre-Existing Technology Group',
        'validity': 'p.ExTechGroup__label'
    },
    'StdTechGroup': {
        'verbose': 'Standard Technology Group',
        'validity': 'p.StdTechGroup__label'
    },
    'TechType': {
        'verbose': 'Technology Type',
        'validity': 'p.TechType__label'
    },
    'PreTechType': {
        'verbose': 'Pre-Existing Technology Type',
        'validity': 'p.ExTechType__label'
    },
    'StdTechType': {
        'verbose': 'Standard Technology Type',
        'validity': 'p.StdTechType__label'
    },
    'UseCategory': {
        'verbose': 'Use Category'
    },
    'UseSubCategory': {
        'verbose': 'Use Sub Category'
    },
    'BldgHVAC': {
        'verbose': 'Building HVAC',
        'validity': 'p.BldgHVAC__label'
    },
    'ETP_Flag': {
        'verbose': 'ETP Flag',
        'validity': 'Null__Blank',
        'conditional': [('emergingTech__projectNumber', 'ETVT')]
    },
    'ETP_YearFirstIntroducedToPrograms': {
        'verbose': 'ETP First Year Introduced to Programs',
        'validity': 'Null__BlankDate',
        'conditional': [('emergingTech__introYear', 'ETVT')]
    },
    'IE_Applicable': {
        'verbose': 'Is IE Factor Applied? (Yes / No)'
    },
    'IETableName': {
        'verbose': 'IE Table Name'
    },
    'MeasQualifier': {
        'verbose': 'Measure Qualifier',
        'validity': 'p.MeasQualifier__label'
    },
    'DEER_MeasureID': {
        'verbose': 'DEER Measure ID'
    },
    'MeasCostID': {
        'verbose': 'Measure Cost ID',
        'validity': 'Null__Blank'
    },
    'MeasImpactType': {
        'verbose': 'Measure Impact Type',
        'validity': 'p.MeasImpactType__label'
    },
    'OfferingDesc': {
        'verbose': 'Offering Description',
        'validity': 'offerId__measOfferDesc'
    }
}