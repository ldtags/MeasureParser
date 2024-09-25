import unittest as ut
from typing import Type


def get_test_methods(test_case: Type[ut.TestCase]) -> list[ut.TestCase]:
    return [
        test_case(func)
            for func
            in dir(test_case)
            if (
                callable(getattr(test_case, func))
                    and func.startswith('test_')
            )
    ]
