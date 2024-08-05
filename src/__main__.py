import sys
from traceback import print_exc
from argparse import ArgumentParser, Namespace

from src import etrm
from src.app import Controller
from src.etrm import sanitizers
from src.utils import perror


def valid_api_key(api_key: str) -> str:
    """eTRM API key validator.

    Use when validating an API key from an `argparse` argument.
    """

    try:
        sanitized_key = sanitizers.sanitize_api_key(api_key)
    except:
        raise TypeError
    return sanitized_key


def valid_measure_id(measure_id: str) -> str:
    """eTRM measure ID validator.

    Use when validating an eTRM measure ID from an `argparse` argument.
    """

    try:
        sanitized_id = sanitizers.sanitize_measure_id(measure_id)
    except:
        raise TypeError
    return sanitized_id


def parse_arguments() -> Namespace:
    parser = ArgumentParser(description='parser for eTRM measure JSON files')

    parser.add_argument(
        '-m', '--measure',
        type=valid_measure_id,
        default=None,
        required=False,
        help='A full measure version ID (i.e., SWAP001-06)'
    )

    key_group = parser.add_mutually_exclusive_group()

    key_group.add_argument(
        '-k', '--key',
        type=valid_api_key,
        default=None,
        required=False,
        help='An eTRM API key (i.e., Token ae163fba910e9c021)'
    )

    key_group.add_argument(
        '-d', '--dev',
        action='store_true'
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    measure_id = getattr(args, 'measure', None)
    dev_mode = getattr(args, 'dev', False)
    if dev_mode:
        api_key = etrm.get_api_key()
    else:
        api_key = getattr(args, 'key', None)

    app = Controller()
    app.start(api_key=api_key, measure_id=measure_id)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Measure parsing interrupted')
    except Exception as err:
        perror('An unhandled error occurred while parsing measure:\n',
              f'{err.__class__.__name__}: {err}')
        print_exc(file=sys.stderr)
