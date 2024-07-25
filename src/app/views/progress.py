import tkinter as tk

from src.app.widgets import Page


class ProgressPage(Page):
    key = 'progress'

    def __init__(self, parent: tk.Misc, root: tk.Tk, **kwargs):
        Page.__init__(parent, root, **kwargs)

        
