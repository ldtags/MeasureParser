import os
from typing import Literal
from configparser import ConfigParser

from src.etrm.exceptions import ETRMError


_PATH = os.path.abspath(os.path.dirname(__file__))
"""The absolute path to the eTRM package resources folder."""


def get_path(file_name: str) -> str:
    """Returns the absolute path to the eTRM package resource file
    named `file_name`.

    Raises `FileNotFoundError` if the file is not found.
    """

    file_path = os.path.join(_PATH, file_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'No file named {file_name} exists in {_PATH}')

    return file_path


def get_api_key(role: Literal['user', 'admin']='user') -> str:
    match role:
        case 'user':
            source = 'etrm'
        case 'admin':
            source = 'etrm-admin'
        case other:
            raise RuntimeError(f'invalid eTRM role: {other}')

    config = ConfigParser()
    try:
        config_path = get_path('config.ini')
    except FileNotFoundError as err:
        raise ETRMError('eTRM API config.ini file is missing') from err

    config.read(config_path)
    try:
        section = config[source]
    except KeyError:
        raise ETRMError(
            f'eTRM API config.ini file is missing a {source} section'
        )

    token_type = section.get('type', 'Token')
    try:
        token = section['token']
    except KeyError:
        raise ETRMError(
            'eTRM API config.ini file is missing a token field in the'
            f' {source} section'
        )

    return f'{token_type} {token}'
