import os

from src import _ROOT

def get_path(file_name: str) -> str:
    """Returns an absolute path to a resource file in the package."""

    file_path = os.path.join(_ROOT, 'resources', file_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'No resource file named {file_name} exists')

    return file_path
