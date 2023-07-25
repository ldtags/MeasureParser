import sys
import json
from data.parameters import ALL_PARAMS
from data.valuetables import ALL_VALUE_TABLES, ALL_SHARED_TABLES
from data.permutations import ALL_PERMUTATIONS
from typing import Optional, TextIO
from exceptions import MeasureFormatError, RequiredParameterError
from objects import (
    Measure,
    SharedParameter,
    ValueTable,
    Calculation,
    Permutation
)
try:
    from types import SimpleNamespace as Namespace
except ImportError:
    from argparse import Namespace


# Global Variables
out: Optional[TextIO] = None


def main(args: list[str]) -> None:
    flags: list[str] = list(filter(lambda arg: arg[0] == '-', args))
    for flag in flags:
        args.remove(flag)

    with open(args[1], 'r') as measure_file:
        if '-console' not in flags: 
            global out
            out = open('out.txt', 'w+')
        measure: Measure = Measure(
            json.loads(measure_file.read(),
                       object_hook=lambda d: Namespace(**d)))
        print(f'\nstarting to parse measure file - {measure_file.name}\n')
        parse(measure)
        print(f'\nfinished parsing measure file - {measure_file.name}')

        if out != None:
            out.close()

# Parses a Measure object that is built from a given JSON file
#
# Parameters:
#   measure (Measure): the Measure object that will be parsed
def parse(measure: Measure) -> None:
    try:
        ordered_params = get_ordered_params(measure)
        ordered_val_tables = get_ordered_value_tables(measure)
        ordered_sha_tables = get_ordered_shared_tables(measure)
    except RequiredParameterError as err:
        print('ERROR - the measure is missing required information\n',
              err)
        return None
    except MeasureFormatError as err:
        print('ERROR - the measure is incorrectly formatted\n', err)
        return None
    except Exception as err:
        print('ERROR - something went wrong\n', err)
        return None

    define_measure_types(measure)
    print('\nParams:\n', ordered_params)
    print('\nValue Tables:\n', ordered_val_tables)
    print('\nShared Tables:\n', ordered_sha_tables)

    print('\nUnknown Parameters/Tables:', file=out)
    print('\tParams: ', list(
        map(lambda param: param.version.version_string,
            measure.remove_unknown_params(ordered_params))),
        file=out)
    print('\tNon-Shared Value Tables: ', list(
        map(lambda table: table.api_name,
            measure.remove_unknown_value_tables(ordered_val_tables))),
        file=out)
    print('\tShared Value Tables: ', list(
        map(lambda table: table.version.version_string,
            measure.remove_unknown_shared_tables(ordered_sha_tables))),
        file=out)

    print('\nMissing Parameters/Tables:', file=out)
    validate_param_existence(measure, ordered_params)
    validate_value_table_existence(measure, ordered_val_tables)
    validate_shared_table_existence(measure, ordered_sha_tables)

    print('\nParameter/Table order:', file=out)
    validate_param_order(measure, ordered_params)
    validate_value_table_order(measure, ordered_val_tables)
    validate_shared_table_order(measure, ordered_sha_tables)

    print('\nValidating Permutations:', file=out)
    validate_permutations(measure.permutations)

    print('\nAll Value Tables:', file=out)
    print_value_tables(measure.value_tables)

    print('\nAll Calculations:', file=out)
    print_calculations(measure.calculations)
    
    print('\nAll Permutations:', file=out)
    print_permutations(measure.permutations)

# returns the ordered list of all parameters to check for
#
# Parameters:
#   measure (Measure): the measure object being parsed
#
# Returns:
#   list[str]: a list of parameter names
def get_ordered_params(measure: Measure) -> list[str]:
    ordered_params = ALL_PARAMS

    try:
        if not measure.is_DEER():
            ordered_params = filter_dict(ordered_params, 'DEER')

        if measure.is_GSIA_default():
            ordered_params = filter_dict(ordered_params, 'NGSIA')

        if not (measure.contains_MAT_label('AR')
                or measure.contains_MAT_label('AOE')):
            ordered_params = filter_dict(ordered_params, 'MAT')

        if not measure.is_WEN():
            ordered_params = filter_dict(ordered_params, 'WEN')

        if measure.is_sector_default():
            ordered_params = filter_dict(ordered_params, 'NTG')

        if not measure.is_interactive():
            ordered_params = filter_dict(ordered_params, 'INTER')
        else:
            ordered_params = filter_inter_params(measure,
                                                 ordered_params)
    except Exception as err:
        raise err

    return list(ordered_params.keys())

