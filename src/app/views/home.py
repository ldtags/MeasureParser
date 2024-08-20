import tkinter as tk
import tkinter.ttk as ttk
from typing import Literal

from src.app import fonts
from src.app.widgets import (
    Frame,
    Page,
    FileEntry,
    FileNameEntry,
    Button,
    Entry,
    OptionLabel,
    Label,
    OptionCheckBox,
    ScrollableFrame
)
from src.config import app_config


class HomePage(Page):
    key = 'home'

    def __init__(self, parent: Frame, root: tk.Tk, **kwargs):
        Page.__init__(self, parent, root, **kwargs)

        self.config(bg='#f0f0f0')
        self.grid(
            row=0,
            column=0,
            sticky=tk.NSEW
        )

        self.intro_label = OptionLabel(
            self,
            title='eTRM Measure Parser',
            sub_title='Simplifies the eTRM measure QA/QC process by providing'
                ' accurate measure data validation.',
            img_name='etrm.png',
            ipadx=(15, 15),
            ipady=(20, 20),
            bg='#ffffff'
        )
        self.intro_label.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.X
        )
        
        self.home_container = HomeContainer(self)
        self.home_container.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.BOTH,
            expand=tk.TRUE
        )

        self.controls_frame = ControlsFrame(self)
        self.controls_frame.pack(
            side=tk.BOTTOM,
            anchor=tk.S,
            fill=tk.X
        )

        # top-level references to child widgets
        self.source_frame = self.home_container.source_frame
        self.output_frame = self.home_container.output_frame
        self.options_frame = self.home_container.options_frame

    def show(self) -> None:
        sources = self.source_frame
        checkboxes = self.options_frame
        if not sources.etrm_frame.is_empty():
            sources.json_frame.disable()
            sources.etrm_frame.enable()
            checkboxes.validate_permutations.disable()
            checkboxes.qa_qc_permutations.enable()

        if not sources.json_frame.is_empty():
            sources.etrm_frame.disable()
            sources.json_frame.enable()
            checkboxes.validate_permutations.enable()
            checkboxes.qa_qc_permutations.disable()

        super().show()


class HomeContainer(ScrollableFrame):
    def __init__(self, parent: tk.Frame, **kwargs):
        ScrollableFrame.__init__(self, parent, scrollbar=True, **kwargs)

        self.source_frame = MeasureSourceFrame(self.interior)
        self.source_frame.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.BOTH,
            expand=tk.TRUE,
            padx=(10, 10),
            pady=(10, 0)
        )

        self.output_frame = OutputFrame(self.interior)
        self.output_frame.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.BOTH,
            expand=tk.TRUE,
            padx=(10, 10),
            pady=(0, 10)
        )

        self.options_frame = OptionsFrame(self.interior)
        self.options_frame.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.BOTH,
            expand=tk.TRUE,
            padx=(10, 10),
            pady=(10, 25)
        )


class MeasureSourceFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        Frame.__init__(self, parent, **kwargs)

        self.source_label = OptionLabel(self,
                                        title='Measure Sources',
                                        level=0)
        self.source_label.pack(side=tk.TOP,
                               anchor=tk.NW,
                               fill=tk.X)

        self.source_frame = self._SourceFrame(self)
        self.source_frame.pack(side=tk.TOP,
                               anchor=tk.NW,
                               fill=tk.BOTH,
                               expand=True,
                               padx=(10, 10),
                               pady=(10, 0))

        self.source_err_var = tk.StringVar(self, ' ')
        self.source_err_label = Label(self,
                                      textvariable=self.source_err_var,
                                      fg='#ff0000')
        self.source_err_label.pack(side=tk.TOP,
                                   anchor=tk.NW,
                                   fill=tk.X,
                                   padx=(10, 10))

        # top-level child references
        self.json_frame = self.source_frame.json_frame
        self.etrm_frame = self.source_frame.etrm_frame

    def print_err(self, err: str) -> None:
        self.source_err_var.set(err)

    def clear_err(self) -> None:
        self.source_err_var.set('')

    class _SourceFrame(Frame):
        def __init__(self, parent: Frame, **kwargs):
            Frame.__init__(self, parent, **kwargs)

            self.grid_rowconfigure((0), weight=1)
            self.grid_columnconfigure((0, 2),
                                      weight=1,
                                      uniform='_SourceFrame')
            self.grid_columnconfigure((1), weight=0)

            self.json_frame = JSONSourceFrame(self)
            self.json_frame.grid(column=0,
                                 row=0,
                                 sticky=tk.NSEW,
                                 padx=(10, 10))

            self.source_separator = SourceSeparator(self)
            self.source_separator.grid(column=1,
                                       row=0,
                                       sticky=tk.NSEW)

            self.etrm_frame = ETRMSourceFrame(self)
            self.etrm_frame.grid(column=2,
                                row=0,
                                sticky=tk.NSEW,
                                padx=(10, 10))


class JSONSourceFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        Frame.__init__(self, parent, **kwargs)

        self.grid_columnconfigure((0), weight=1)
        self.grid_rowconfigure((0, 7), weight=1)
        self.grid_rowconfigure((1, 2, 3, 4, 5, 6), weight=0)

        self.file_label = OptionLabel(
            self,
            title='Measure JSON File',
            sub_title='Select an existing eTRM measure JSON file.',
            level=1
        )
        self.file_label.grid(
            column=0,
            row=1,
            sticky=tk.NSEW
        )

        self.file_entry = FileEntry(
            self,
            file_type='file',
            types=[('JSON File', '.json')]
        )
        self.file_entry.grid(
            column=0,
            row=2,
            sticky=tk.NSEW,
            pady=(5, 0)
        )

        self.file_err_var = tk.StringVar(self, '')
        self.file_err_label = Label(
            self,
            variable=self.file_err_var,
            text_color='#ff0000'
        )
        self.file_err_label.grid(
            column=0,
            row=3,
            sticky=tk.NSEW,
            pady=(2.5, 0)
        )

        self.csv_label = OptionLabel(
            self,
            title='Permutations CSV File (*Optional)',
            sub_title='Select an existing eTRM measure permutations'
                ' CSV file.',
            level=1
        )
        self.csv_label.grid(
            column=0,
            row=4,
            sticky=tk.NSEW
        )

        self.csv_entry = FileEntry(
            self,
            file_type='file',
            types=[('CSV File', '.csv')]
        )
        self.csv_entry.grid(
            column=0,
            row=5,
            sticky=tk.NSEW,
            pady=(5, 0)
        )

        self.csv_err_var = tk.StringVar(self, '')
        self.csv_err_label = Label(
            self,
            variable=self.csv_err_var,
            text_color='#ff0000'
        )
        self.csv_err_label.grid(
            column=0,
            row=6,
            sticky=tk.NSEW,
            pady=(2.5, 0)
        )

    def print_err(self,
                  err: str,
                  entry: Literal['json', 'csv']
                 ) -> None:
        match entry:
            case 'json':
                self.file_err_var.set(err)
            case 'csv':
                self.csv_err_var.set(err)
            case other:
                raise RuntimeError(f'Unknown entry: {other}')

    def clear_err(self,
                  entry: Literal['json', 'csv'] | None=None
                 ) -> None:
        if entry is None:
            self.file_err_var.set('')
            self.csv_err_var.set('')
            return
        
        match entry:
            case 'json':
                self.file_err_var.set('')
            case 'csv':
                self.csv_err_var.set('')
            case other:
                raise RuntimeError(f'Unknown entry: {other}')

    def disable(self) -> None:
        self.file_entry.disable()
        self.csv_entry.disable()

    def enable(self) -> None:
        self.file_entry.enable()
        self.csv_entry.enable()

    def clear(self) -> None:
        self.file_entry.clear()
        self.csv_entry.clear()

    def is_empty(self) -> bool:
        if self.file_entry.get() != '':
            return False

        if self.csv_entry.get() != '':
            return False

        return True


