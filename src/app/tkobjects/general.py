import tkinter as tk
from tkinter import ttk
from typing import Literal

from src import utils
from src.app import fonts
from src.app.tkobjects.frames import Frame
from src.app.exceptions import GUIError


class OptionLabel(Frame):
    def __init__(self,
                 parent: tk.Frame,
                 title: str,
                 sub_title: str,
                 level: Literal[0, 1]=0,
                 separate: bool=False,
                 image_asset: str | None=None,
                 **kwargs):
        super().__init__(parent, **kwargs)

        sub_title_font = fonts.BODY
        match level:
            case 0:
                title_font = fonts.SUB_HEADER
            case 1:
                title_font = fonts.BODY_BOLD
            case x:
                raise GUIError(f'Invalid level: {x}')

        self.grid_columnconfigure((0), weight=1)
        self.grid_columnconfigure((1), weight=0)

        colspan = 2 if image_asset else 1

        self.title = tk.Label(self,
                              text=title,
                              font=title_font,
                              bg=self['bg'],
                              wraplength=self.parent.winfo_width(),
                              justify=tk.LEFT)
        self.title.grid(row=0,
                        column=0,
                        columnspan=colspan,
                        sticky=tk.NW)

        self.sub_title = tk.Label(self,
                                  text=sub_title,
                                  font=sub_title_font,
                                  bg=self['bg'],
                                  wraplength=self.parent.winfo_width(),
                                  justify=tk.LEFT)
        self.sub_title.grid(row=1,
                            column=0,
                            columnspan=colspan,
                            sticky=tk.NW)

        if image_asset:
            tkimage = utils.get_tkimage(image_asset)
            self.image = tk.Label(self,
                                  image=tkimage,
                                  bg=self['bg'])
            self.image.grid(row=0,
                            rowspan=2,
                            column=1,
                            sticky=tk.NSEW)

        if separate:
            self.separator = ttk.Separator(self)
            self.separator.grid(row=2,
                                column=0,
                                columnspan=2,
                                sticky=tk.NSEW,
                                padx=(0, 0),
                                pady=(5, 5))

        self.title.bind('<Configure>', lambda _: self.rewrap(self.title))
        self.sub_title.bind('<Configure>',
                            lambda _: self.rewrap(self.sub_title))

    def rewrap(self, label: tk.Label):
        label.config(wraplength=self.parent.winfo_width())


class Option(Frame):
    def __init__(self,
                 parent: tk.Frame,
                 title: str,
                 sub_title: str,
                 widget: tk.Widget,
                 level: Literal[0, 1]=0,
                 wpadx: tuple[int, int]=(0, 0),
                 wpady: tuple[int, int]=(0, 0),
                 **kwargs):
        super().__init__(parent, **kwargs)

        wrap_len = parent.winfo_width()

        self.label = OptionLabel(self,
                                 title=title,
                                 sub_title=sub_title,
                                 level=level,
                                 wraplength=wrap_len)
        self.label.pack(side=tk.TOP,
                        anchor=tk.N,
                        fill=tk.X,
                        padx=(0, 0),
                        pady=(0, 5))

        self.widget = widget
        self.widget.pack(side=tk.TOP,
                         anchor=tk.N,
                         fill=tk.X,
                         padx=wpadx,
                         pady=(wpady[0], 5))

        self._err_var = tk.StringVar(self, '')
        self._err_label = tk.Label(self,
                                   textvariable=self._err_var,
                                   font=fonts.BODY,
                                   bg=self['bg'],
                                   fg='red',
                                   wraplength=wrap_len + wpadx[0] + wpadx[1])
        self._err_label.pack(side=tk.TOP,
                             anchor=tk.N,
                             fill=tk.X,
                             padx=wpadx,
                             pady=(0, wpady[1]))

    def display_err(self, err_text: str):
        self._err_var.set(err_text)

    def clear_err(self):
        self._err_var.set('')
