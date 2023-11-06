import os
from io import TextIOWrapper
from typing import Type
from gooey import (
    Gooey,
    GooeyParser
)
from argparse import (
    FileType,
    Namespace
)
from src.measure_parser.parser import MeasureParser


# parses the command line arguments in sys.argv
#
# Returns:
#   (argparse.Namespace): a namespace containing the associated values
def parse_arguments() -> Namespace:
    argparser: GooeyParser = GooeyParser(
        description='parser for eTRM measure JSON files')

    argparser.add_argument('measure_file', widget='FileChooser',
        type=FileType('r'),
        help='filepath to the measure JSON file',
        gooey_options={
            'wildcard': 'JSON file (*.json)|*.json'
        })

    argparser.add_argument('output', widget='DirChooser',
        help='directory that will contain the output file')

    return argparser.parse_args()

# controls the flow of processes when parsing the measure
#
# Parameters:
#   args (list[str]): measure parsing arguments, including flags
@Gooey (
    program_name='eTRM Measure Parser',
    program_description='Parses and validates eTRM measures'
)
def main() -> None:
    args: Namespace = parse_arguments()
    measure_file: TextIOWrapper = getattr(args, 'measure_file', None)
    if (measure_file == None):
        print('measure JSON file not found')

    try:
        parser: MeasureParser = MeasureParser(measure_file)
        parser.parse()
        parser.close()
    except OSError as err:
        print(f'ERROR[{err.errno}] - {measure_file.name} not found')


if __name__ == '__main__':
    main()