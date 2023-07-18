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
            self.api_name: str = valueTable.api_name
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
    def __init__(self, shared_table):
        try:
            self.order: int = shared_table.order
            self.version: Version = Version(shared_table.version)
        except:
            raise SharedTableFormatError()

class Measure:
    def __init__(self, measure):
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
        except:
            raise MeasureFormatError()

    def contains_param(self, param_name: str) -> bool:
        param_names = map(lambda param: param.version.version_string,
                          self.params)
        return param_name in param_names

    def get_param(self, param_name: str) -> SharedParameter:
        for param in self.params:
            if param.version.version_string == param_name:
                return param
        return None

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

    def contains_value_table(self, table_name: str) -> bool:
        value_tables \
            = map(lambda table: table.api_name, self.value_tables)
        return table_name in value_tables

    def get_value_table(self, table_name: str) -> ValueTable:
        for table in self.value_tables:
            if table.api_name == table_name:
                return table
        return None

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

    def contains_shared_table(self, table_name : str) -> bool:
        shared_tables = map(lambda table: table.version.version_string,
                            self.shared_tables)
        return table_name in shared_tables

    def get_shared_table(self, table_name : str) -> SharedValueTable:
        for table in self.shared_tables:
            if table.version.version_string == table_name:
                return table
        return None

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

    # Parameters:
    #   @params - a dict mapping all measure parameters to their
    #       respective names
    #
    # checks the labels of the version param to determine if the
    #   measure is a DEER measure
    #
    # returns true if the measure is a DEER measure
    #   otherwise returns false
    def is_DEER(self) -> bool:
        version = self.get_param('version')
        if version == None:
            raise RequiredParameterError(name='Version')

        for label in version.labels:
            if 'DEER' in label:
                return True

        return False


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
    def is_deemed(self) -> bool:
        delivery_table = self.get_param('DelivType')
        if delivery_table == None:
            raise RequiredParameterError(name='Delivery Type')

        return 'DnDeemDI' in delivery_table.labels \
            or ('DnDeemed' in delivery_table.labels
                and 'UpDeemed' in delivery_table.labels)


    def is_fuel_sub(self) -> bool:
        meas_impact_type = self.get_param('MeasImpactType')
        if meas_impact_type == None:
            raise RequiredParameterError(name='Measure Impact Type')

        for label in meas_impact_type.labels:
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
    def is_def_sector(self) -> bool:
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


    def is_def_res(self) -> bool:
        ntg_id = self.get_param('NTGID')
        if ntg_id == None:
            raise RequiredParameterError(name='Net to Gross Ratio ID')

        for id in ntg_id.labels:
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
    def is_def_GSIA(self) -> bool:
        version = self.get_param('GSIAID')
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
    def is_AR_or_AOE(self) -> bool:
        version = self.get_param('MeasAppType')
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
    def is_NC_or_NR(self) -> bool:
        version = self.get_param('MeasAppType')
        if version == None:
            raise RequiredParameterError(name='Measure Application Type')

        for label in version.labels:
            if 'NC' in label or 'NR' in label:
                return True

        return False


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