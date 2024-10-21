import argparse as ap

from src.etrm import sanitizers
import src.__main__ as src
import tests.main as tests


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


def parse_args() -> ap.Namespace:
    parser = ap.ArgumentParser()

    subparsers = parser.add_subparsers(help="subcommand help")

    app_parser = subparsers.add_parser("app", help="arguments for running the app")
    app_parser.add_argument(
        "-m",
        "--measure",
        type=valid_measure_id,
        default=None,
        required=False,
        help="A full measure version ID (i.e., SWAP001-06)",
    )

    key_group = app_parser.add_mutually_exclusive_group()
    key_group.add_argument(
        "-k",
        "--key",
        type=valid_api_key,
        default=None,
        required=False,
        help="An eTRM API key (i.e., Token ae163fba910e9c021)",
    )

    key_group.add_argument("-d", "--dev", action="store_true")

    app_parser.set_defaults(run_type="app")

    test_parser = subparsers.add_parser("test", help="arguments for testing the app")
    test_parser.add_argument(
        "-u",
        "--unit",
        nargs="*",
        type=str,
        choices=["parser", "permqaqc"],
        help="specify the modules to unit test",
    )

    test_parser.set_defaults(run_type="test")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_type = getattr(args, "run_type", None)
    match run_type:
        case "app":
            dev_mode = getattr(args, "dev")
            api_key = getattr(args, "key")
            measure_id = getattr(args, "measure")
            src.main(dev_mode, measure_id, api_key)
        case "test":
            unit_modules = getattr(args, "unit", [])
            tests.main(*unit_modules)
        case other:
            raise ValueError(f"Unknown run type: {other}")
