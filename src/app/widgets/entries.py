import tkinter as tk
import tkinter.filedialog as filedialog
from typing import Literal

from .misc import Widget
from .labels import Label
from .frames import Frame
from .buttons import Button

from src import utils, _ROOT
from src.app import fonts


__all__ = [
    'Entry',
    'FileNameEntry',
    'FileEntry'
]


class _Entry(Widget, tk.XView):
    def __init__(self,
                 parent: tk.Misc,
                 text_color: str='black',
                 relief: str=tk.SOLID,
                 font: tuple[str, int, str | None]=fonts.BODY,
                 **kwargs):
        kw = {
            'fg': text_color,
            'relief': relief,
            'font': font,
            'borderwidth': 0
        }
        for key, val in kwargs.items():
            kw[key] = val
        Widget.__init__(self, parent, 'entry', kw=kw)


class Entry(Widget):
    """Custom Tkinter entry widget."""

    def __init__(self,
                 parent: tk.Misc,
                 placeholder: str | None=None,
                 placeholder_color: str='grey',
                 text: str | None=None,
                 text_color: str='black',
                 relief: str=tk.FLAT,
                 border_width: float=1,
                 border_color: str='#adadad',
                 font: tuple[str, int, str | None]=fonts.BODY,
                 bg: str='#ffffff',
                 disabledbackground: str='#dfdfdf',
                 ipadx: float=3,
                 **kwargs):
        """Initializes a new custom Tkinter entry widget.

        Used to create a Tkinter entry with more customization options.

        Supports all standard Tkinter entry options, as well as:
            - `placeholder` placeholder text that disappears when the entry
            is focused.

            - `placeholder_color` the color of the placeholder text. This
            cannot be the same color as `text_color`.

            - `ipadx` the left-sided internal padding of the entry.

            - `border_width` specifies the width of the entry border.

            - `border_color` specifies the color of the entry border.

        Some standard Tkinter entry options have been renamed; such as:
            - `text_color` replaces `fg`

        If a standard Tkinter entry options that has been replaced is included
        in `kwargs`, it will override the replacement arg.
        """

        kw = {
            'highlightcolor': border_color,
            'highlightbackground': border_color,
            'highlightthickness': border_width,
            'height': font[1],
            'bg': bg
        }
        Widget.__init__(self, parent, 'frame', cnf={}, kw=kw)

        assert text_color != placeholder_color

        self.pad_frame = Frame(self, relief=relief, bg=bg)
        self.pad_frame.pack(
            side=tk.RIGHT,
            anchor=tk.NW,
            fill=tk.BOTH,
            expand=tk.TRUE
        )

        self.is_placeholder = False
        self.placeholder = placeholder
        self.placeholder_color = placeholder_color
        self.text_color = text_color
        self.text = text
        self.entry = _Entry(
            self.pad_frame,
            text_color,
            relief,
            font,
            bg=bg,
            disabledbackground=disabledbackground,
            **kwargs
        )
        self.entry.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.BOTH,
            expand=tk.TRUE,
            padx=(ipadx, 0)
        )

        if text:
            self.insert(0, text)
        elif placeholder:
            self.put_placeholder()

        self.bind('<FocusIn>', self.focus_in)
        self.bind('<FocusOut>', self.focus_out)
        self.pad_frame.bind('<Button-1>', self.__on_pad_frame_click)

    def delete(self, first: str | int, last: str | int | None=None) -> None:
        """Delete text from FIRST to LAST (not included)."""

        self.entry.tk.call(self.entry._w, 'delete', first, last)

    def get(self) -> str:
        """Return the text."""

        return self.entry.tk.call(self.entry._w, 'get')

    def icursor(self, index: int) -> None:
        """Insert cursor at INDEX."""

        self.entry.tk.call(self.entry._w, 'icursor', index)

    def index(self, index: int) -> int:
        """Return position of cursor."""

        return self.entry.tk.getint(
            self.entry.tk.call(self.entry._w, 'index', index)
        )

    def insert(self, index: int, string: str) -> None:
        """Insert STRING at INDEX."""

        self.entry.tk.call(self.entry._w, 'insert', index, string)

    def disable(self) -> None:
        self.config(cursor='arrow')
        self.entry.config(
            cursor='arrow',
            state=tk.DISABLED
        )
        self.pad_frame.unbind('<Button-1>')
        self.pad_frame.config(
            cursor='arrow',
            bg=self.entry.cget('disabledbackground')
        )

    def enable(self) -> None:
        self.config(cursor='xterm')
        self.entry.config(
            cursor='xterm',
            state=tk.NORMAL
        )
        self.pad_frame.bind('<Button-1>', self.__on_pad_frame_click)
        self.pad_frame.config(
            cursor='xterm',
            bg=self.entry.cget('bg')
        )

    def clear(self) -> None:
        self.delete(0, tk.END)
        self.put_placeholder()

    def put_placeholder(self) -> None:
        if self.placeholder is not None:
            self.is_placeholder = True
            self.insert(0, self.placeholder)
            self.entry['fg'] = self.placeholder_color

    def focus_in(self, event: tk.Event) -> None:
        if (self.placeholder is not None
                and self.entry['fg'] == self.placeholder_color):
            self.is_placeholder = False
            self.delete(0, tk.END)
            self.entry['fg'] = self.text_color

    def focus_out(self, event: tk.Event) -> None:
        if self.placeholder is not None and self.get() == '':
            self.put_placeholder()

    def set_text(self, text: str) -> None:
        if (self.placeholder is not None
                and self.entry['fg'] == self.placeholder_color):
            self.delete(0, tk.END)
            self.entry['fg'] = self.text_color
            self.insert(0, text)

    def set_validator(self, validate: str, command: tuple[str, str]) -> None:
        self.entry.config(validate=validate, validatecommand=command)

    def __on_pad_frame_click(self, event: tk.Event) -> None:
        self.entry.focus()
        self.icursor(0)


