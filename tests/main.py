import sys
import os
import unittest as ut

from tests import permqaqc


MODULES = {
    'permqaqc': permqaqc.suites
}


def main(*unit_modules: str):
    if unit_modules != None:
        if 'all' in unit_modules:
            unit_modules = (MODULES.keys())
        else:
            for module in unit_modules:
                if module not in MODULES:
                    print(f'unknown module: {module}', file=sys.stderr)
                    print(f'supported modules - {MODULES}', file=sys.stderr)
                    sys.exit(os.EX_OK)

        test_suites: list[ut.TestSuite] = []
        for module in unit_modules:
            test_suites.extend(MODULES[module]())

        runner = ut.TextTestRunner()
        for test_suite in test_suites:
            runner.run(test_suite)


if __name__ == '__main__':
    main()
