from typing import Optional
from data.permutations import ALL_PERMUTATIONS
from exceptions import (
    RequiredParameterError,
    VersionFormatError,
    ParameterFormatError,
    ValueTableFormatError,
    SharedTableFormatError,
    MeasureFormatError,
    PermutationFormatError,
    RequiredPermutationError
)
try:
    from types import SimpleNamespace as Namespace
except ImportError:
    from argparse import Namespace

class Permutation:
    def __init__(self,
                 reporting_name: str,
                 valid_name: Optional[str],
                 derivation: str = 'mapped'):
        self.reporting_name: str = reporting_name
        self.valid_name: str = valid_name
        self.derivation: str = derivation

class Column:
    def __init__(self, column: Namespace):
        try:
            self.name: str = column.name
            self.api_name: str = column.api_name
            self.unit: str = column.unit
            self.reference_refs: list = column.reference_refs
        except:
            raise Exception()

class Version:
    def __init__(self, version: Namespace):
        try:
            if version.version_string.index('-') != -1:
                self.version_string = version.version_string.split('-')[0]
            else:
                self.version_string = version.version_string
        except:
            raise VersionFormatError()

class Calculation:
    def __init__(self, calculation: Namespace):
        try:
            self.name: str = calculation.name
            self.api_name: str = calculation.api_name
            self.order: int = calculation.order
            self.unit: str = calculation.unit
            self.determinants: list[str] = calculation.determinants
            self.values: list[list[str]] = calculation.values
            self.reference_refs: list = calculation.reference_refs
        except Exception as err:
            raise err

class SharedParameter:
    def __init__(self, param: Namespace):
        try:
            self.order: int = getattr(param, 'order')
            self.version: Version = Version(param.version)
            self.labels: list[str] = param.active_labels
        except AttributeError:
            raise ParameterFormatError()
        except:
            raise Exception(
                '')

class ValueTable:
    def __init__(self, valueTable: Namespace):
        try:
            self.name: str = valueTable.name
            self.api_name: str = valueTable.api_name
            self.type: str = valueTable.type
            self.description: str = valueTable.description
            self.order: int = valueTable.order
            self.determinants: list = valueTable.determinants
            self.columns: list[Column] = list(
                map(lambda column: Column(column),
                    valueTable.columns))
            self.values: list[str] = valueTable.values
            self.refs: list = valueTable.reference_refs
        except:
            raise ValueTableFormatError()

class SharedValueTable:
    def __init__(self, shared_table: Namespace):
        try:
            self.order: int = shared_table.order
            self.version: Version = Version(shared_table.version)
        except:
            raise SharedTableFormatError()

