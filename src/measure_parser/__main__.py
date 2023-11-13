import sys
from gooey import (
    Gooey,
    GooeyParser
)
from argparse import (
    Namespace
)

from src.measure_parser.parser import MeasureParser
from src.measure_parser.exceptions import (
    MeasureFormatError
)


# parses the command line arguments in sys.argv
#
# Returns:
#   (argparse.Namespace): a namespace containing the associated values
def parse_arguments() -> Namespace:
    argparser: GooeyParser = GooeyParser(
        description='parser for eTRM measure JSON files')

    argparser.add_argument('filepath',
        widget='FileChooser',
        metavar='Measure JSON File',
        help='Select an eTRM measure JSON file',
        gooey_options={
            'wildcard': 'JSON file (*.json)|*.json'
        })

    argparser.add_argument('output',
        widget='DirChooser',
        metavar='Output Location',
        help='Select a folder to store the output file',
        default=sys.executable[0:sys.executable.rindex('\\')])

    return argparser.parse_args()

# controls the flow of processes when parsing the measure
#
# Parameters:
#   args (list[str]): measure parsing arguments, including flags
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

    try:
        parser: MeasureParser = MeasureParser(filepath, output)
        parser.parse()
        parser.close()
    except OSError as err:
        print(f'ERROR[{err.errno}] - {output} not found')
    except MeasureFormatError as err:
        print(f'An error occurred while parsing {filepath}:',
              f'\n{err.message}')
    except Exception as err:
        print(f'An unhandled error occurred while parsing {filepath}:',
              f'\n{err.__class__.__name__}: {err}')


if __name__ == '__main__':
    main()