import os

__all__ = [
    'dbservice',
    'exceptions',
    'htmlparser',
    'parser',
    'objects',
    'utils'
]

_ROOT = os.path.abspath(os.path.dirname(__file__))
def get_path(filename: str, directory: str='data') -> str:
    '''Returns an absolute path to a file in the package'''
    return os.path.join(_ROOT, directory, filename)