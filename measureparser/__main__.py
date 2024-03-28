import signal
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
        help='Version ID of the desired eTRM measure',
        type=str)

    conn_group.add_argument('auth_token',
        metavar='eTRM Auth Token',
        help='Enter an eTRM authorization token',
        type=str)

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
    program_description='Parses and validates eTRM measures',
    shutdown_signal=signal.CTRL_C_EVENT
)
def main() -> None:
    args = parse_arguments()
    msr_filepath: str | None = getattr(args, 'filepath', None)
    msr_version: str | None = getattr(args, 'version_id', None)
    auth_token: str | None = getattr(args, 'auth_token', None)
    if not (msr_filepath or (msr_version and auth_token)):
        print('ERROR - either path to measure JSON file or eTRM auth token'
                + ' and measure version ID required.')
        return

    out_dirpath: str | None = getattr(args, 'output', None)
    if out_dirpath == None:
        print('ERROR - output directory not specified')
        return

    try:
        parser = MeasureParser(msr_filepath)
        parser.parse()
        parser.log_output(out_dirpath)
        return
    except KeyboardInterrupt as err:
        print('Measure parsing interrupted')
    except MeasureFormatError as err:
        print(f'A formatting error was encountered:\n{err.message}')
    except Exception as err:
        print('An unhandled error occurred while parsing:\n',
              f'{err.__class__.__name__}: {err}')
        print_exc()

    parser.clear()


if __name__ == '__main__':
    main()
