import sys
from traceback import print_exc

from src import etrm
from src.app import Controller
from src.utils import perror


def main(dev_mode: bool=True,
         measure_id: str | None=None,
         api_key: str | None=None
        ) -> None:
    if dev_mode and api_key is None:
        api_key = etrm.get_api_key()

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
