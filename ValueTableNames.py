REQUIRED_TABLES = [
    'offerId',
    'measOffer',
    'implementationEligibility',
    'description'
]

REQUIRED_SHARED_TABLES = [
    'GSIA_default',
    'EUL',
    'Null'
]

DEER_TABLES = [
    'offerIdDEERId'
]

SHARED_DEER_TABLES = [
    'DEERMeasure',
    'EnergyImpactAP'
]

WEN_TABLES = [
    'waterEnergyIntensity'
]

NR_NC_TABLES = [
    'hostEULID'
]

AR_AOE_TABLES = [
    'hostEulAndRul'
]

INTERACTIVE_TABLES = [
    'IEApplicability'
]

ALL_TABLES = {
    'offerId': 'REQ',
    'measOffer': 'REQ',
    'implementationEligibility': 'REQ',
    'description': 'REQ',
    'offerIdDEERId': 'DEER',
    
}