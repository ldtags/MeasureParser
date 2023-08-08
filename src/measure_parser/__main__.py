import sys
from typing import Optional, TextIO
from parser import MeasureParser

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

    with open(filename, 'r') as measure_file:
        out: Optional[TextIO] = None
        if '-console' not in flags: 
            out = open('out.txt', 'w+')

        print(f'\nstarting to parse measure file - {measure_file.name}')
        parser: MeasureParser = MeasureParser(measure_file, out)
        parser.parse()
        print(f'\nfinished parsing measure file - {measure_file.name}\n')

        if out != None:
            out.close()


if __name__ == '__main__':
    main(sys.argv)