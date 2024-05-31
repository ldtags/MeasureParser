from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import Optional, TYPE_CHECKING, TypeVar
from argparse import Namespace

if TYPE_CHECKING:
    from src.models import Measure


_T = TypeVar('_T')


class BaseDatabase(metaclass=ABCMeta):
    """Base class for database interaction.

    Specifies which database methods are required by the Measure Parser.
    """

    @abstractmethod
    def get_measure(self, *args) -> object:
        ...

    @abstractmethod
    def get_param_api_names(self, measure: Measure | None = None) -> list[str]:
        ...

    @abstractmethod
    def get_value_table_api_names(self, criteria: list[str]) -> list[str]:
        ...

    @abstractmethod
    def get_shared_table_api_names(self, criteria: list[str]) -> list[str]:
        ...

    @abstractmethod
    def get_table_api_names(self,
                            measure: Measure | None = None,
                            shared: bool = False,
                            nonshared: bool = False) -> list[str]:
        ...

    @abstractmethod
    def get_standard_table_names(self,
                                 measure: Measure | None = None
                                ) -> dict[str, str]:
        ...

    @abstractmethod
    def filter_optional_tables(self,
                               tables: dict[int, str],
                               table_names: list[str],
                               measure: Measure) -> list[str]:
        ...

    @abstractmethod
    def get_table_columns(self,
                          measure: Measure | None = None,
                          table_api_name: str | None = None
                         ) -> dict[str, list[dict[str, str]]]:
        ...

    @abstractmethod
    def get_permutations(self) -> list[tuple[str, str, Optional[str]]]:
        ...

    @abstractmethod
    def get_permutation_data(self, reporting_name: str) -> dict[str, str]:
        ...

    @abstractmethod
    def get_permutation_names(self) -> list[str]:
        ...

    @abstractmethod
    def get_all_characterization_names(self) -> list[str]:
        ...

    @abstractmethod
    def get_characterization_names(self, measure: Namespace) -> list[str]:
        ...

def queryfy(elements: list[str | int]) -> str:
    '''Generates a list that is understood by the SQL interpreter.'''

    query_list: str = '('
    length: int = len(elements)
    for i, element in enumerate(elements):
        match element:
            case str():
                query_list += '\"' + element + '\"'
            case int():
                query_list += str(element)
            case _:
                raise RuntimeError(f'Object type [{str(type(element))}]'
                                    ' is not supported by queryfy')

        if i != length - 1:
            query_list += ', '

    query_list += ')'
    return query_list


def listify(tuples: list[tuple[_T]]) -> list[_T]:
    '''Generates a list of the first elements of each tuple in `tuples`.'''

    if type(tuples) is not list:
        return []

    if len(tuples) == 0:
        return []

    first = tuples[0]
    if type(first) is not tuple:
        return []

    if len(first) == 0:
        return []

    return [element[0] for element in tuples]
