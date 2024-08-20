"""This module contains lookup tables for eTRM data.

Add data to this module when the data is concise. Otherwise, add the
data to the database in the resources sub-package.
"""


USE_CATEGORIES = {
    'AP': 'Appliance or Plug Load',
    'BE': 'Building Envelope',
    'CA': 'Compressed Air',
    'CR': 'Commercial Refrigeration',
    'FS': 'Food Service',
    'HC': 'HVAC',
    'LG': 'Lighting',
    'MI': 'Miscellanious',
    'PR': 'Process',
    'RE': 'Recreation',
    'SV': 'Service',
    'WB': 'Whole Building',
    'WH': 'Service & Domestic Hot Water',
    'WP': 'Water Pumping / Irrigation'
}
"""A mapping of each use category acronym to its full name."""
