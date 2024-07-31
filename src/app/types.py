import tkinter as tk
from typing import Callable


TK_EVENT_BINDING = tuple[str, Callable[[tk.Event], None]]
