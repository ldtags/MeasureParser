import os


_ROOT = os.path.abspath(os.path.dirname(__file__))


def get_path(*path_fragments: str, exists: bool=True) -> str:
    file_path = os.path.join(_ROOT, *path_fragments)
    if not os.path.exists(file_path) and exists:
        raise FileExistsError(f'No file with the path {file_path} exists')

    return file_path
