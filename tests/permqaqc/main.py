import unittest as ut

from tests.permqaqc import datavalidation


def suites() -> list[ut.TestSuite]:
    return [
        datavalidation.suite()
    ]


if __name__ == '__main__':
    runner = ut.TextTestRunner()
    for suite in suites():
        runner.run(suite)
