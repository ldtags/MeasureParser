import os
import sys
import signal
from traceback import print_exc
from gooey import Gooey, GooeyParser
from argparse import Namespace

from measureparser import _ROOT
from measureparser.utils import perror
from measureparser.parser import MeasureParser
from measureparser.dbservice import (
    BaseDatabase,
    LocalDatabase,
    ETRMDatabase
)
from measureparser.exceptions import (
    ParserError,
    MeasureFormatError,
    DatabaseError,
    DatabaseConnectionError,
    InvalidFileError
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

    conn_group.add_argument('msr_id',
        metavar='Measure ID',
        help='ID of the desired eTRM measure (Example: SWHC002-03)',
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
        default=_ROOT[0:_ROOT.rindex(os.pathsep)])

    return argparser.parse_args()


@Gooey (
    program_name='eTRM Measure Parser',
    program_description='Parses and validates eTRM measures',
    shutdown_signal=signal.CTRL_C_EVENT
)
def main() -> None:
    args = parse_arguments()
    msr_filepath: str | None = getattr(args, 'filepath', None)
    msr_id: str | None = getattr(args, 'msr_id', None)
    auth_token: str | None = getattr(args, 'auth_token', None)
    if not (msr_filepath or (msr_id and auth_token)):
        perror('Input Error:\nEither path to measure JSON file or eTRM'
                + ' auth token and measure version ID required.')
        return

    out_dirpath: str | None = getattr(args, 'output', None)
    if out_dirpath == None:
        perror('Input Error:\nOutput directory not specified')
        return

    database: BaseDatabase | None = None
    msr_source: str | None = None
    try:
        if (msr_id and auth_token):
            database = ETRMDatabase(auth_token)
            msr_source = msr_id
        elif msr_filepath:
            database = LocalDatabase()
            msr_source = msr_filepath
        else:
            raise DatabaseConnectionError('No database source specified')
    except DatabaseError as err:
        perror(f'Database Error:\n{err.message}')
        return

    try:
        measure = database.get_measure(msr_source)
    except MeasureFormatError as err:
        perror(f'Measure Format Error:\n{err.message}')
        return
    except InvalidFileError as err:
        perror(f'Invalid File Error:\n{err.message}')
        return

    try:
        parser = MeasureParser(database)
        parser.parse(measure)
        parser.log_output(out_dirpath)
    except ParserError as err:
        perror(f'Parser Error:\n{err.message}')
        return


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Measure parsing interrupted')
    except Exception as err:
        perror('An unhandled error occurred while parsing measure:\n',
              f'{err.__class__.__name__}: {err}')
        print_exc(file=sys.stderr)
