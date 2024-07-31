import tkinter as tk

from src.app.widgets import (
    Page
)


class ResultsPage(Page):
    key = 'results'

    def __init__(self, parent: tk.Misc, root: tk.Tk, **kwargs):
        Page.__init__(self, parent, root, **kwargs)
