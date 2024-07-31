import tkinter as tk
from typing import Literal, Callable

from .misc import Widget

from src.app import fonts
from src.app.types import TK_EVENT_BINDING


class _Button(Widget):
    def __init__(self,
                 parent: tk.Misc,
                 bg: str='#e1e1e1',
                 fg: str='black',
                 border_width: float=1,
                 border_color: str='#adadad',
                 active_background: str='#ffffff',
                 relief: str=tk.SOLID,
                 state: Literal['normal', 'active', 'disabled']='normal',
                 cursor: str='hand2',
                 command: Callable[[tk.Event], None] | None=None,
                 font: tuple=fonts.BODY,
                 events=None,
                 **kwargs):
        """Construct a button widget with the parent MASTER.

        STANDARD OPTIONS

            activebackground, activeforeground, anchor,
            background, bitmap, borderwidth, cursor,
            disabledforeground, font, foreground
            highlightbackground, highlightcolor,
            highlightthickness, image, justify,
            padx, pady, relief, repeatdelay,
            repeatinterval, takefocus, text,
            textvariable, underline, wraplength

        WIDGET-SPECIFIC OPTIONS

            command, compound, default, height,
            overrelief, state, width
        """

        kw = {
            'bg': bg,
            'fg': fg,
            'borderwidth': 0,
            'highlightthickness': border_width,
            'activebackground': active_background,
            'relief': relief,
            'state': state,
            'cursor': cursor,
            'command': command,
            'font': font
        }
        for key, val in kwargs.items():
            try:
                kw[key]
            except KeyError:
                kw[key] = val
        Widget.__init__(self, parent, 'button', cnf={}, kw=kw)
        self.configure(
            highlightbackground=border_color,
            highlightcolor=border_color
        )

    def set_state(self, state):
        self.configure(state=state)

    def set_command(self, command):
        self.configure(command=command)


class Button(Widget):
    def __init__(self,
                 parent: tk.Misc,
                 bg: str='#e1e1e1',
                 fg: str='black',
                 border_width: float=1,
                 border_color: str='#adadad',
                 active_background: str='#ffffff',
                 relief: str=tk.SOLID,
                 state: Literal['normal', 'active', 'disabled']='normal',
                 cursor: str='hand2',
                 command: Callable[[tk.Event], None] | None=None,
                 font: tuple=fonts.BODY,
                 **kwargs):
        kw = {
            'highlightcolor': border_color,
            'highlightbackground': border_color,
            'highlightthickness': border_width
        }
        Widget.__init__(self, parent, 'frame', cnf={}, kw=kw)
        

# class Button(tk.Frame):
#     def __init__(self,
#                  parent: tk.Frame,
#                  bg: str='#e1e1e1',
#                  fg: str = 'black',
#                  pady: float=5,
#                  padx: float=10,
#                  borderwidth: float=0,
#                  highlightcolor: str='#bcbcbc',
#                  highlightbackground: str='#bcbcbc',
#                  highlightthickness: float=2,
#                  activebackground: str='#ffffff',
#                  relief: str=tk.SOLID,
#                  font=fonts.BODY,
#                  state: Literal['normal', 'active', 'disabled']='normal',
#                  cursor: str='hand2',
#                  events: list[TK_EVENT_BINDING] | None=None,
#                  **kwargs):
#         tk.Frame.__init__(self,
#                           parent,
#                           borderwidth=borderwidth,
#                           highlightbackground=highlightbackground,
#                           highlightcolor=highlightcolor,
#                           highlightthickness=highlightthickness,
#                           bd=0,
#                           cursor=cursor)

#         self.default_border = highlightcolor

#         kwargs['bg'] = bg
#         kwargs['fg'] = fg
#         kwargs['activebackground'] = activebackground
#         kwargs['pady'] = pady
#         kwargs['padx'] = padx
#         kwargs['borderwidth'] = 0
#         kwargs['font'] = font
#         kwargs['relief'] = relief
#         kwargs['state'] = state
#         self.button = tk.Button(self, **kwargs)
#         self.button.pack(side=tk.TOP,
#                          fill=tk.BOTH,
#                          expand=True,
#                          padx=(0, 0),
#                          pady=(0, 0))

#         self.bind('<FocusIn>', self.focus_in)
#         self.bind('<FocusOut>', self.focus_out)
#         for event, callback in events or []:
#             self.bind(event, callback)
#             self.button.bind(event, callback)

#     def focus_in(self, *args):
#         self.configure(highlightbackground='#1281d9',
#                        highlightcolor='#1281d9')

#     def focus_out(self, *args):
#         self.configure(highlightbackground=self.default_border,
#                        highlightcolor=self.default_border)

#     def set_state(self,
#                   state: Literal['normal', 'active', 'disabled']
#                  ) -> None:
#         match state:
#             case 'normal':
#                 self.config(cursor='hand2')
#             case 'active' | 'disabled':
#                 self.config(cursor='arrow')
#             case _:
#                 pass

#         self.button.config(state=state)

#     def set_command(self, command: Callable[..., None]):
#         self.button.configure(command=command)
