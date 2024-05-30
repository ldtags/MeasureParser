import json
from types import SimpleNamespace

from .dbservice import BaseDatabase
from .exceptions import (
    MeasureFormatError,
    RequiredContentError,
    InvalidFileError
)


class Characterization:
    """Class representation of a characterization."""

    def __init__(self, name: str, content: str):
        self.name: str = name
        self.content: str = content


class Permutation:
    """Class representation of a measure permutation."""

    def __init__(self,
                 reporting_name: str,
                 mapped_name: str | None,
                 derivation: str = 'mapped'):
        self.reporting_name: str = reporting_name
        self.mapped_name: str | None = mapped_name
        self.derivation: str = derivation


class Column:
    """Class representation of a measure specific value table column."""

    def __init__(self, column: object):
        try:
            self.name: str = getattr(column, 'name')
            self.api_name: str = getattr(column, 'api_name')
            self.unit: str = getattr(column, 'unit')
            self.reference_refs: list = getattr(column, 'reference_refs')
        except AttributeError:
            raise MeasureFormatError(field='column')


class Version:
    """Class representation of a measure non-specific table/parameter version.
    """

    def __init__(self, version: object):
        try:
            version_string: str = getattr(version, 'version_string')
            if version_string.index('-') != -1:
                self.version_string = version_string.split('-')[0]
            else:
                self.version_string = version_string
        except AttributeError:
            raise MeasureFormatError(field='version')


class ExclusionTable:
    """Class representation of a measure exclusion table."""

    def __init__(self, table: object):
        try:
            self.name: str = getattr(table, 'name')
            self.api_name: str = getattr(table, 'api_name')
            self.order: int = getattr(table, 'order')
            self.determinants: list[str] = getattr(table, 'determinants')
            self.values: list[list[str | bool]] = getattr(table, 'values')
        except AttributeError:
            raise MeasureFormatError(field='exclusion table')


class Calculation:
    """Class representation of a measure calculation."""

    def __init__(self, calculation: object):
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
            raise MeasureFormatError(field='calculation')


class ParameterLabel:
    """Class representation of a measure specific parameter label."""

    def __init__(self, label: object):
        try:
            self.name: str = getattr(label, 'name')
            self.api_name: str = getattr(label, 'api_name')
            self.active: bool = getattr(label, 'active')
            self.description: str | None \
                = getattr(label, 'description')
        except AttributeError:
            raise MeasureFormatError(field='parameter label')


class Parameter:
    """Class representation of a measure specific parameter."""

    def __init__(self, param: object):
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
        except AttributeError:
            raise MeasureFormatError(field='measure specific parameter')


class SharedParameter:
    """Class representation of a measure non-specific parameter."""

    def __init__(self, param: object):
        try:
            self.order: int = getattr(param, 'order')
            version: SimpleNamespace = getattr(param, 'version')
            self.version: Version = Version(version)
            self.labels: list[str] = getattr(param, 'active_labels')
        except AttributeError:
            raise MeasureFormatError(field='measure non-specific parameter')


class ValueTable:
    """Class representation of a measure specific value table."""

    def __init__(self, value_table: object):
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
            raise MeasureFormatError(field='measure specific value table')

    def contains_column(self, api_name: str) -> bool:
        for column in self.columns:
            if column.api_name == api_name:
                return True
        return False

    def get_column(self, api_name: str) -> Column:
        for column in self.columns:
            if column.api_name == api_name:
                return column
        return None


class SharedValueTable:
    """Class representation of a measure non-specific value table."""

    def __init__(self, shared_table: object):
        try:
            self.order: int = getattr(shared_table, 'order')
            version: SimpleNamespace = getattr(shared_table, 'version')
            self.version: Version = Version(version)
        except AttributeError:
            raise MeasureFormatError(field='measure non-specific value table')


