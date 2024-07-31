import tkinter as tk
import tkinter.filedialog as filedialog
from typing import Literal

from src import utils, _ROOT
from src.app import fonts
from src.app.types import TK_EVENT_BINDING
from src.app.widgets.frames import Frame
from src.app.widgets.buttons import Button


class Entry(tk.Entry):
    def __init__(self,
                 parent: tk.Widget,
                 placeholder: str | None=None,
                 placeholder_color='grey',
                 text: str | None=None,
                 relief=tk.SOLID,
                 border_width: int=1,
                 border_color: str='grey',
                 font=fonts.BODY,
                 events: list[TK_EVENT_BINDING] | None=None,
                 **kwargs):
        kwargs['borderwidth'] = 0
        kwargs['relief'] = relief
        kwargs['highlightthickness'] = border_width
        kwargs['highlightbackground'] = border_color
        kwargs['highlightcolor'] = border_color
        kwargs['font'] = font
        tk.Entry.__init__(self, parent, **kwargs)

        self.parent = parent
        self.placeholder = placeholder
        self.placeholder_color = placeholder_color
        self.default_fg = self['fg']

        if text:
            self.insert(0, text)
        elif placeholder:
            self.put_placeholder()

        self.bind('<FocusIn>', self.focus_in)
        self.bind('<FocusOut>', self.focus_out)
        for event, callback in events or []:
            self.bind(event, callback)

    def put_placeholder(self):
        if self.placeholder:
            self.insert(0, self.placeholder)
            self['fg'] = self.placeholder_color

    def focus_in(self, *args):
        if self.placeholder and self['fg'] == self.placeholder_color:
            self.delete(0, tk.END)
            self['fg'] = self.default_fg

    def focus_out(self, *args):
        if self.placeholder and not self.get():
            self.put_placeholder()

    def set_text(self, text: str) -> None:
        if self.placeholder and self['fg'] == self.placeholder_color:
            self.delete(0, tk.END)
            self['fg'] = self.default_fg
            self.insert(0, text)


class FileNameEntry(Entry):
    def __init__(self,
                 parent: tk.Widget,
                 placeholder: str | None=None,
                 placeholder_color='grey',
                 text: str | None=None,
                 relief=tk.SOLID,
                 border_width: int=1,
                 border_color: str='grey',
                 font=fonts.BODY,
                 file_ext: str='txt',
                 events: list[TK_EVENT_BINDING] | None=None,
                 **kwargs):
        Entry.__init__(self,
                       parent,
                       placeholder,
                       placeholder_color,
                       f'{text}.{file_ext}',
                       relief,
                       border_width,
                       border_color,
                       font,
                       events=events,
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


class FileEntry(Frame):
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
                 events: list[TK_EVENT_BINDING] | None=None,
                 **kwargs):
        Frame.__init__(self, parent, events, **kwargs)

        self.types = types
        self.file_type = file_type
        self.initial_dir = initial_dir or _ROOT
        self.file_path = tk.StringVar(self, '')

        if label_text:
            self.label = tk.Label(self,
                                  text=label_text,
                                  font=font,
                                  bg=self['bg'])
            self.label.pack(side=tk.LEFT,
                            anchor=tk.NE,
                            padx=(0, 5),
                            pady=(0, 0))
            for event, callback in events or []:
                self.label.bind(event, callback)

        self.entry = Entry(self,
                           text=text,
                           font=font,
                           events=events)
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
                             command=self.open_dialog,
                             events=events)
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
