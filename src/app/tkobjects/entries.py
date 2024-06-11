import tkinter as tk
import tkinter.filedialog as filedialog
from typing import Literal

from src import utils, _ROOT
from src.app import fonts
from src.app.tkobjects.frames import Frame
from src.app.tkobjects.buttons import Button


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
                 **kwargs):
        kwargs['borderwidth'] = 0
        kwargs['relief'] = relief
        kwargs['highlightthickness'] = border_width
        kwargs['highlightbackground'] = border_color
        kwargs['highlightcolor'] = border_color
        kwargs['font'] = font
        super().__init__(parent, **kwargs)

        self.placeholder = placeholder
        self.placeholder_color = placeholder_color
        self.default_fg = self['fg']

        if text:
            self.insert(0, text)

        self.bind('<FocusIn>', self.focus_in)
        self.bind('<FocusOut>', self.focus_out)

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
                 **kwargs):
        super().__init__(parent, **kwargs)

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

        self.entry = Entry(self,
                           text=text,
                           font=font)
        self.entry.pack(side=tk.LEFT,
                        anchor=tk.N,
                        fill=tk.BOTH,
                        expand=True,
                        padx=(0, 0),
                        pady=(0, 0),
                        ipadx=1,
                        ipady=2)

        if textvariable:
            self.entry.config(textvariable=textvariable)

        global dir_img
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
                         pady=(0, 0),
                         ipadx=2,
                         ipady=2)

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

    def get_file_path(self) -> str | None:
        path = self.entry.get()
        if path == '':
            return None
        return path