class Measure:
    """Class representation of an eTRM measure.

    Contains all fields from an eTRM measure JSON file and methods for
    querying measure data and information.
    """

    def __init__(self, measure_json: object, db_source: BaseDatabase):
        from .utils import is_etrm_measure
        if not is_etrm_measure(measure_json):
            raise InvalidFileError()

        try:
            self.owner: str = getattr(measure_json, 'owned_by_user')
            self.id: str = getattr(measure_json, 'MeasureID')
            self.version_id: str = getattr(measure_json, 'MeasureVersionID')
            self.name: str = getattr(measure_json, 'MeasureName')
            self.use_category: str = getattr(measure_json, 'UseCategory')
            self.pa_lead: str = getattr(measure_json, 'PALead')
            self.start_date: str = getattr(measure_json, 'StartDate')
            self.end_date: str = getattr(measure_json, 'EndDate', 'None')
            self.status: str = getattr(measure_json, 'Status')
        except AttributeError:
            raise MeasureFormatError(field='measure')

        try:
            self.parameters: list[Parameter] = list(
                map(lambda param: Parameter(param),
                    getattr(measure_json, 'determinants')))

            self.shared_parameters: list[SharedParameter] = list(
                map(lambda param: SharedParameter(param),
                    getattr(measure_json, 'shared_determinant_refs')))

            self.shared_tables: list[SharedValueTable] = list(
                map(lambda table: SharedValueTable(table),
                    getattr(measure_json, 'shared_lookup_refs')))

            self.value_tables: list[ValueTable] = list(
                map(lambda table: ValueTable(table),
                    getattr(measure_json, 'value_tables')))

            self.calculations: list[Calculation] = list(
                map(lambda calc: Calculation(calc),
                    getattr(measure_json, 'calculations')))

            self.exclusion_tables: list[ExclusionTable] = list(
                map(lambda table: ExclusionTable(table),
                    getattr(measure_json, 'exclusion_tables')))
        except AttributeError:
            raise MeasureFormatError()

        self.characterizations: list[Characterization] \
            = db_source.get_characterizations(measure_json)

        self.permutations: list[Permutation] \
            = db_source.get_permutations(measure_json)


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
                          self.shared_parameters)
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


    def contains_table(self, table_name: str) -> bool:
        for table in self.value_tables:
            if table.api_name == table_name:
                return True

        for table in self.shared_tables:
            if table.version.version_string == table_name:
                return True

        return False


    def contains_calculation(self, calc_name: str) -> bool:
        for calculation in self.calculations:
            if calculation.api_name == calc_name:
                return True

            if calculation.name == calc_name:
                return True

        return False


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
    def get_shared_parameter(self, param_name: str
                             ) -> (SharedParameter | None):
        for param in self.shared_parameters:
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
    def get_value_table(self, table_name: str) -> (ValueTable | None):
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
    def get_shared_table(self, table_name: str) -> (SharedValueTable | None):
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
    def get_permutation(self, perm_name: str) -> (Permutation | None):
        for permutation in self.permutations:
            if permutation.reporting_name == perm_name:
                return permutation
        return None


    # returns the characterization object associated with @name, or None
    #   if the characterization doesn't exist
    #
    # Parameters:
    #   name (str)  : the name of the characterization being searched for
    #
    # Returns:
    #   Characterization    : the characterization being searched for
    #   None                : if no such characterization was found
    def get_characterization(self, name: str) -> Characterization | None:
        for characterization in self.characterizations:
            if characterization.name == name:
                return characterization
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
        for param in self.shared_parameters:
            if param.version.version_string not in param_names:
                unknown_params.append(param)

        for param in unknown_params:
            self.shared_parameters.remove(param)

        for i in range(0, len(self.shared_parameters)):
            self.shared_parameters[i].order = i + 1

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
            raise RequiredContentError(name='Measure Application Type')

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
            raise RequiredContentError(name='Version')

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
            raise RequiredContentError(name='Delivery Type')

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
            raise RequiredContentError(name='Measure Impact Type')

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
            raise RequiredContentError(name='Sector')

        ntg_id = self.get_shared_parameter('NTGID')
        if ntg_id == None:
            raise RequiredContentError(name='Net to Gross Ratio ID')

        sectors = list(map(lambda sector: sector + '-Default',
                           sector.labels))
        for sector in sectors:
            for id in ntg_id.labels:
                if sector in id:
                    return True
        return False


    # determines if the measure requires the NTG_Version parameter
    #
    # Returns:
    #   bool    : true if the measure contains any NTGID labels other than
    #             Com-Default, Ind-Default, Agric-Default, or Res-Default
    def requires_ntg_version(self) -> bool:
        ntg_id: SharedParameter = self.get_shared_parameter('NTGID')
        if ntg_id == None:
            raise RequiredContentError(name='Net to Gross Ratio ID')

        for label in ntg_id.labels:
            match label:
                case ('Res-Default>2yrs'
                        | 'Com-Default>2yrs'
                        | 'Ind-Default>2yrs'
                        | 'Agric-Default>2yrs'):
                    continue
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
            raise RequiredContentError(name='Upstream Flag')

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
            raise RequiredContentError(name='Net to Gross Ratio ID')

        return 'Res-Default>2yrs' in ntg_id.labels


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
            raise RequiredContentError(name='Net to Gross Ratio ID')

        for label in ntg_id.labels:
            match label:
                case ('Com-Default>2yrs'
                        | 'Ind-Default>2yrs'
                        | 'Agric-Default>2yrs'):
                    return True
                case _:
                    continue
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
            raise RequiredContentError(name='GSIA ID')

        return 'Def-GSIA' in gsia.labels


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


    # generates a list of criteria determined by the data in the measure
    #
    # Returns:
    #   list[str]: a list of criteria represented as strings
    def get_criteria(self) -> list[str]:
        criteria: list[str] = ['REQ']

        if self.is_DEER():
            criteria.append('DEER')

        if self.is_GSIA_default():
            criteria.append('DEF_GSIA')
        else:
            criteria.append('GSIA')

        if self.is_WEN():
            criteria.append('WEN')

        if self.is_fuel_sub():
            criteria.append('FUEL')

        if self.is_interactive():
            criteria.append('INTER')

        if self.is_res_default():
            criteria.append('RES_DEF')

        if self.is_nonres_default():
            criteria.append('RES_NDEF')

        if not ('RES-DEF' in criteria or 'RES-NDEF' in criteria):
            criteria.append('RES')

        mat_labels: list[str] \
            = self.get_shared_parameter('MeasAppType').labels
        if 'AR' in mat_labels or 'AOE' in mat_labels:
            criteria.append('MAT_ARAOE')

        if 'NC' in mat_labels or 'NR' in mat_labels:
            criteria.append('MAT_NCNR')
            if 'AR' in mat_labels or 'AOE' in mat_labels:
                criteria.append('MAT_NCNR_ARAOE')

        if self.requires_ntg_version():
            criteria.append('NTG')

        if self.requires_upstream_flag():
            criteria.append('DEEM')

        if self.contains_value_table('emergingTech'):
            criteria.append('ET')

        return criteria


    def get_table_column_criteria(self) -> list[str]:
        criteria: list[str] = []

        mat = self.get_shared_parameter('MeasAppType')
        if 'AR' in mat.labels:
            criteria.append('AR_MAT')
            if len(mat.labels) > 2:
                criteria.append('AR_M_MAT')

        deliv = self.get_shared_parameter('DelivType')
        if 'UpDeemed' in deliv.labels:
            if len(deliv.labels) > 2:
                criteria.append('UD_M_DT')

        return criteria


    def get_permutation_criteria(self) -> list[str]:
        criteria: list[str] = []

        mat = self.get_shared_parameter('MeasAppType')
        if 'AR' in mat.labels:
            criteria.append('AR_MAT')
            if len(mat.labels) == 1:
                criteria.append('O_AR_MAT')
            else:
                criteria.append('M_AR_MAT')
        else:
            criteria.append('N_AR_MAT')

        if 'AOE' in mat.labels:
            criteria.append('AOE_MAT')
        else:
            criteria.append('N_AOE_MAT')

        if 'AR' in mat.labels and 'AOE' in mat.labels:
            criteria.append('AR_AOE_MAT')
            if len(mat.labels) == 2:
                criteria.append('O_AR_AOE_MAT')
            else:
                criteria.append('M_AR_AOE_MAT')
        else:
            criteria.append('N_AR_AOE_MAT')

        if self.is_GSIA_default():
            criteria.append('DEF_GSIA')

        criteria.append('PK_DMND')
        criteria.append('ELCT_SVG')
        criteria.append('GAS_SVG')
        criteria.append('FBLC') # maybe in costs value table? ask chau