class SourceSeparator(Frame):
    def __init__(self, parent: Frame, **kwargs):
        Frame.__init__(self, parent, **kwargs)

        self.grid_columnconfigure((0, 2), weight=1)
        self.grid_columnconfigure((1), weight=0)
        self.grid_rowconfigure(
            (0, 2),
            weight=1,
            uniform='VerticalSourceSeparator'
        )
        self.grid_rowconfigure((1), weight=0)

        self.top_separator = ttk.Separator(
            self,
            orient='vertical'
        )
        self.top_separator.grid(
            column=1,
            row=0,
            sticky=tk.NS
        )

        self.label = tk.Label(
            self,
            text='OR',
            font=fonts.BODY,
            bg=self['bg']
        )
        self.label.grid(
            column=1,
            row=1,
            sticky=tk.NSEW
        )

        self.bottom_separator = ttk.Separator(
            self,
            orient='vertical'
        )
        self.bottom_separator.grid(
            column=1,
            row=2,
            sticky=tk.NS
        )


class ETRMSourceFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        Frame.__init__(self, parent, **kwargs)

        self.key_label = OptionLabel(
            self,
            title='API Key',
            sub_title='An eTRM API key, used for authorizing requests to'
                ' the eTRM API.',
            level=1
        )
        self.key_label.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.X
        )

        self.api_key_entry = Entry(
            self,
            placeholder='Token ae38f19b8c03de122...'
        )
        self.api_key_entry.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.X,
            expand=True,
            ipady=3,
            pady=(5, 0)
        )

        self.api_key_err_var = tk.StringVar(self, '')
        self.api_key_err_label = Label(
            self,
            variable=self.api_key_err_var,
            text_color='#ff0000'
        )
        self.api_key_err_label.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.X,
            pady=(2.5, 0)
        )

        self.measure_label = OptionLabel(
            self,
            title='Measure Version ID',
            sub_title='A full eTRM measure version ID.',
            level=1
        )
        self.measure_label.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.X,
            pady=(5, 0)
        )

        self.measure_entry = Entry(
            self,
            placeholder='SWAP001-06'
        )
        self.measure_entry.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.X,
            expand=True,
            ipady=3,
            pady=(5, 0)
        )

        self.measure_err_var = tk.StringVar(self, '')
        self.measure_err_label = Label(
            self,
            variable=self.measure_err_var,
            text_color='#ff0000'
        )
        self.measure_err_label.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.X,
            pady=(2.5, 0)
        )

    def print_err(self,
                err: str,
                entry: Literal['api_key', 'measure']
               ) -> None:
        match entry:
            case 'api_key':
                self.api_key_err_var.set(err)
            case 'measure':
                self.measure_err_var.set(err)
            case _:
                pass

    def clear_err(self,
                  entry: Literal['api_key', 'measure'] | None=None
                 ) -> None:
        if entry is None:
            self.api_key_err_var.set('')
            self.measure_err_var.set('')
            return

        match entry:
            case 'api_key':
                self.api_key_err_var.set('')
            case 'measure':
                self.measure_err_var.set('')
            case _:
                pass

    def disable(self) -> None:
        self.api_key_entry.disable()
        self.measure_entry.disable()

    def enable(self) -> None:
        self.api_key_entry.enable()
        self.measure_entry.enable()

    def is_empty(self) -> bool:
        if self.api_key_entry.get() != '':
            return False

        if self.measure_entry.get() != '':
            return False

        return True


class OutputFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        Frame.__init__(self, parent, **kwargs)

        self.output_label = OptionLabel(self, title='Parser Output')
        self.output_label.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.X
        )

        self.options_frame = self._OutputOptionsFrame(self)
        self.options_frame.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.BOTH,
            expand=True,
            padx=(10, 10),
            pady=(10, 0)
        )

    class _OutputOptionsFrame(Frame):
        def __init__(self, parent: Frame, **kwargs):
            Frame.__init__(self, parent, **kwargs)

            self.grid_columnconfigure((0), weight=1)
            self.grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=0)

            self.fname_label = OptionLabel(
                self,
                title='Output File Name',
                sub_title='The file name of the parser output file.',
                level=1
            )
            self.fname_label.grid(
                row=0,
                column=0,
                sticky=tk.NSEW
            )

            self.fname_entry = FileNameEntry(
                self,
                text='parser_output'
            )
            self.fname_entry.grid(
                row=1,
                column=0,
                sticky=tk.NSEW,
                ipady=3,
                pady=(5, 0)
            )

            self.file_err_var = tk.StringVar(self, ' ')
            self.file_err_label = Label(
                self,
                textvariable=self.file_err_var,
                fg='#ff0000'
            )
            self.file_err_label.grid(
                row=2,
                column=0,
                sticky=tk.NSEW,
                pady=(0, 10)
            )

            self.outdir_label = OptionLabel(
                self,
                title='Output File Location',
                sub_title='The folder that the parser output file will be'
                    ' placed in.',
                level=1
            )
            self.outdir_label.grid(
                row=3,
                column=0,
                sticky=tk.NSEW
            )

            self.outdir_entry = FileEntry(
                self,
                text=app_config.output_path
            )
            self.outdir_entry.grid(
                row=4,
                column=0,
                sticky=tk.NSEW,
                pady=(5, 0)
            )

            self.outdir_err_var = tk.StringVar(self, ' ')
            self.outdir_err_label = Label(
                self,
                textvariable=self.outdir_err_var,
                fg='#ff0000'
            )
            self.outdir_err_label.grid(
                row=5,
                column=0,
                sticky=tk.NSEW
            )

        def print_err(self,
                      err: str,
                      entry: Literal['directory', 'file']
                     ) -> None:
            match entry:
                case 'directory':
                    self.outdir_err_var.set(err)
                case 'file':
                    self.file_err_var.set(err)
                case _:
                    pass

        def clear_err(self,
                      entry: Literal['directory', 'file'] | None=None
                     ) -> None:
            if entry is None:
                self.file_err_var.set(' ')
                self.outdir_err_var.set(' ')

            match entry:
                case 'directory':
                    self.outdir_err_var.set('')
                case 'file':
                    self.file_err_var.set('')
                case _:
                    pass


class OptionsFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        Frame.__init__(self, parent, **kwargs)

        self.label = OptionLabel(self, title='Parser Options')
        self.label.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.X,
            pady=(0, 10)
        )

        self.container = Frame(self)
        self.container.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.BOTH,
            expand=tk.TRUE,
            padx=(10, 10)
        )

        self.container.grid_columnconfigure(
            (0, 1, 2),
            weight=1,
            uniform='OptionsFrameCols'
        )
        self.container.grid_rowconfigure((0), weight=1)

        self.override_file = OptionCheckBox(
            self.container,
            text='Override File',
            sub_text='Override the existing file if a file conflict occurs'
        )
        self.override_file.grid(
            row=0,
            column=0,
            sticky=tk.NSEW
        )

        self.validate_permutations = OptionCheckBox(
            self.container,
            text='Validate Permutations',
            sub_text='Validate the mapped permutation fields (JSON file'
                ' only)'
        )
        self.validate_permutations.grid(
            row=0,
            column=1,
            sticky=tk.NSEW,
            padx=(0, 5)
        )

        self.qa_qc_permutations = OptionCheckBox(
            self.container,
            text='QA/QC Permutations',
            sub_text='QA/QC the measure\'s permutations (eTRM API only)'
        )
        self.qa_qc_permutations.grid(
            row=0,
            column=2,
            sticky=tk.NSEW,
            padx=(5, 5)
        )


class ControlsFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        Frame.__init__(self, parent, **kwargs)

        self.separator = ttk.Separator(self)
        self.separator.pack(side=tk.TOP,
                            anchor=tk.S,
                            fill=tk.X)

        self.start_btn = Button(self,
                                pady=0,
                                padx=30,
                                text='Start')
        self.start_btn.pack(side=tk.RIGHT,
                            anchor=tk.E,
                            padx=(15, 30),
                            pady=(20, 20))

        self.close_btn = Button(self,
                                pady=0,
                                padx=30,
                                text='Close')
        self.close_btn.pack(side=tk.RIGHT,
                            anchor=tk.E,
                            padx=(30, 15),
                            pady=(20, 20))
