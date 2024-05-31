from __future__ import annotations
import re
import json
import requests
from typing import Optional, Self, TYPE_CHECKING
from argparse import Namespace

from src.dbservice.basedb import BaseDatabase
from src.dbservice.exceptions import (
    DatabaseContentError
)

if TYPE_CHECKING:
    from src.models import Measure


def __sanitize_auth_token(auth_token: str) -> str:
    token_re = re.compile('^[a-zA-Z] .+$')
    if not token_re.fullmatch(auth_token):
        raise RuntimeError(f'{auth_token} is not a valid authorization token')

    token_type, token = auth_token.split(' ', 1)
    if token_type != 'Token':
        raise RuntimeError(
            f'Authorization token type {token_type} is not supported')

    return f'{token_type} {token}'


def __sanitize_measure_id(measure_id: str) -> tuple[str, str]:
    id_re = re.compile('^[a-zA-Z]{2,4}[0-9]{1,3}-[0-9]{1,3}$')
    if not id_re.fullmatch(measure_id):
        raise RuntimeError(f'{measure_id} is not a valid measure id')

    statewide_id, version_id = measure_id.split('-', 1)
    return (statewide_id, version_id)


class ETRMDatabase(BaseDatabase):
    '''Data interaction layer for the eTRM database.'''

    api_url = 'https://www.caetrm.com/api/v1/'

    def __init__(self, auth_token: str):
        self.auth_token = __sanitize_auth_token(auth_token)

    def __enter__(self) -> Self:
        return self

    def close(self):
        del self.auth_token

    def __exit__(self):
        self.close()

    def get_measure(self, measure_id: str) -> object:
        statewide_id, version_id = __sanitize_measure_id(measure_id)
        _url = f'{self.api_url}/{statewide_id}/{version_id}'
        response = requests.get(_url)
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            raise DatabaseContentError(f'Invalid data received from {_url}')

        return response_json


    def get_param_api_names(self, measure: Measure | None = None) -> list[str]:
        pass

    def get_value_table_api_names(self, criteria: list[str]) -> list[str]:
        pass

    def get_shared_table_api_names(self, criteria: list[str]) -> list[str]:
        pass

    def get_table_api_names(self,
                            measure: Measure | None = None,
                            shared: bool = False,
                            nonshared: bool = False) -> list[str]:
        pass

    def get_standard_table_names(self,
                                 measure: Measure | None = None
                                ) -> dict[str, str]:
        pass

    def filter_optional_tables(self,
                               tables: dict[int, str],
                               table_names: list[str],
                               measure: Measure) -> list[str]:
        pass

    def get_table_columns(self,
                          measure: Measure | None = None,
                          table_api_name: str | None = None
                         ) -> dict[str, list[dict[str, str]]]:
        pass

    def get_permutations(self) -> list[tuple[str, str, Optional[str]]]:
        pass

    def get_permutation_data(self, reporting_name: str) -> dict[str, str]:
        pass

    def get_permutation_names(self) -> list[str]:
        pass

    def get_all_characterization_names(self) -> list[str]:
        pass

    def get_characterization_names(self, measure: Namespace) -> list[str]:
        pass