# returns the ordered list of all non-shared value tables to check for
#
# Parameters:
#   measure (Measure): the measure object being parsed
#
# Returns:
#   list[str]: a list of non-shared value table names
def get_ordered_value_tables(measure: Measure) -> list[str]:
    ordered_val_tables = ALL_VALUE_TABLES

    try:
        if not measure.is_DEER():
            ordered_val_tables = filter_dict(ordered_val_tables, 'DEER')

        if not (measure.contains_MAT_label('AR')
                or measure.contains_MAT_label('AOE')):
            ordered_val_tables \
                = filter_dict(ordered_val_tables, 'NRNC+ARAOE')

        if not (measure.contains_MAT_label('NR')
                or measure.contains_MAT_label('NC')):
            ordered_val_tables \
                = filter_dict(ordered_val_tables, 'NRNC+ARAOE')

        if not measure.is_deemed():
            ordered_val_tables = filter_dict(ordered_val_tables, 'DEEM')

        if not measure.is_fuel_sub():
            ordered_val_tables = filter_dict(ordered_val_tables, 'FUEL')

        if not measure.is_interactive():
            ordered_val_tables = filter_dict(ordered_val_tables, 'INTER')
        else:
            ordered_val_tables \
                    = filter_inter_value_tables(measure,
                                                ordered_val_tables)
    except Exception as err:
        raise err

    return list(ordered_val_tables.keys())

# returns the ordered list of all shared value tables to check for
#
# Parameters:
#   measure (Measure): the measure object being parsed
#
# Returns:
#   list[str]: a list of shared value table names
def get_ordered_shared_tables(measure: Measure) -> list[str]:
    ordered_sha_tables = ALL_SHARED_TABLES

    try:
        if not measure.is_DEER():
            ordered_sha_tables = filter_dict(ordered_sha_tables, 'DEER')

        if not measure.is_GSIA_default():
            ordered_sha_tables = filter_dict(ordered_sha_tables, 'NGSIA')
        else:
            ordered_sha_tables = filter_dict(ordered_sha_tables, 'GSIA')

        if not (measure.contains_MAT_label('AR')
                or measure.contains_MAT_label('AOE')):
            ordered_sha_tables = filter_dict(ordered_sha_tables, 'ARAOE')

        if not measure.is_WEN():
            ordered_sha_tables = filter_dict(ordered_sha_tables, 'WEN')

        if measure.is_residential_default():
            ordered_sha_tables \
                = filter_dict(ordered_sha_tables, 'RES-DEF')
            ordered_sha_tables = filter_dict(ordered_sha_tables, 'RES')
        elif measure.is_sector_default():
            ordered_sha_tables \
                = filter_dict(ordered_sha_tables, 'RES-NDEF')
            ordered_sha_tables = filter_dict(ordered_sha_tables, 'RES')
        else:
            ordered_sha_tables \
                = filter_dict(ordered_sha_tables, 'RES-NDEF')
            ordered_sha_tables \
                = filter_dict(ordered_sha_tables, 'RES-DEF')

        if not measure.is_interactive():
            ordered_sha_tables = filter_dict(ordered_sha_tables, 'INTER')
        else:
            ordered_sha_tables \
                = filter_inter_shared_tables(measure, ordered_sha_tables)
    except Exception as err:
        raise err

    return list(ordered_sha_tables.keys())

# returns the provided dict excluding any item whose value matches @flag
#
# Parameters:
#   ordered_list (dict[str, str]): the dict being filtered
#   flag (str): the flag to filter the dict for
#
# Returns:
#   dict[str, str]: the filtered dict
def filter_dict(ordered_list: dict[str, str],
                flag: str) -> dict[str, str]:
    return {key:val for (key, val) in ordered_list.items() if val != flag}

# filters the provided list in accordance to the interactive measure specs
#
# Parameters:
#   measure (Measure):  the measure object being parsed
#   ordered_params (dict[str, str]): an ordered dict of parameter names
#
# Returns:
#   dict[str, str]: the dict filtered in accordance to the interactive
#   measure specs
def filter_inter_params(measure: Measure,
                        ordered_params: dict[str, str]
                       ) -> dict[str, str]:
    if not measure.contains_param('LightingType'):
        del ordered_params['LightingType']

    return ordered_params

# filters the provided list in accordance to the interactive measure specs
#
# Parameters:
#   measure (Measure):  the measure object being parsed
#   ordered_tables (dict[str, str]): an ordered dict of non-shared table
#                                    names
#
# Returns:
#   dict[str, str]: the dict filtered in accordance to the interactive
#   measure specs
def filter_inter_value_tables(measure: Measure,
                              ordered_tables: dict[str, str]
                             ) -> dict[str, str]:
    if not measure.contains_value_table('IEApplicability'):
        del ordered_tables['IEApplicability']

    return ordered_tables

# filters the provided list in accordance to the interactive measure specs
#
# Parameters:
#   measure (Measure):  the measure object being parsed
#   ordered_tables (dict[str, str]): an ordered dict of shared table names
#
# Returns:
#   dict[str, str]: the dict filtered in accordance to the interactive
#   measure specs
def filter_inter_shared_tables(measure: Measure,
                               ordered_tables: dict[str, str]
                              ) -> dict[str, str]:
    if not measure.contains_shared_table('commercialInteractiveEffects'):
        del ordered_tables['commercialInteractiveEffects']

    if not measure.contains_shared_table('residentialInteractiveEffects'):
        del ordered_tables['residentialInteractiveEffects']

    return ordered_tables


