from __future__ import annotations
import math
import tkinter as tk
import tkinter.ttk as ttk
from typing import Literal, Callable

from .frames import Frame
from .labels import Label

from src import assets
from src.app import fonts
from src.app.exceptions import GUIError


class OptionLabel(Frame):
    def __init__(self,
                 parent: tk.Frame,
                 title: str,
                 sub_title: str | None=None,
                 level: Literal[0, 1]=0,
                 ipadx: tuple[float, float]=(0, 0),
                 ipady: tuple[float, float]=(0, 0),
                 img_name: str | None=None,
                 **kwargs):
        Frame.__init__(self, parent, **kwargs)

        self.content_frame = Frame(self)
        self.content_frame.pack(side=tk.TOP,
                                anchor=tk.NW,
                                fill=tk.BOTH,
                                expand=True,
                                padx=ipadx,
                                pady=ipady)

        self.content_frame.grid_rowconfigure((0, 2), weight=1)
        self.content_frame.grid_rowconfigure((1), weight=0)
        self.content_frame.grid_columnconfigure((0, 1), weight=1)

        self.text_frame = self._TextFrame(self.content_frame,
                                          title,
                                          sub_title,
                                          level)
        self.text_frame.grid(column=0,
                             row=1,
                             sticky=tk.NSEW)

        if img_name is not None:
            self.img_frame = self._ImageFrame(self.content_frame,
                                              self,
                                              img_name=img_name)
            self.img_frame.grid(column=1,
                                row=1,
                                sticky=tk.NSEW,
                                padx=(10, 10))

        if level == 0:
            self.separator = ttk.Separator(self)
            self.separator.pack(side=tk.BOTTOM,
                                anchor=tk.NW,
                                fill=tk.X,
                                expand=True,
                                pady=(5, 0))

    class _TextFrame(Frame):
        def __init__(self,
                     parent: Frame,
                     title: str,
                     sub_title: str | None=None,
                     level: Literal[0, 1]=0,
                     **kwargs):
            Frame.__init__(self, parent, **kwargs)

            sub_title_font = fonts.BODY
            match level:
                case 0:
                    title_font = fonts.SUB_HEADER
                case 1:
                    title_font = fonts.BODY_BOLD
                case x:
                    raise GUIError(f'Invalid precedence level: {x}')

            self.grid_columnconfigure((0), weight=1)
            self.grid_rowconfigure((0, 3), weight=1)
            self.grid_rowconfigure((1, 2), weight=0)

            self.title = Label(self,
                               text=title,
                               font=title_font)
            self.title.grid(column=0,
                            row=1,
                            sticky=tk.EW)

            if sub_title is not None:
                self.sub_title = Label(self,
                                       text=sub_title,
                                       font=sub_title_font)
                self.sub_title.grid(column=0,
                                    row=2,
                                    sticky=tk.EW)

    class _ImageFrame(Frame):
        def __init__(self,
                     parent: Frame,
                     outer: OptionLabel,
                     img_name: str,
                     **kwargs):
            Frame.__init__(self, parent, **kwargs)

            img = assets.get_image(img_name)
            base_width = img.width
            base_height = img.height
            aspect_ratio = base_height / base_width

            outer.update()
            img_height = outer.winfo_reqheight() * 0.75
            img_width = img_height * aspect_ratio
            size = (math.floor(img_height), math.floor(img_width))
            tk_img = assets.get_tkimage(img_name, size)
            self.img_label = Label(self,
                                   image=tk_img,
                                   bg=self['bg'])
            self.img_label.pack(side=tk.RIGHT,
                                anchor=tk.NE,
                                fill=tk.BOTH)


class OptionCheckBox(Frame):
    def __init__(self,
                 parent: tk.Frame,
                 text: str,
                 sub_text: str | None=None,
                 **kwargs):
        Frame.__init__(self, parent, **kwargs)

        self.style = ttk.Style()
        self.text_label = Label(
            self,
            text=text,
            font=fonts.BODY_BOLD
        )
        self.text_label.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.X
        )

        self.check_box_var = tk.IntVar(self, 0)
        self.style.configure(
            'TCheckbutton',
            font=fonts.BODY_SM,
            relief=tk.FLAT
        )
        self.check_box = ttk.Checkbutton(
            self,
            text=sub_text,
            cursor='hand2',
            variable=self.check_box_var,
            style='TCheckbutton'
        )
        self.check_box.pack(
            side=tk.TOP,
            anchor=tk.NW
        )

        self.bind('<Configure>', self.__wrap)

    @property
    def state(self) -> Literal['normal', 'disabled', 'active']:
        return self.check_box.cget('state')

    @state.setter
    def state(self, state: Literal['normal', 'disabled', 'active']) -> None:
        self.check_box.config(state=state)

    def __wrap(self, *args) -> None:
        self.update()
        self.style.configure(
            'TCheckbutton',
            wraplength=self.winfo_width()
        )

    def disable(self) -> None:
        self.check_box.config(
            state=tk.DISABLED,
            cursor='arrow'
        )

    def enable(self) -> None:
        self.check_box.config(
            state=tk.NORMAL,
            cursor='hand2'
        )

    def set_command(self, func: Callable[[], None]) -> None:
        self.check_box.config(command=lambda _=None: func())

    def configure(self, **kw) -> None:
        self.check_box.configure(**kw)

    def get(self) -> bool:
        val = self.check_box_var.get()
        if val == 1:
            return True
        return False

    def set(self, state: bool) -> None:
        if state:
            _state = 1
        else:
            _state = 0
        self.check_box_var.set(_state)
