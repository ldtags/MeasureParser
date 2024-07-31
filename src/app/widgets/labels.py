import tkinter as tk
from typing import Literal

from .misc import Widget


class Label(Widget):
    def __init__(self,
                 parent: tk.Misc,
                 justify: Literal['left', 'center', 'right']='left',
                 bg: str | None=None,
                 **kwargs):
        self.parent = parent

        if justify == 'left':
            anchor = tk.W
        elif justify == 'right':
            anchor = tk.E
        else:
            anchor = tk.CENTER

        kw = {
            'justify': justify,
            'anchor': anchor
        }
        for key, val in kwargs.items():
            kw[key] = val
        Widget.__init__(self, parent, 'label', kw=kw)

        # defaults for optional args that rely on the parent object
        try:
            self.config(bg=bg or parent['bg'])
        except TypeError:
            pass

        self.bind('<Configure>', self.__wrap)
        self.bind('<Button-1>', self.__focus)

    def __wrap(self, *args):
        self.config(wraplength=self.parent.winfo_width())

    def __focus(self, *args):
        self.focus()
