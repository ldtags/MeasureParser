import sys
from traceback import print_exc
from gooey import Gooey, GooeyParser
from argparse import Namespace

from src.measure_parser.parser import MeasureParser
from src.measure_parser.exceptions import (
    MeasureFormatError,
    InvalidFileError
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
        'Specify the locations of the eTRM measure JSON file and output directory')

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

    parser_config = argparser.add_argument_group(
        'Parser Config',
        'Optional flags that determine how the parser is run',
        show_border=True)

    parser_config.add_argument('validate_schema',
        widget='BlockCheckbox',
        gooey_options={
            'checkbox_label': 'Validate Schema'
        })

    return argparser.parse_args()


@Gooey (
    program_name='eTRM Measure Parser',
    program_description='Parses and validates eTRM measures',
    required_cols=1
)
def main() -> None:
    args: Namespace = parse_arguments()
    filepath: str = getattr(args, 'filepath', None)
    if (filepath == None):
        print('measure JSON file not found')

    output: str = getattr(args, 'output', None)
    if (output == None):
        print('invalid output location')

    validate_schema: bool = getattr(args, 'validate_schema', False)

    try:
        parser: MeasureParser = MeasureParser(filepath, validate_schema)
        parser.parse()
        parser.log_output(output)
    except OSError as err:
        print(f'ERROR[{err.errno}] - {output} not found')
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