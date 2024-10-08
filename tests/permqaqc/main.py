import unittest as ut

from tests.permqaqc import process_validation


def suites() -> list[ut.TestSuite]:
    return [
        process_validation.suite()
    ]


if __name__ == '__main__':
    runner = ut.TextTestRunner()
    for suite in suites():
        runner.run(suite)
