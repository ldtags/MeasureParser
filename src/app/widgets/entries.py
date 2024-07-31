import tkinter as tk
import tkinter.filedialog as filedialog
from typing import Literal

from .misc import Widget
from .labels import Label
from .buttons import Button

from src import utils, _ROOT
from src.app import fonts


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
    def __init__(self,
                 parent: tk.Misc,
                 placeholder: str | None=None,
                 placeholder_color: str='grey',
                 text: str | None=None,
                 text_color: str='black',
                 relief: str=tk.SOLID,
                 border_width: float=1,
                 border_color: str='#adadad',
                 font: tuple[str, int, str | None]=fonts.BODY,
                 **kwargs):
        kw = {
            'highlightcolor': border_color,
            'highlightbackground': border_color,
            'highlightthickness': border_width,
            'height': font[1]
        }
        Widget.__init__(self, parent, 'frame', cnf={}, kw=kw)

        self.placeholder = placeholder
        self.placeholder_color = placeholder_color
        self.text_color = text_color
        self.text = text
        self.entry = _Entry(
            self,
            text_color,
            relief,
            font,
            **kwargs
        )
        self.entry.pack(side=tk.TOP,
                        anchor=tk.NW,
                        fill=tk.BOTH,
                        expand=tk.TRUE)

        if text:
            self.insert(0, text)
        elif placeholder:
            self.put_placeholder()

        self.bind('<FocusIn>', self.focus_in)
        self.bind('<FocusOut>', self.focus_out)

    def configure(self, **kw) -> None:
        self.entry.configure(**kw)

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
            self.entry.tk.call(
                self.entry._w, 'index', index
            )
        )

    def insert(self, index: int, string: str) -> None:
        """Insert STRING at INDEX."""

        self.entry.tk.call(self.entry._w, 'insert', index, string)

    def put_placeholder(self) -> None:
        if self.placeholder:
            self.insert(0, self.placeholder)
            self.entry['fg'] = self.placeholder_color

    def focus_in(self, event: tk.Event) -> None:
        if self.placeholder and self.entry['fg'] == self.placeholder_color:
            self.delete(0, tk.END)
            self.entry['fg'] = self.text_color

    def focus_out(self, event: tk.Event) -> None:
        if self.placeholder and not self.get():
            self.put_placeholder()

    def set_text(self, text: str) -> None:
        if self.placeholder and self.entry['fg'] == self.placeholder_color:
            self.delete(0, tk.END)
            self.entry['fg'] = self.text_color
            self.insert(0, text)


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


class FileEntry(Widget):
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
        Widget.__init__(self, parent, 'frame', kw=kwargs)

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
                            padx=(0, 5),
                            pady=(0, 0))

        self.entry = Entry(self,
                           text=text,
                           font=font)
        self.entry.pack(side=tk.LEFT,
                        anchor=tk.N,
                        fill=tk.BOTH,
                        expand=True,
                        padx=(0, 0),
                        pady=(0, 0))

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
        self.button.pack(side=tk.LEFT,
                         anchor=tk.NW,
                         padx=(0, 0),
                         pady=(0, 0))

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
            self.entry.delete(0, tk.END)
            self.entry.insert(0, file_path)

    def get(self) -> str:
        return self.entry.get()
