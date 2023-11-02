from io import TextIOWrapper
import os
from argparse import (
    ArgumentParser,
    FileType,
    Namespace,
    Action
)
from src.measure_parser.parser import MeasureParser

# determines if the input string is a valid path
#
# Parameters:
#   path (str): string being validated
#
# Exceptions:
#   NotADirectoryError: raised if the string is not a valid path
#
# Returns:
#   str: the validated string
def dir_path(path: str) -> str:
    if os.path.isdir(path):
        return path
    raise NotADirectoryError(path)

# validates the arguments extension
#
# Returns:
#   (argparse.Action): an action that ensures the arg is a JSON file
def check_ext(choices):
    class Act(Action):
        def __call__(self,
                     parser: ArgumentParser,
                     namespace: Namespace,
                     file: TextIOWrapper,
                     option_string: str=None):
            ext: str = os.path.splitext(file.name)[1][1:]
            if ext not in choices:
                if option_string:
                    option_string = '({})'.format(option_string)
                else:
                    option_string = ''
                parser.error('{} isn\'t a JSON file'.format(file.name))
            else:
                setattr(namespace, self.dest, file)
    return Act

# parses the command line arguments in sys.argv
#
# Returns:
#   (argparse.Namespace): a namespace containing the associated values
def parse_arguments() -> Namespace:
    argparser: ArgumentParser = ArgumentParser(
        description='parser for eTRM measure JSON files')
    argparser.add_argument(
        'filepath', type=FileType('r'), action=check_ext({'json'}),
        help='filepath to the measure JSON file')
    argparser.add_argument(
        'output', type=dir_path,
        help='directory that will contain the output file')
    return argparser.parse_args()

# controls the flow of processes when parsing the measure
#
# Parameters:
#   args (list[str]): measure parsing arguments, including flags
def main() -> None:
    args: Namespace = parse_arguments()
    try:
        parser: MeasureParser = MeasureParser(args.filepath)
        parser.parse()
        parser.close()
    except OSError as err:
        print(f'ERROR[{err.errno}] - {args.filepath} not found')


if __name__ == '__main__':
    main()