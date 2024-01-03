import sys
from traceback import print_exc
from gooey import Gooey, GooeyParser
from argparse import Namespace

from measure_parser.parser import MeasureParser
from measure_parser.exceptions import (
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

    input_paths = argparser.add_argument_group('Input Paths',
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

    return argparser.parse_args()


@Gooey (
    program_name='eTRM Measure Parser',
    program_description='Parses and validates eTRM measures'
)
def main() -> None:
    args = parse_arguments()
    filepath: str = getattr(args, 'filepath', None)
    if filepath == None:
        print('ERROR - measure JSON file not specified')
        return

    outpath: str = getattr(args, 'output', None)
    if outpath == None:
        print('ERROR - output directory not specified')
        return

    try:
        parser = MeasureParser(filepath)
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