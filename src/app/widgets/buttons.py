import tkinter as tk
from typing import Literal, Callable

from src.app import fonts
from src.app.types import TK_EVENT_BINDING


class Button(tk.Frame):
    def __init__(self,
                 parent: tk.Frame,
                 bg: str='#e1e1e1',
                 fg: str = 'black',
                 pady: float=5,
                 padx: float=10,
                 borderwidth: float=0,
                 highlightcolor: str='#bcbcbc',
                 highlightbackground: str='#bcbcbc',
                 highlightthickness: float=2,
                 activebackground: str='#ffffff',
                 relief: str=tk.SOLID,
                 font=fonts.BODY,
                 state: Literal['normal', 'active', 'disabled']='normal',
                 cursor: str='hand2',
                 events: list[TK_EVENT_BINDING] | None=None,
                 **kwargs):
        tk.Frame.__init__(self,
                          parent,
                          borderwidth=borderwidth,
                          highlightbackground=highlightbackground,
                          highlightcolor=highlightcolor,
                          highlightthickness=highlightthickness,
                          bd=0,
                          cursor=cursor)

        self.default_border = highlightcolor

        kwargs['bg'] = bg
        kwargs['fg'] = fg
        kwargs['activebackground'] = activebackground
        kwargs['pady'] = pady
        kwargs['padx'] = padx
        kwargs['borderwidth'] = 0
        kwargs['font'] = font
        kwargs['relief'] = relief
        kwargs['state'] = state
        self.button = tk.Button(self, **kwargs)
        self.button.pack(side=tk.TOP,
                         fill=tk.BOTH,
                         expand=True,
                         padx=(0, 0),
                         pady=(0, 0))

        self.bind('<FocusIn>', self.focus_in)
        self.bind('<FocusOut>', self.focus_out)
        for event, callback in events or []:
            self.bind(event, callback)
            self.button.bind(event, callback)

    def focus_in(self, *args):
        self.configure(highlightbackground='#1281d9',
                       highlightcolor='#1281d9')

    def focus_out(self, *args):
        self.configure(highlightbackground=self.default_border,
                       highlightcolor=self.default_border)

    def set_state(self,
                  state: Literal['normal', 'active', 'disabled']
                 ) -> None:
        match state:
            case 'normal':
                self.config(cursor='hand2')
            case 'active' | 'disabled':
                self.config(cursor='arrow')
            case _:
                pass

        self.button.config(state=state)

    def set_command(self, command: Callable[..., None]):
        self.button.configure(command=command)
