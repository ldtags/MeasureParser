import tkinter as tk
from typing import overload


class Frame(tk.Frame):
    def __init__(self, parent: tk.Misc, **kwargs):
        try:
            kwargs['bg']
        except KeyError:
            if isinstance(parent, tk.Frame):
                kwargs['bg'] = parent['bg']

        super().__init__(parent, **kwargs)

        self.parent = parent
        self.bind('<Button-1>', lambda _: self.focus())


class Page(Frame):
    key: str

    def __init__(self, parent: tk.Misc, root: tk.Tk, **kwargs):
        self.parent = parent
        self.root = root

        super().__init__(parent, **kwargs)

    @overload
    def show(self):
        ...


class Container(Frame):
    def __init__(self, root: tk.Tk, **kwargs):
        self.root = root

        Frame.__init__(self, root, **kwargs)


class Toplevel(tk.Toplevel):
    def __init__(self, parent: tk.BaseWidget, **kwargs):
        self.parent = parent
        super().__init__(parent, **kwargs)

        self.bind('<Button-1>', self.focus)

        x_offset = parent.winfo_width() // 2 - self.winfo_width() // 2
        y_offset = parent.winfo_height() // 2 - self.winfo_height() // 2
        x = parent.winfo_x() + x_offset
        y = parent.winfo_y() + y_offset
        self.geometry(f'+{x}+{y}')
