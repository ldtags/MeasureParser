from traceback import print_exc
from gooey import Gooey, GooeyParser
from argparse import Namespace

from measureparser import _ROOT
from measureparser.parser import MeasureParser
from measureparser.exceptions import (
    MeasureFormatError
)

# parses the command line arguments in sys.argv
#
# Returns:
#   (argparse.Namespace): a namespace containing the associated values
def parse_arguments() -> Namespace:
    argparser: GooeyParser = GooeyParser(
        description='parser for eTRM measure JSON files')

    input_group = argparser.add_argument_group(
        title='Measure Source',
        description='Specify the eTRM measure source',
        gooey_options={
            'columns': 2,
            'show_border': True
        })

    conn_group = input_group.add_argument_group(
        title='eTRM Connection',
        description='Measure Version ID and eTRM auth token',
        gooey_options={
            'columns': 1,
            'show_border': True
        })

    conn_group.add_argument('version_id',
        metavar='Measure Version ID',
        help='Version ID of the desired eTRM measure')

    conn_group.add_argument('auth_token',
        metavar='eTRM Auth Token',
        help='Enter an eTRM authorization token')

    input_group.add_argument('filepath',
        widget='FileChooser',
        metavar='Measure JSON File',
        help='Select an eTRM measure JSON file',
        gooey_options={
            'wildcard': 'JSON file (*.json)|*.json'
        })

    input_group.add_argument('password',
        metavar='eTRM Password')

    argparser.add_argument('output',
        widget='DirChooser',
        metavar='Output Location',
        help='Select a folder to store the output file',
        default=_ROOT[0:_ROOT.rindex('\\')])

    return argparser.parse_args()


@Gooey (
    program_name='eTRM Measure Parser',
    program_description='Parses and validates eTRM measures'
)
def main() -> None:
    args = parse_arguments()
    filepath: str | None = getattr(args, 'filepath', None)
    

    outpath: str | None = getattr(args, 'output', None)
    if outpath == None:
        print('ERROR - output directory not specified')
        return

    try:
        parser = MeasureParser(filepath)
        parser.parse()
        parser.log_output(outpath)
    except MeasureFormatError as err:
        print(f'A formatting error was encountered in {filepath}:',
              f'\n{err.message}')
    except Exception as err:
        print(f'An unhandled error occurred while parsing {filepath}:',
              f'\n{err.__class__.__name__}: {err}')
        print_exc()


if __name__ == '__main__':
    main()
