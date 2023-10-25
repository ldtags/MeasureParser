import sys
from src.measure_parser.parser import MeasureParser

# controls the flow of processes when parsing the measure
#
# Parameters:
#   args (list[str]): measure parsing arguments, including flags
def main(args: list[str]) -> None:
    flags: list[str] = list(filter(lambda arg: arg[0] == '-', args))
    for flag in flags:
        args.remove(flag)
    filename: str = None
    try:
        filename = args[1]
    except IndexError:
        print('ERROR - filename missing')
        return
    except Exception as err:
        print(f'ERROR - something went wrong when parsing args:\n{err}')
        return

    try:
        parser: MeasureParser = MeasureParser(filename)
        parser.parse()
        parser.close()
    except OSError as err:
        print(f'ERROR[{err.errno}] - {filename} not found')


if __name__ == '__main__':
    main(sys.argv)