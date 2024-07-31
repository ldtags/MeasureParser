import tkinter as tk
from typing import Literal

from src.app.types import TK_EVENT_BINDING


class Label(tk.Label):
    def __init__(self,
                 parent: tk.Misc,
                 justify: Literal['left', 'center', 'right']='left',
                 bg: str | None=None,
                 events: list[TK_EVENT_BINDING]=None,
                 **kwargs):
        self.parent = parent

        if justify == 'left':
            anchor = tk.W
        elif justify == 'right':
            anchor = tk.E
        else:
            anchor = tk.CENTER

        tk.Label.__init__(self,
                          parent,
                          justify=justify,
                          anchor=anchor,
                          **kwargs)

        # defaults for optional args that rely on the parent object
        try:
            self.config(
                bg=bg or parent['bg']
            )
        except TypeError:
            pass

        self.bind('<Configure>', self.__wrap)
        self.bind('<Button-1>', self.__focus)
        for event, callback in events or []:
            self.bind(event, callback)

    def __wrap(self, *args):
        self.config(wraplength=self.parent.winfo_width())

    def __focus(self, *args):
        self.focus()
