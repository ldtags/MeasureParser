import os
from PIL import ImageTk, Image

from src import _ROOT


def get_path(file_name: str) -> str:
    """Returns an absolute path to an asset file."""

    file_path = os.path.join(_ROOT, "assets", file_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No asset named {file_name} exists")
    return file_path


_IMAGES: dict[str, Image.Image] = {}


def get_image(file_name: str) -> Image.Image:
    file_path = get_path(file_name)
    try:
        image = _IMAGES[file_path]
    except KeyError:
        image = Image.open(file_path)
        _IMAGES[file_path] = image
    return image


# storing images in a dict solves the issue of needing to make
# any new image an attribute of a class
_TK_IMAGES: dict[str, ImageTk.PhotoImage] = {}


def get_tkimage(
    file_name: str, size: tuple[int, int] | None = None
) -> ImageTk.PhotoImage:
    """Returns an image asset that can be used in a tkinter widget."""

    file_path = get_path(file_name)
    key = f"{file_path}{str(size)}"
    try:
        tk_image = _TK_IMAGES[key]
    except KeyError:
        image = Image.open(file_path)
        if size is not None:
            image = image.resize(size)
        tk_image = ImageTk.PhotoImage(image)
        _TK_IMAGES[key] = tk_image
    return tk_image
