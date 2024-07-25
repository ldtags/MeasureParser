import os
import tkinter as tk

from src import assets, _ROOT
from src.app import fonts
from src.app.widgets.frames import Frame
from src.app.widgets.buttons import Button
from src.app.widgets.entries import FileEntry
from src.app.widgets.general import OptionLabel
from src.app.exceptions import ValidationError


def validate_path(path: str | None,
                  file_ext: list[str] | str | None=None
                 ) -> bool:
    if path is None:
        raise ValidationError('File path is required')

    if not os.path.exists(path):
        raise ValidationError(f'{path} does not exist')

    split_path = os.path.splitext(path)
    if len(split_path) != 2:
        raise ValidationError(f'{path} is missing a file extension')

    path_ext = split_path[1]
    if isinstance(file_ext, list) and path_ext not in file_ext:
        raise ValidationError(f'{path} must have one of the following'
                              f' file extensions: {file_ext}')

    if isinstance(file_ext, str) and path_ext != file_ext:
        raise ValidationError(f'{path} must have the file extension:'
                              f' {file_ext}')

    return True


class MeasureFilePopup(tk.Toplevel):
    def __init__(self, parent: tk.Frame, **kwargs):
        self.parent = parent
        try:
            kwargs['bg']
        except KeyError:
            kwargs['bg'] = parent['bg']
        super().__init__(parent, **kwargs)

        self.geometry('450x250')
        self.resizable(width=False, height=False)
        self.iconbitmap(assets.get_path('app.ico'))
        self.grab_set()

        self.grid_columnconfigure((0), weight=1)
        self.grid_rowconfigure((2), weight=1)

        self.label = OptionLabel(self,
                                 title='eTRM Measure JSON File',
                                 sub_title='File path to an eTRM Measure JSON'
                                           ' file',
                                 level=1,
                                 bg=self['bg'])
        self.label.grid(row=0,
                        column=0,
                        sticky=tk.NSEW,
                        padx=(10, 10),
                        pady=(10, 10))

        self.path_var = tk.StringVar(self, '')
        self.entry = FileEntry(self,
                               initial_dir=_ROOT,
                               file_type='file',
                               types=[('JSON files', '.json')],
                               textvariable=self.path_var)
        self.entry.grid(row=1,
                        column=0,
                        sticky=tk.NSEW,
                        padx=(10, 10),
                        pady=(10, 10))

        self.err_var = tk.StringVar(self, '')
        self.err_label = tk.Label(self,
                                  textvariable=self.err_var,
                                  bg=self['bg'],
                                  fg='red',
                                  font=fonts.BODY,
                                  wraplength=self.parent.winfo_width())
        self.err_label.grid(row=2,
                            column=0,
                            sticky=tk.N)

        self.btn_frame = Frame(self, bg=self['bg'])
        self.btn_frame.grid(row=3,
                            column=0,
                            sticky=tk.SE)

        self.add_btn = Button(self.btn_frame,
                              text='Add Measure',
                              command=self._add_cb)
        self.add_btn.pack(side=tk.RIGHT,
                          anchor=tk.E,
                          padx=(10, 10),
                          pady=(10, 10))

        self.cancel_btn = Button(self.btn_frame,
                                 text='Cancel',
                                 command=self._cancel_cb)
        self.cancel_btn.pack(side=tk.RIGHT,
                             anchor=tk.E,
                             padx=(10, 10),
                             pady=(10, 10))

    def display_err(self, text: str):
        self.err_var.set(text)

    def clear_err(self):
        self.err_var.set('')

    def _close(self):
        if self.winfo_exists():
            self.grab_release()
            self.destroy()

    def wait(self) -> str:
        if self.winfo_exists():
            self.wait_window()
        return self.path_var.get()

    def _cancel_cb(self, *args):
        self._close()

    def _add_cb(self, *args):
        input_path = self.entry.get_file_path()
        try:
            validate_path(input_path, 'json')
            self._close()
        except ValidationError as err:
            self.display_err(err.message)