class Measure:
    def __init__(self, measure: Namespace):
        try:
            self.owner: str = measure.owned_by_user
            self.params: list[SharedParameter] = list(
                map(lambda param: SharedParameter(param),
                    measure.shared_determinant_refs))
            self.shared_tables: list[SharedValueTable] = list(
                map(lambda table: SharedValueTable(table),
                    measure.shared_lookup_refs))
            self.value_tables: list[ValueTable] = list(
                map(lambda table: ValueTable(table),
                    measure.value_tables))
            self.calculations: list[Calculation] = list(
                map(lambda calc: Calculation(calc),
                    measure.calculations))
            self.permutations: list[Permutation] \
                = self.get_permutations(measure)
        except RequiredPermutationError as err:
            raise err
        except:
            raise MeasureFormatError()

    def get_permutations(self, measure: Namespace) -> list[Permutation]:
        permutations: Namespace = Namespace(**ALL_PERMUTATIONS)
        perm_names: list[str] = list(ALL_PERMUTATIONS.keys())
        perm_list: list[Permutation] = []
        for perm_name in perm_names:
            permutation = getattr(permutations, perm_name, None)
            if permutation == None:
                raise RequiredPermutationError()
            verbose_name = getattr(measure, perm_name, None)
            perm_list.append(
                Permutation(
                    perm_name,
                    verbose_name
                )
            )
        return perm_list
        

    # Checks if the measure contains a parameter associated with
    # @param_name
    #
    # Parameters:
    #   param_name (str): name of desired parameter
    #
    # Returns:
    #   bool: True if the measure contains a parameter associated
    #         with @param_name
    def contains_param(self, param_name: str) -> bool:
        param_names = map(lambda param: param.version.version_string,
                          self.params)
        return param_name in param_names
    
    # Checks if the measure contains a non-shared value table associated
    # with @table_name
    #
    # Parameters:
    #   table_name (str): the name of the desired value table
    #
    # Returns:
    #   bool: True if the measure contains a non-shared value table
    #         associated with @table_name
    def contains_value_table(self, table_name: str) -> bool:
        value_tables \
            = map(lambda table: table.api_name, self.value_tables)
        return table_name in value_tables
    
    # Checks if the measure contains a shared value table associated with
    # @table_name
    #
    # Parameters:
    #   table_name (str): the name of the desired value table
    #
    # Returns:
    #   bool: True if the measure contains a shared value table associated
    #         with @table_name
    def contains_shared_table(self, table_name : str) -> bool:
        shared_tables = map(lambda table: table.version.version_string,
                            self.shared_tables)
        return table_name in shared_tables

    # Returns the parameter associated with @param_name
    #
    # Parameters:
    #   param_name (str): name of desired parameter
    #
    # Returns:
    #   SharedParameter: The desired parameter
    #   None: If no parameter with a name matching @param_name exists 
    def get_param(self, param_name: str) -> SharedParameter:
        for param in self.params:
            if param.version.version_string == param_name:
                return param
        return None
    
    # Returns the non-shared value table associated with @table_name
    #
    # Parameters:
    #   table_name (str): name of desired value table
    #
    # Returns:
    #   ValueTable: The desired non-shared value table
    #   None: If no value table with a name matching @table_name exists
    def get_value_table(self, table_name: str) -> ValueTable:
        for table in self.value_tables:
            if table.api_name == table_name:
                return table
        return None
    
    # Returns the shared value table associated with @table_name
    #
    # Parameters:
    #   table_name (str): name of desired value table
    #
    # Returns:
    #   SharedValueTable: The desired shared value table
    #   None: If no value table with a name matching @table_name exists
    def get_shared_table(self, table_name : str) -> SharedValueTable:
        for table in self.shared_tables:
            if table.version.version_string == table_name:
                return table
        return None

    # Removes all parameters whose names don't appear in @param_names
    #    
    # Parameters:
    #   param_names (list[str]): a list of valid parameter names
    #        
    # Returns:
    #   list[SharedParameter]: the list of parameters not in
    #   @param_names
    def remove_unknown_params(self,
                              param_names: list[str]
                             ) -> list[SharedParameter]:
        unknown_params: list[SharedParameter] = []
        for param in self.params:
            if param.version.version_string not in param_names:
                unknown_params.append(param)

        for param in unknown_params:
            self.params.remove(param)

        for i in range(0, len(self.params)):
            self.params[i].order = i + 1

        return unknown_params

    # Removes all non-shared value tables whose names don't appear in
    # @table_names
    #    
    # Parameters:
    #   table_names (list[str]): a list of valid non-shared value table
    #                            names
    #        
    # Returns:
    #   list[ValueTable]: the list of non-shared value tables not in
    #   @table_names
    def remove_unknown_value_tables(self,
                                    table_names : list[str]
                                   ) -> list[ValueTable]:
        unknown_tables : list[ValueTable] = []
        for table in self.value_tables:
            if table.api_name not in table_names:
                unknown_tables.append(table)

        for table in unknown_tables:
            self.value_tables.remove(table)

        for i in range(0, len(self.value_tables)):
            self.value_tables[i].order = i + 1

        return unknown_tables

    # Removes all shared value tables whose names don't appear in
    # @table_names
    #    
    # Parameters:
    #   table_names (list[str]): a list of valid shared value table names
    #        
    # Returns:
    #   list[SharedValueTable]: the list of shared value tables not in
    #   @table_names
    def remove_unknown_shared_tables(self,
                                     table_names : list[str]
                                    ) -> list[SharedValueTable]:
        unknown_tables: list[SharedValueTable] = []
        for table in self.shared_tables:
            if table.version.version_string not in table_names:
                unknown_tables.append(table)

        for table in unknown_tables:
            self.shared_tables.remove(table)

        for i in range(0, len(self.shared_tables)):
            self.shared_tables[i].order = i + 1

        return unknown_tables
    
    # Checks if the Measure Application Type parameter contains @label
    #
    # Parameters:
    #   labels (str): MAT label(s) being searched for
    #
    # Exceptions:
    #   RequiredParameterError: raised if the 'Measure Application Type'
    #                           parameter is missing
    #
    # Returns:
    #   bool: True if the Measure Application Type parameter contains
    #         all provided labels
    def contains_MAT_label(self, *labels: str) -> bool:
        version = self.get_param('MeasAppType')
        if version == None:
            raise RequiredParameterError(name='Measure Application Type')
        
        for label in labels:
            if label not in version.labels:
                return False
        return True

    # Checks the labels of the version param to determine if the measure
    # is a DEER measure
    #
    # Exceptions:
    #   RequiredParameterError: raised if the 'version' parameter isn't
    #                           present
    #
    # Returns:
    #   bool: True if the measure is a DEER measure
    def is_DEER(self) -> bool:
        version = self.get_param('version')
        if version == None:
            raise RequiredParameterError(name='Version')

        for label in version.labels:
            if 'DEER' in label:
                return True

        return False

    # Checks that either all WEN requirements are met, denoting a WEN
    # measure
    #
    # Exceptions:
    #   Exception: raised if only part of the required WEN data is present
    #
    # Returns:
    #   bool: True if the measure is a WEN measure
    def is_WEN(self) -> bool:
        wen_param = self.get_param('waterMeasureType')
        wen_table = self.get_shared_table('waterEnergyIntensity')
        if wen_param == None or wen_table == None:
            if (wen_param == None) ^ (wen_table == None):
                raise Exception(
                    'WEN measure detected but required data is missing - ' \
                    + ('Water Energy Intensity Parameter' if wen_table \
                       else 'Water Energy Intensity Value Table'))
            return False
        return True

    # Checks if the Delivery Type of the measure is either DnDeemDI
    # or DnDeemed and UpDeemed
    #
    # Exceptions:
    #   RequiredParameterError: raised if the 'Delivery Type' parameter is
    #                           missing
    #
    # Returns:
    #   bool: True if the measure is deemed
    def is_deemed(self) -> bool:
        delivery_table = self.get_param('DelivType')
        if delivery_table == None:
            raise RequiredParameterError(name='Delivery Type')

        return 'DnDeemDI' in delivery_table.labels \
            or ('DnDeemed' in delivery_table.labels
                and 'UpDeemed' in delivery_table.labels)

    # Checks if the Measure Impact Type of the measure is FuelSub
    #
    # Exceptions:
    #   RequiredParameterError: raised if the 'Measure Impact Type'
    #                           parameter is missing
    #
    # Returns:
    #   bool: True if the measure is a Fuel Substitution measure
    def is_fuel_sub(self) -> bool:
        meas_impact_type = self.get_param('MeasImpactType')
        if meas_impact_type == None:
            raise RequiredParameterError(name='Measure Impact Type')

        for label in meas_impact_type.labels:
            if 'FuelSub' in label:
                return True

        return False

    # Checks if the NTGID contains a sector default
    #
    # Exceptions:
    #   RequiredParameterError: raised if the 'NTGID' or 'Sector'
    #                           parameters are missing
    #
    # Returns:
    #   bool: True if the NTGID parameter contains a sector default
    def is_sector_default(self) -> bool:
        sector = self.get_param('Sector')
        if sector == None:
            raise RequiredParameterError(name='Sector')

        ntg_id = self.get_param('NTGID')
        if ntg_id == None:
            raise RequiredParameterError(name='Net to Gross Ratio ID')

        sectors = list(map(lambda sector: sector + '-Default',
                           sector.labels))
        for sector in sectors:
            for id in ntg_id.labels:
                if sector in id:
                    return True
        return False

    # Checks if the NTGID contains the residential default
    #
    # Exceptions:
    #   RequiredParameterError: raised if the 'NTGID' parameter is missing
    #
    # Returns:
    #   bool: True if the NTGID parameter contains the residential default
    def is_residential_default(self) -> bool:
        ntg_id = self.get_param('NTGID')
        if ntg_id == None:
            raise RequiredParameterError(name='Net to Gross Ratio ID')

        for label in ntg_id.labels:
            if 'Res-Default' in label:
                return True
        return False

    # Checks if the GSIAID contains the GSIA default
    #
    # Exceptions:
    #   RequiredParameterError: raised if the 'GSIAID' parameter is
    #                           missing
    #
    # Returns:
    #   bool: True if the GSIAID parameter contains the GSIA default
    def is_GSIA_default(self) -> bool:
        version = self.get_param('GSIAID')
        if version == None:
            raise RequiredParameterError(name='GSIA ID')

        for label in version.labels:
            if 'Def-GSIA' in label:
                return True

        return False

    # Checks if the measure is an interactive measure
    #
    # Exceptions:
    #   MeasureFormatError: raised if only some of the required
    #                       interactive fields are present
    #
    # Returns:
    #   bool: True if the measure is an interactive measure
    def is_interactive(self) -> bool:
        lighting_type = self.get_param('LightingType')
        interactive_effect_app = self.get_value_table('IEApplicability')
        commercial_effects = self.get_shared_table(
            'commercialInteractiveEffects')
        residential_effects = self.get_shared_table(
            'residentialInteractiveEffects')

        if lighting_type and (commercial_effects or residential_effects):
            return True
        elif (lighting_type or (commercial_effects or residential_effects)
              or interactive_effect_app):
            raise MeasureFormatError(
                'Missing required information for interactive effects')

        return False