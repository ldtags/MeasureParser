from __future__ import annotations
import math
import tkinter as tk
import tkinter.ttk as ttk
from typing import Literal, Callable

from src import assets
from src.app import fonts
from src.app.types import TK_EVENT_BINDING
from src.app.widgets.frames import Frame
from src.app.widgets.labels import Label
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
                 events: list[TK_EVENT_BINDING] | None=None,
                 **kwargs):
        Frame.__init__(self, parent, events, **kwargs)

        self.content_frame = Frame(self, events)
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
                                          level,
                                          events=events)
        self.text_frame.grid(column=0,
                             row=1,
                             sticky=tk.NSEW)

        if img_name is not None:
            self.img_frame = self._ImageFrame(self.content_frame,
                                              self,
                                              img_name=img_name,
                                              events=events)
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
            for event, callback in events or []:
                self.separator.bind(event, callback)

    class _TextFrame(Frame):
        def __init__(self,
                     parent: Frame,
                     title: str,
                     sub_title: str | None=None,
                     level: Literal[0, 1]=0,
                     events: list[TK_EVENT_BINDING] | None=None,
                     **kwargs):
            Frame.__init__(self, parent, events, **kwargs)

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
                               font=title_font,
                               events=events)
            self.title.grid(column=0,
                            row=1,
                            sticky=tk.EW)

            if sub_title is not None:
                self.sub_title = Label(self,
                                       text=sub_title,
                                       font=sub_title_font,
                                       events=events)
                self.sub_title.grid(column=0,
                                    row=2,
                                    sticky=tk.EW)

    class _ImageFrame(Frame):
        def __init__(self,
                     parent: Frame,
                     outer: OptionLabel,
                     img_name: str,
                     events: list[TK_EVENT_BINDING] | None=None,
                     **kwargs):
            Frame.__init__(self, parent, events, **kwargs)

            img = assets.get_image(img_name)
            base_width = img.width
            base_height = img.height
            aspect_ratio = base_height / base_width

            outer.update()
            img_height = outer.winfo_reqheight() * 0.75
            img_width = img_height * aspect_ratio
            size = (math.floor(img_height), math.floor(img_width))
            tk_img = assets.get_tkimage(img_name, size)
            self.img_label = tk.Label(self,
                                      image=tk_img,
                                      bg=self['bg'])
            self.img_label.pack(side=tk.RIGHT,
                                anchor=tk.NE,
                                fill=tk.BOTH)
            for event, callback in events or []:
                self.img_label.bind(event, callback)


class OptionCheckBox(Frame):
    def __init__(self,
                 parent: tk.Frame,
                 text: str,
                 sub_text: str | None=None,
                 events: list[TK_EVENT_BINDING] | None=None,
                 **kwargs):
        Frame.__init__(self, parent, events, **kwargs)

        self.text_label = Label(self,
                                text=text,
                                font=fonts.BODY_BOLD,
                                events=events)
        self.text_label.pack(side=tk.TOP,
                             anchor=tk.NW,
                             fill=tk.X)

        self.check_box_var = tk.IntVar(self, 0)
        self.check_box = tk.Checkbutton(self,
                                        text=sub_text,
                                        font=fonts.BODY_SM,
                                        justify='left',
                                        anchor=tk.NW,
                                        cursor='hand2',
                                        offrelief=tk.SOLID,
                                        variable=self.check_box_var)
        self.check_box.pack(side=tk.TOP,
                            anchor=tk.NW)

        self.bind('<Configure>', self.__wrap)
        for event, callback in events or []:
            self.check_box.bind(event, callback)

    def __wrap(self, *args):
        self.check_box.config(wraplength=self.parent.winfo_width() / 3 - 20)

    def set_command(self, func: Callable[[], None]) -> None:
        self.check_box.config(command=lambda _=None: func())

    def get(self) -> bool:
        val = self.check_box_var.get()
        if val == 1:
            return True
        return False
