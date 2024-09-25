import unittest as ut

from tests.parser import model_construction


def suites() -> list[ut.TestSuite]:
    return [
        model_construction.suite()
    ]


if __name__ == '__main__':
    runner = ut.TextTestRunner()
    for suite in suites():
        runner.run(suite)