# Parameters:
#   @sharedTables - a dict mapping all value tables to their respective api_name
#   @tableNames - a list of table names to check the measures value tables against
#
# validates that all shared value tables represented in @tableNames are found in @sharedTables
def validate_shared_table_existence(measure: Measure,
                                    table_names: list[str]) -> None:
    for table in table_names:
        if not measure.contains_shared_table(table):
            print(f'\tMISSING SHARED TABLE - {table}', file=out)


# Parameters:
#   @value_tables - a dict mapping all value tables to their respective api_name
#   @tableNames - a list of table names to check the measures value tables against
#
# validates that all value tables represented in @tableNames are found in @value_tables
def validate_value_table_existence(measure: Measure,
                                   table_names: list[str]) -> None:
    for table in table_names:
        if not measure.contains_value_table(table):
            print(f'\tMISSING TABLE - {table}', file=out)


# Parameters:
#   @sharedParams - a dict mapping all measure parameters to their
#                       respective names
#   @paramNames - a list of parameter names to check the measure
#                     parameters against
#
# validates that all parameters represented in @paramNames are
#      found in @sharedParams
def validate_param_existence(measure: Measure,
                             param_names: list[str]) -> None:
    for param in param_names:
        if not measure.contains_param(param):
            print(f'\tMISSING PARAM - {param}', file=out)


def validate_param_order(measure: Measure,
                         ordered_params: list[str]) -> None:
    for param in measure.params:
        index = ordered_params.index(param.version.version_string)
        if param.order != (index + 1):
            print('\tparameters are out of order', file=out)
            return None


def validate_value_table_order(measure: Measure,
                               ordered_tables: list[str]) -> None:
    for table in measure.value_tables:
        if table.order != (ordered_tables.index(table.api_name) + 1):
            print('\tnon-shared value tables are out of order', file=out)
            return None


def validate_shared_table_order(measure: Measure,
                                ordered_tables: list[str]) -> None:
    for table in measure.shared_tables:
        index = ordered_tables.index(table.version.version_string)
        if table.order != (index + 1):
            print('\tshared value tables are out of order', file=out)
            return None


def validate_permutations(permutations: list[Permutation]) -> None:
    for permutation in permutations:
        perm_name: str = permutation.reporting_name
        perm_data: dict[str, str] = None
        try:
            perm_data = ALL_PERMUTATIONS[perm_name]
        except:
            print(f'UNKNOWN PERMUTATION - {perm_name}')

        valid_name: Optional[str] = None
        try:
            valid_name = perm_data['validity']
        except:
            continue

        if permutation.valid_name == valid_name:
            continue

        print('\tIncorrect Permutation',
              f' -  {permutation.valid_name} should be {valid_name}',
              file=out)


def check_params(measure: Measure,
                 ordered_params: list[str]) -> list[SharedParameter]:
    unknown: list[SharedParameter] = []
    for param in measure.params:
        if param.version.version_string not in ordered_params:
            unknown.append(param)

    for param in unknown:
        measure.params.remove(param)


def print_value_tables(tables: list[ValueTable]) -> None:
    for table in tables:
        print(f'\tTable Name - {table.name}', file=out)
        print(f'\tAPI Name - {table.api_name}', file=out)
        print('\tColumns:', file=out)
        for column in table.columns:
            print(f'\t\tColumn Name - {column.name}', file=out)
            print(f'\t\t\tAPI Name - {column.api_name}', file=out)
        print(file=out)
            

def print_calculations(calculations: list[Calculation]) -> None:
    for calculation in calculations:
        print(f'\tCalculation Name - {calculation.name}', file=out)
        print(f'\t\tAPI Name - {calculation.api_name}\n', file=out)


def print_permutations(permutations: list[Permutation]) -> None:
    for permutation in permutations:
        try:
            perm_data = ALL_PERMUTATIONS[permutation.reporting_name]
        except:
            raise MeasureFormatError()

        try:
            verbose_name = perm_data['verbose']
            print(f'\t{permutation.reporting_name}:',
                  f'\n\t\tVerbose Name - {verbose_name}',
                  f'\n\t\tMapped Field - {permutation.valid_name}\n',
                  file=out)
        except:
            continue

# defines the type of measure that the given measure satisfies
# returns nothing and does not modify any data, use for debugging
def define_measure_types(measure: Measure) -> None:
    if measure.is_DEER():
        print('is DEER measure')

    # if measure.is_AR_or_AOE():
    #     print('MAT = AR and/or AOE')

    # if measure.is_NC_or_NR():
    #     print('MAT = NC and/or NR')

    # if measure.is_def_GSIA():
    #     print('is a default GSIA measure')

    # if measure.is_def_sector():
    #     print('is a sector default measure')

    if measure.is_deemed():
        print('is a deemed delivery type measure')

    if measure.is_WEN():
        print('is a WEN measure')

    if measure.is_fuel_sub():
        print('is fuel substitution measure')

    if measure.is_interactive():
        print('is an interactive measure')


if __name__ == '__main__':
    main(sys.argv)