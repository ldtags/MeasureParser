"""Measure Parser database interaction layer"""

from measureparser.dbservice.localdb import (
    LocalDatabase
)

from measureparser.dbservice.etrmdb import (
    ETRMDatabase
)

from measureparser.dbservice.basedb import (
    BaseDatabase
)


def get_all_characterization_names() -> list[str]:
    return LocalDatabase().get_all_characterization_names()


# def get_characterizations(self,
#                           measure_json: object
#                          ) -> list[Characterization]:
#     """Retrieves a list of all characterizations in `measure`.
#     Parameters:
#         measure `object` : eTRM measure JSON object

#     Returns:
#         `list[Characterization]` : all characterizations in `measure`
#     """

#     char_list: list[Characterization] = []
#     for char_name in self.get_characterization_names(measure_json):
#         content: str | None = getattr(measure_json, char_name, None)
#         if content != None:
#             char_list.append(Characterization(char_name, content))
#     return char_list

# def get_permutations(self, measure_json: object) -> list[Permutation]:
#     """Retrieves a list of all permutations found in `measure`.
    
#     Parameters:
#         measure `object` : eTRM measure JSON object
    
#     Returns:
#         `list[Permutation]` : all permutations in `measure`
#     """

#     perm_list: list[Permutation] = []
#     for perm_name in self.get_permutation_names():
#         verbose_name = getattr(measure_json, perm_name, None)
#         if verbose_name != None:
#             perm_list.append(Permutation(perm_name, verbose_name))

#     return perm_list
