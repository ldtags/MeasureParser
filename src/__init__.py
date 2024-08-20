"""eTRM Measure JSON Parser"""

__author__ = 'Liam Tangney'
__version__ = '1.1.0'
__all__ = ['parser']

import os
import logging


logging.basicConfig(filename='parser.log', level=logging.INFO)


_ROOT = os.path.abspath(os.path.dirname(__file__))


def get_path(*path_fragments: str) -> str:
    file_path = os.path.join(_ROOT, *path_fragments)
    if not os.path.exists(file_path):
        raise FileExistsError(f'No file with the path {file_path} exists')

    return file_path