class FileNameEntry(Entry):
    def __init__(self,
                 parent: tk.Widget,
                 placeholder: str | None=None,
                 placeholder_color='grey',
                 text: str | None=None,
                 relief=tk.SOLID,
                 border_width: int=1,
                 border_color: str='#adadad',
                 font=fonts.BODY,
                 file_ext: str='txt',
                 **kwargs):
        Entry.__init__(self,
                       parent,
                       placeholder=placeholder,
                       placeholder_color=placeholder_color,
                       text=f'{text}.{file_ext}',
                       relief=relief,
                       border_width=border_width,
                       border_color=border_color,
                       font=font,
                       **kwargs)
        self.file_ext = file_ext

        self.bind('<FocusIn>', self.shift_cursor)

    def shift_cursor(self, *args) -> None:
        self.focus_set()

        try:
            index = self.get().rindex(f'.{self.file_ext}')
        except ValueError:
            return

        self.icursor(index)


class FileEntry(Entry):
    """Custom widget that opens either a file or directory dialog."""
    def __init__(self,
                 parent: tk.Widget,
                 initial_dir: str | None=None,
                 text: str | None=None,
                 file_type: Literal['file', 'directory']='directory',
                 types: list[tuple[str, str | list[str] | None]] | None=None,
                 label_text: str | None=None,
                 font=fonts.BODY,
                 textvariable: tk.Variable | None=None,
                 **kwargs):
        Entry.__init__(
            self,
            parent,
            text=text,
            font=font,
            **kwargs
        )

        self.types = types
        self.file_type = file_type
        self.initial_dir = initial_dir or _ROOT
        self.file_path = tk.StringVar(self, '')

        if label_text:
            self.label = Label(self,
                               text=label_text,
                               font=font,
                               bg=self['bg'])
            self.label.pack(side=tk.LEFT,
                            anchor=tk.NE,
                            padx=(0, 5))

        if textvariable:
            self.entry.config(textvariable=textvariable)

        dir_img = utils.get_tkimage('folder.png', (24, 24))
        self.button = Button(self,
                             pady=0,
                             padx=0,
                             image=dir_img,
                             highlightbackground='grey',
                             highlightcolor='grey',
                             highlightthickness=1,
                             command=self.open_dialog)
        self.button.pack(side=tk.RIGHT,
                         anchor=tk.NW,
                         padx=(0, 0),
                         pady=(0, 0))

    def configure(self, **kw) -> None:
        self.entry.config(**kw)

    def disable(self) -> None:
        self.button.disable()
        super().disable()

    def enable(self) -> None:
        self.button.enable()
        super().enable()

    def open_dialog(self, *args):
        initial_file = self.file_path.get()
        if initial_file == '':
            initial_file = None

        if self.file_type == 'file':
            file_path = filedialog.askopenfilename(initialdir=self.initial_dir,
                                                   initialfile=initial_file,
                                                   filetypes=self.types)
        else:
            file_path = filedialog.askdirectory(initialdir=self.initial_dir,
                                                mustexist=True)
        if file_path != '':
            self.file_path.set(file_path)
            self.delete(0, tk.END)
            self.insert(0, file_path)
