from typing import Optional
try:
    from types import SimpleNamespace as Namespace
except ImportError:
    from argparse import Namespace

import src.measure_parser.constants as cnst
import src.measure_parser.dbservice as db
from src.measure_parser.exceptions import (
    RequiredParameterError,
    VersionFormatError,
    ParameterFormatError,
    ValueTableFormatError,
    SharedTableFormatError,
    MeasureFormatError,
    ColumnFormatError,
    CalculationFormatError,
    RequiredCharacterizationError
)


class Characterization:
    """the representation of a characterization
    """
    def __init__(self, name: str, content: str):
        self.name: str = name
        self.content: str = content

class Permutation:
    """the representation of a permutation
    """
    def __init__(self,
                 reporting_name: str,
                 mapped_name: Optional[str],
                 derivation: str = 'mapped'):
        self.reporting_name: str = reporting_name
        self.mapped_name: str = mapped_name
        self.derivation: str = derivation

class Column:
    """the representation of a column
    """
    def __init__(self, column: Namespace):
        try:
            self.name: str = getattr(column, 'name')
            self.api_name: str = getattr(column, 'api_name')
            self.unit: str = getattr(column, 'unit')
            self.reference_refs: list = getattr(column, 'reference_refs')
        except AttributeError:
            raise ColumnFormatError()
        except Exception as err:
            raise err

class Version:
    """the representation of a version
    """
    def __init__(self, version: Namespace):
        try:
            version_string: str = getattr(version, 'version_string')
            if version_string.index('-') != -1:
                self.version_string = version_string.split('-')[0]
            else:
                self.version_string = version_string
        except AttributeError:
            raise VersionFormatError()
        except Exception as err:
            raise err
        
class ExclusionTable:
    """defines a measure exclusion table
    """
    def __init__(self, table: Namespace):
        try:
            self.name: str = getattr(table, 'name')
            self.api_name: str = getattr(table, 'api_name')
            self.order: int = getattr(table, 'order')
            self.determinants: list[str] = getattr(table, 'determinants')
            self.values: list[list[str | bool]] = getattr(table, 'values')
        except Exception as err:
            raise err

class Calculation:
    """contains data related to a calculation
    """
    def __init__(self, calculation: Namespace):
        try:
            self.name: str = getattr(calculation, 'name')
            self.api_name: str = getattr(calculation, 'api_name')
            self.order: int = getattr(calculation, 'order')
            self.unit: str = getattr(calculation, 'unit')
            self.determinants: list[str] \
                = getattr(calculation, 'determinants')
            self.values: list[list[str]] = getattr(calculation, 'values')
            self.reference_refs: list \
                = getattr(calculation, 'reference_refs')
        except AttributeError:
            raise CalculationFormatError()
        except Exception as err:
            raise err
        
class ParameterLabel:
    """a label found in a measure specific parameter
    """
    def __init__(self, label: Namespace):
        try:
            self.name: str = getattr(label, 'name')
            self.api_name: str = getattr(label, 'api_name')
            self.active: bool = getattr(label, 'active')
            self.description: Optional[str] \
                = getattr(label, 'description')
        except Exception as err:
            raise err
        
class Parameter:
    """contains data related to a measure specific parameter
    """
    def __init__(self, param: Namespace):
        try:
            self.name: str = getattr(param, 'name')
            self.api_name: str = getattr(param, 'api_name')
            self.labels: list[ParameterLabel] = list(
                map(lambda label: ParameterLabel(label),
                    getattr(param, 'labels')))
            self.description: str = getattr(param, 'description')
            self.order: int = getattr(param, 'order')
            self.reference_refs: list[str] \
                = getattr(param, 'reference_refs')
        except Exception as err:
            raise err

class SharedParameter:
    """contains data related to a shared parameter
    """
    def __init__(self, param: Namespace):
        try:
            self.order: int = getattr(param, 'order')
            version: Namespace = getattr(param, 'version')
            self.version: Version = Version(version)
            self.labels: list[str] = getattr(param, 'active_labels')
        except AttributeError:
            raise ParameterFormatError()
        except Exception as err:
            raise err

