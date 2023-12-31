import sys
import json
import errno
from traceback import print_exc
from gooey import Gooey, GooeyParser
from argparse import Namespace

from src.measure_parser.utils import is_etrm_measure
from src.measure_parser.parser import MeasureParser
from src.measure_parser.exceptions import (
    MeasureFormatError,
    InvalidFileError,
    SchemaNotFoundError
)


# parses the command line arguments in sys.argv
#
# Returns:
#   (argparse.Namespace): a namespace containing the associated values
def parse_arguments() -> Namespace:
    argparser: GooeyParser = GooeyParser(
        description='parser for eTRM measure JSON files')

    input_paths = argparser.add_argument_group(
        'Input Paths',
        description='Specify the locations of the eTRM measure JSON file and output directory',
        gooey_options={
            'columns': 1,
            'show_underline': True
        })

    input_paths.add_argument('filepath',
        widget='FileChooser',
        metavar='Measure JSON File',
        help='Select an eTRM measure JSON file',
        gooey_options={
            'wildcard': 'JSON file (*.json)|*.json'
        })

    input_paths.add_argument('output',
        widget='DirChooser',
        metavar='Output Location',
        help='Select a folder to store the output file',
        default=sys.executable[0:sys.executable.rindex('\\')])

    # parser_config = argparser.add_argument_group('Parser Config',
    #     description='Optional flags that determine how the parser is run',
    #     gooey_options={
    #         'show_border': True
    #     })

    # parser_config.add_argument('--validate_schema',
    #     widget='BlockCheckbox',
    #     metavar='Validate Schema',
    #     action=BooleanOptionalAction,
    #     default=True,
    #     gooey_options={
    #         'checkbox_label': ' Validate Schema'
    #     })

    return argparser.parse_args()


@Gooey (
    program_name='eTRM Measure Parser',
    program_description='Parses and validates eTRM measures'
)
def main() -> None:
    args: Namespace = parse_arguments()
    filepath: str = getattr(args, 'filepath', None)
    if filepath == None:
        print('measure JSON file not specified')

    outpath: str = getattr(args, 'output', None)
    if outpath == None:
        print('output directory not specified')

    validate_schema: bool = getattr(args, 'validate_schema', True)
    try:
        if validate_schema and not is_etrm_measure(filepath):
            print(f'ERROR - {filepath} is either missing required '
                  'data or is not an eTRM measure JSON file')
            return
    except SchemaNotFoundError as err:
        print(f'ERROR - {err.message}')
        return
    except json.JSONDecodeError:
        print('ERROR - the measure schema file has been modified, '
              'please re-download your parser')
        return
    except MeasureFormatError:
        print(f'ERROR - {filepath} is not a properly formatted JSON file')
        return
    except OSError as err:
        match err.errno:
            case errno.EPERM:
                print(f'ERROR - {filepath} cannot be accessed')
            case errno.ENOENT:
                print(f'ERROR - {filepath} does not exist')
            case _:
                print('ERROR - an unkown I/O error has occurred while '
                      'validating the JSON schema')
                print_exc()
        return

    try:
        parser: MeasureParser = MeasureParser(filepath)
        parser.parse()
        parser.log_output(outpath)
    except OSError as err:
        print(f'ERROR[{err.errno}] - {outpath} not found')
    except MeasureFormatError as err:
        print(f'A formatting error was encountered in {filepath}:',
              f'\n{err.message}')
    except InvalidFileError as err:
        print(f'The file {filepath} is not valid:',
              f'\n{err.message}')
    except Exception as err:
        print(f'An unhandled error occurred while parsing {filepath}:',
              f'\n{err.__class__.__name__}: {err}')
        print_exc()


if __name__ == '__main__':
    main()