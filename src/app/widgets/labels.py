import tkinter as tk
from typing import Literal

from src.app.widgets.misc import Widget


class Label(Widget):
    def __init__(
        self,
        parent: tk.Misc,
        justify: Literal["left", "center", "right"] = "left",
        text_color: str = "black",
        variable: tk.StringVar | None = None,
        bg: str | None = None,
        **kwargs
    ) -> None:
        self.parent = parent

        if justify == "left":
            anchor = tk.W
        elif justify == "right":
            anchor = tk.E
        else:
            anchor = tk.CENTER

        kw = {
            "justify": justify,
            "anchor": anchor,
            "fg": text_color,
            "textvariable": variable,
        }
        for key, val in kwargs.items():
            kw[key] = val
        Widget.__init__(self, parent, "label", kw=kw)

        # defaults for optional args that rely on the parent object
        try:
            bg = bg or parent["bg"]
            self.config(bg=bg)
        except TypeError:
            pass

        self.bind("<Configure>", self.__wrap)
        self.bind("<Button-1>", self.__focus)

    def __wrap(self, *args):
        self.config(wraplength=self.parent.winfo_width())

    def __focus(self, *args):
        self.focus()


class ErrorLabel(Label):
    def __init__(
        self,
        parent: tk.Misc,
        justify: Literal["left", "center", "right"] = "left",
        bg: str | None = None,
    ) -> None:
        self._var = tk.StringVar(parent, "")
        super().__init__(
            parent, justify=justify, text_color="#ff0000", variable=self._var, bg=bg
        )

    def set(self, text: str) -> None:
        self._var.set(text)

    def clear(self) -> None:
        self._var.set("")
