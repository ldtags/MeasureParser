from abc import ABCMeta, abstractmethod
from typing import Optional
from argparse import Namespace

from ..measure import Measure, Characterization, Permutation

class BaseDatabase(metaclass=ABCMeta):
    """Base class for database interaction.

    Specifies which database methods are required by the Measure Parser.
    """

    def get_characterizations(self,
                              measure_json: object
                             ) -> list[Characterization]:
        """Retrieves a list of all characterizations in `measure`.

        Parameters:
            measure `object` : eTRM measure JSON object

        Returns:
            `list[Characterization]` : all characterizations in `measure`

        """

        char_list: list[Characterization] = []
        for char_name in self.get_characterization_names(measure_json):
            content: str | None = getattr(measure_json, char_name, None)
            if content != None:
                char_list.append(Characterization(char_name, content))

        return char_list

    def get_permutations(self, measure_json: object) -> list[Permutation]:
        """Retrieves a list of all permutations found in `measure`.
        
        Parameters:
            measure `object` : eTRM measure JSON object
        
        Returns:
            `list[Permutation]` : all permutations in `measure`
        """

        perm_list: list[Permutation] = []
        for perm_name in self.get_permutation_names():
            verbose_name = getattr(measure_json, perm_name, None)
            if verbose_name != None:
                perm_list.append(Permutation(perm_name, verbose_name))

        return perm_list

    @abstractmethod
    def get_measure(self, *args) -> Measure:
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