class ValueTable:
    """contains data related to a measure specific value table
    """
    def __init__(self, value_table: Namespace):
        try:
            self.name: str = getattr(value_table, 'name')
            self.api_name: str = getattr(value_table, 'api_name')
            self.type: str = getattr(value_table, 'type')
            self.description: str = getattr(value_table, 'description')
            self.order: int = getattr(value_table, 'order')
            self.determinants: list = getattr(value_table, 'determinants')
            self.columns: list[Column] = list(
                map(lambda column: Column(column),
                    getattr(value_table, 'columns')))
            self.values: list[str] = getattr(value_table, 'values')
            self.reference_refs: list \
                = getattr(value_table, 'reference_refs')
        except AttributeError:
            raise ValueTableFormatError()
        except Exception as err:
            raise err

class SharedValueTable:
    """contains data related to a shared value table
    """

    def __init__(self, shared_table: Namespace):
        try:
            self.order: int = getattr(shared_table, 'order')
            version: Namespace = getattr(shared_table, 'version')
            self.version: Version = Version(version)
        except AttributeError:
            raise SharedTableFormatError()
        except Exception as err:
            raise err

class Measure:
    """a measure built from data in an eTRM measure JSON file
    
    Attributes:
        owner (str): the listed owner of the measure
        params (list[SharedParameter]): the list of parameters
        shared_tables (list[SharedValueTable]): the list of shared
                                                value tables
        value_tables (list[ValueTable]): the list of non-shared value
                                         tables
        calculations (list[Calculation]): the list of calculations
        permutations (list[Permutation]): the list of permutations
        characterizations (list[Characterization]): the list of
                                                    characterizations
    """

    def __init__(self, measure: Namespace):
        try:
            self.owner: str = getattr(measure, 'owned_by_user')

            self.params: list[Parameter] = list(
                map(lambda param: Parameter(param),
                    getattr(measure, 'determinants')))

            self.shared_params: list[SharedParameter] = list(
                map(lambda param: SharedParameter(param),
                    getattr(measure, 'shared_determinant_refs')))

            self.shared_tables: list[SharedValueTable] = list(
                map(lambda table: SharedValueTable(table),
                    getattr(measure, 'shared_lookup_refs')))

            self.value_tables: list[ValueTable] = list(
                map(lambda table: ValueTable(table),
                    getattr(measure, 'value_tables')))

            self.calculations: list[Calculation] = list(
                map(lambda calc: Calculation(calc),
                    getattr(measure, 'calculations')))

            self.exclusion_tables: list[ExclusionTable] = list(
                map(lambda table: ExclusionTable(table),
                    getattr(measure, 'exclusion_tables')))

            self.id: str = getattr(measure, 'MeasureID')
            self.version_id: str = getattr(measure, 'MeasureVersionID')
            self.name: str = getattr(measure, 'MeasureName')
            self.use_category: str = getattr(measure, 'UseCategory')
            self.pa_lead: str = getattr(measure, 'PALead')
            self.start_date: str = getattr(measure, 'StartDate')
            self.end_date: str = getattr(measure, 'EndDate', 'None')
            self.status: str = getattr(measure, 'Status')

            self.characterizations: list[Characterization] \
                = get_characterizations(measure)
            self.permutations: list[Permutation] \
                = get_permutations(measure)
        except AttributeError:
            raise MeasureFormatError()
        except RequiredCharacterizationError as err:
            raise MeasureFormatError(err.message)
        except Exception as err:
            raise err

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
                          self.shared_params)
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
        value_tables = map(lambda table: table.api_name,
                           self.value_tables)
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
    def contains_shared_table(self, table_name: str) -> bool:
        table_names = map(lambda table: table.version.version_string,
                            self.shared_tables)
        return table_name in table_names

    # Checks if the measure contains a permutation associated with
    # @perm_name
    #
    # Parameters:
    #   perm_name (str): the name of the desired permutation
    #
    # Returns:
    #   bool: True if the measure contains a permutation associated
    #         with @perm_name
    def contains_permutation(self, perm_name: str) -> bool:
        perm_names = map(lambda perm: perm.reporting_name,
                         self.permutations)
        return perm_name in perm_names

    # Returns the parameter associated with @param_name
    #
    # Parameters:
    #   param_name (str): name of desired parameter
    #
    # Returns:
    #   SharedParameter: The desired parameter
    #   None: If no parameter with a name matching @param_name exists 
    def get_shared_parameter(self, param_name: str) -> Optional[SharedParameter]:
        for param in self.shared_params:
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
    def get_value_table(self, table_name: str) -> Optional[ValueTable]:
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
    def get_shared_table(self,
                         table_name: str) -> Optional[SharedValueTable]:
        for table in self.shared_tables:
            if table.version.version_string == table_name:
                return table
        return None

    # Returns the permutation associated with @perm_name
    #
    # Parameters:
    #   perm_name (str): name of desired permutation
    #
    # Returns:
    #   SharedValueTable: The desired permutation
    #   None: If no permutation with a name matching @perm_name exists
    def get_permutation(self, perm_name: str) -> Optional[Permutation]:
        for permutation in self.permutations:
            if permutation.reporting_name == perm_name:
                return permutation
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
        for param in self.shared_params:
            if param.version.version_string not in param_names:
                unknown_params.append(param)

        for param in unknown_params:
            self.shared_params.remove(param)

        for i in range(0, len(self.shared_params)):
            self.shared_params[i].order = i + 1

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
                                    table_names: list[str]
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
                                     table_names: list[str]
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
        version = self.get_shared_parameter('MeasAppType')
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
        version = self.get_shared_parameter('version')
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
        wen_param = self.get_shared_parameter('waterMeasureType')
        wen_table = self.get_shared_table('waterEnergyIntensity')
        if wen_param == None or wen_table == None:
            if (wen_param == None) ^ (wen_table == None):
                raise Exception(
                    'WEN measure detected but required data is missing - '
                    + ('Water Energy Intensity Parameter' if wen_table
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
        delivery_table = self.get_shared_parameter('DelivType')
        if delivery_table == None:
            raise RequiredParameterError(name='Delivery Type')

        return ('DnDeemDI' in delivery_table.labels
                or ('DnDeemed' in delivery_table.labels
                    and 'UpDeemed' in delivery_table.labels))

    # Checks if the Measure Impact Type of the measure is FuelSub
    #
    # Exceptions:
    #   RequiredParameterError: raised if the 'Measure Impact Type'
    #                           parameter is missing
    #
    # Returns:
    #   bool: True if the measure is a Fuel Substitution measure
    def is_fuel_sub(self) -> bool:
        meas_impact_type = self.get_shared_parameter('MeasImpactType')
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
        sector = self.get_shared_parameter('Sector')
        if sector == None:
            raise RequiredParameterError(name='Sector')

        ntg_id = self.get_shared_parameter('NTGID')
        if ntg_id == None:
            raise RequiredParameterError(name='Net to Gross Ratio ID')

        sectors = list(map(lambda sector: sector + '-Default',
                           sector.labels))
        for sector in sectors:
            for id in ntg_id.labels:
                if sector in id:
                    return True
        return False


    def requires_ntg_version(self) -> bool:
        ntg_id: SharedParameter = self.get_shared_parameter('NTGID')
        if ntg_id == None:
            raise RequiredParameterError(name='Net to Gross Ratio ID')

        for label in ntg_id.labels:
            match label:
                case (cnst.RES_DEF
                        | cnst.COM_DEF
                        | cnst.IND_DEF
                        | cnst.AGRIC_DEF):
                    break
                case _:
                    return True
        return False

    # Determines if the measure requires the upstream flag value table
    #
    # Exceptions:
    #   RequiredParameterError: raised if the 'DelivType' parameter is
    #                           missing
    #
    # Returns:
    #   bool: True if there are multiple labels in the 'DelivType'
    #         parameter and one of such labels is 'UpDeemed'
    def requires_upstream_flag(self) -> bool:
        upstream_flag: SharedParameter \
            = self.get_shared_parameter('DelivType')
        if upstream_flag == None:
            raise RequiredParameterError(name='Upstream Flag')

        labels: list[str] = upstream_flag.labels
        if len(labels) < 2:
            return False

        return 'UpDeemed' in labels

    # Checks if the NTGID contains the residential default
    #
    # Exceptions:
    #   RequiredParameterError: raised if the 'NTGID' parameter is missing
    #
    # Returns:
    #   bool: True if the NTGID parameter contains the residential default
    def is_res_default(self) -> bool:
        ntg_id: SharedParameter = self.get_shared_parameter('NTGID')
        if ntg_id == None:
            raise RequiredParameterError(name='Net to Gross Ratio ID')

        for label in ntg_id.labels:
            match label:
                case cnst.RES_DEF:
                    return True
                case _:
                    break
        return False

    # Checks if the NTGID contains the non-residential default
    #
    # Exceptions:
    #   RequiredParameterError: raised if the 'NTGID' parameter is missing
    #
    # Returns:
    #   bool: True if the NTGID parameter contains the non-residential
    #         default
    def is_nonres_default(self) -> bool:
        ntg_id: SharedParameter = self.get_shared_parameter('NTGID')
        if ntg_id == None:
            raise RequiredParameterError(name='Net to Gross Ratio ID')

        for label in ntg_id.labels:
            match label:
                case (cnst.COM_DEF
                        | cnst.IND_DEF
                        | cnst.AGRIC_DEF):
                    return True
                case _:
                    break
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
        gsia: SharedParameter = self.get_shared_parameter('GSIAID')
        if gsia == None:
            raise RequiredParameterError(name='GSIA ID')

        return 'Def-GSIA' in gsia.labels

    # Checks if the GSIAID contains a non-default label
    #
    # Exceptions:
    #   RequiredParameterError: raised if the 'GSIAID' parameter is
    #                           missing
    #
    # Returns:
    #   bool: True if the GSIAID parameter contains a non-default label
    def is_GSIA_nondef(self) -> bool:
        gsia: SharedParameter = self.get_shared_parameter('GSIAID')
        if gsia == None:
            raise RequiredParameterError(name='GSIA ID')

        return cnst.GSIA_DEF not in gsia.labels

    # Checks if the measure is an interactive measure
    #
    # Exceptions:
    #   MeasureFormatError: raised if only some of the required
    #                       interactive fields are present
    #
    # Returns:
    #   bool: True if the measure is an interactive measure
    def is_interactive(self) -> bool:
        lighting_type: SharedParameter \
            = self.get_shared_parameter('LightingType')
        interactive_effect_app: ValueTable \
            = self.get_value_table('IEApplicability')
        commercial_effects: SharedValueTable \
            = self.get_shared_table('commercialInteractiveEffects')
        residential_effects: SharedValueTable \
            = self.get_shared_table('residentialInteractiveEffects')

        if lighting_type or (commercial_effects or residential_effects):
            return True
        # elif (lighting_type or (commercial_effects or residential_effects)
        #       or interactive_effect_app):
        #     raise MeasureFormatError(
        #         'Missing required information for interactive effects')

        return False


    def get_characterization(self, name: str) -> Characterization | None:
        for characterization in self.characterizations:
            if characterization.name == name:
                return characterization
        return None


# returns a list of all characterizations found in @measure
#
# Parameters:
#   measure (Namespace): the namespace representation of a measure
#
# Returns:
#   list[Characterization]: the list of characterizations found in
#                           @measure
def get_characterizations(measure: Namespace) -> list[Characterization]:
    char_list: list[Characterization] = []
    for char_name in db.get_characterization_names(measure):
        content: str = getattr(measure, char_name, None)
        if content == None:
            raise RequiredCharacterizationError(name=char_name)
        char_list.append(Characterization(char_name, content))
    return char_list

# returns a list of all permutations found in @measure
#
# Parameters:
#   measure (Namespace): the namespace representation of a measure
#
# Returns:
#   list[Permutation]: the list of permutations found in @measure
def get_permutations(measure: Namespace) -> list[Permutation]:
    perm_list: list[Permutation] = []
    for perm_name in db.get_permutation_names():
        verbose_name = getattr(measure, perm_name, None)
        if verbose_name != None:
            perm_list.append(Permutation(perm_name, verbose_name))
    return perm_list