import tkinter as tk
from typing import Literal, Callable

from .misc import Widget

from src.app import fonts


class _Button(Widget):
    def __init__(self,
                 parent: tk.Misc,
                 bg: str='#e1e1e1',
                 fg: str='black',
                 active_background: str='#ffffff',
                 relief: str=tk.SOLID,
                 state: Literal['normal', 'active', 'disabled']='normal',
                 cursor: str='hand2',
                 command: Callable[[tk.Event], None] | None=None,
                 font: tuple=fonts.BODY,
                 **kwargs):
        kw = {
            'bg': bg,
            'fg': fg,
            'borderwidth': 0,
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
            'highlightcolor': border_color,
            'highlightbackground': border_color,
            'highlightthickness': border_width,
            'cursor': cursor,
            'bd': 0
        }
        Widget.__init__(self, parent, 'frame', cnf={}, kw=kw)

        self._button = _Button(
            self,
            bg=bg,
            fg=fg,
            active_background=active_background,
            relief=relief,
            state=state,
            command=command,
            font=font,
            **kwargs
        )
        self._button.pack(side=tk.TOP,
                          anchor=tk.NW,
                          fill=tk.BOTH,
                          expand=tk.TRUE)

        if command:
            self.bind('<Button-1>', command)

    def configure(self, **kw) -> None:
        self._button.configure(**kw)

    def invoke(self):
        """Invoke the command associated with the button.

        The return value is the return value from the command,
        or an empty string if there is no command associated with
        the button. This command is ignored if the button's state
        is disabled.
        """

        return self._button.tk.call(self._button._w, 'invoke')

    def flash(self):
        """Flash the button.

        This is accomplished by redisplaying
        the button several times, alternating between active and
        normal colors. At the end of the flash the button is left
        in the same normal/active state as when the command was
        invoked. This command is ignored if the button's state is
        disabled.
        """

        self._button.tk.call(self._button._w, 'flash')

    def set_state(self, state):
        self.configure(state=state)

    def set_command(self, command):
        self.configure(command=command)
