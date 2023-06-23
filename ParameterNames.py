REQUIRED_PARAMS = [
    'MeasAppType',
    'BldgType',
    'BldgVint',
    'BldgLoc',
    'BldgHVAC',
    'Sector',
    'EULID',
    'eULVersion',
    'eULBldgType',
    'PAType',
    'PA',
    'DelivType',
    'GSIAID',
    'NTGID',
    'electricImpactProfileID',
    'GasImpactProfileID',
    'NormUnit',
    'UseCategory',
    'UseSubCategory',
    'TechGroup',
    'ExTechGroup',
    'StdTechGroup',
    'TechType',
    'ExTechType',
    'StdTechType',
    'CostAdjustType',
    'MeasImpactCalcType',
    'MeasImpactType',
    'MeasQualifier',
    'version',
    'versionSourceID'
]

DEER_MEASURE_PARAMS = [
    'DEERMeasureID',
    'EnergyImpactID'
]

AR_AOE_PARAMS = [
    'hostEULID',
    'hostEULVersion'
]

NON_DEFAULT_GSIA_PARAMS = [
    'gSIAVersion',
    'gSIABldgType',
    'gSIAVintage',
    'gSIAPA'
]

NTG_VERSION_PARAMS = [
    'NTG_Version'
]

WEN_MEASURE_PARAMS = [
    'waterMeasureType'
]

INTERACTIVE_EFFECTS_PARAMS = [
    'LightingType',
    'iEVersion',
    'iEBldgType'
]

ALL_PARAMS = {
    'MeasAppType':              'REQ',
    'DEERMeasureID':            'DEER',
    'EnergyImpactID':           'DEER',
    'BldgType':                 'REQ',
    'BldgVint':                 'REQ',
    'BldgLoc':                  'REQ',
    'BldgHVAC':                 'REQ',
    'Sector':                   'REQ',
    'EULID':                    'REQ',
    'eULVersion':               'REQ',
    'hostEULID':                'MAT',
    'hostEULVersion':           'MAT',
    'eULBldgType':              'REQ',
    'PAType':                   'REQ',
    'PA':                       'REQ',
    'DelivType':                'REQ',
    'GSIAID':                   'REQ',
    'gSIAVersion':              'NGSIA',
    'gSIABldgType':             'NGSIA',
    'gSIAVintage':              'NGSIA',
    'gSIAPA':                   'NGSIA',
    'NTGID':                    'REQ',
    'NTG_Version':              'NTG',
    'electricImpactProfileID':  'REQ',
    'GasImpactProfileID':       'REQ',
    'NormUnit':                 'REQ',
    'UseCategory':              'REQ',
    'UseSubCategory':           'REQ',
    'TechGroup':                'REQ',
    'ExTechGroup':              'REQ',
    'StdTechGroup':             'REQ',
    'TechType':                 'REQ',
    'ExTechType':               'REQ',
    'StdTechType':              'REQ',
    'CostAdjustType':           'REQ',
    'MeasImpactCalcType':       'REQ',
    'MeasImpactType':           'REQ',
    'MeasQualifier':            'REQ',
    'version':                  'REQ',
    'versionSourceID':          'REQ',
    'waterMeasureType':         'WEN',
    'LightingType':             'INTER',
    'iEVersion':                'INTER',
    'iEBldgType':               'INTER'
}