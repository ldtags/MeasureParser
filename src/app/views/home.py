import tkinter as tk
import tkinter.ttk as ttk

from src.app import fonts
from src.app.tkobjects import (
    Frame,
    Page,
    FileEntry,
    FileNameEntry,
    Button,
    Entry,
    OptionLabel
)


class HomePage(Page):
    key = 'home'

    def __init__(self, parent: Frame, **kwargs):
        Page.__init__(self, parent, **kwargs)

        self.grid(row=0,
                  column=0,
                  sticky=tk.NSEW)

        self.intro_label = OptionLabel(self,
                                       title='eTRM Measure Parser',
                                       sub_title='Simplifies the eTRM measure'
                                                 ' QA/QC process by providing'
                                                 ' accurate measure data'
                                                 ' validation.',
                                       img_name='etrm.png',
                                       ipadx=(15, 15),
                                       ipady=(20, 20))
        self.intro_label.pack(side=tk.TOP,
                              anchor=tk.NW,
                              fill=tk.X)
        
        self.source_frame = MeasureSourceFrame(self)
        self.source_frame.pack(side=tk.TOP,
                               anchor=tk.NW,
                               fill=tk.BOTH,
                               expand=True,
                               padx=(10, 10),
                               pady=(10, 10))

        self.output_frame = OutputFrame(self)
        self.output_frame.pack(side=tk.TOP,
                               anchor=tk.NW,
                               fill=tk.BOTH,
                               expand=True,
                               padx=(10, 10),
                               pady=(10, 10))

        self.controls_frame = ControlsFrame(self,
                                            bg='#f0f0f0')
        self.controls_frame.pack(side=tk.BOTTOM,
                                 anchor=tk.S,
                                 fill=tk.X)

    def show(self):
        self.tkraise()


class MeasureSourceFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        Frame.__init__(self, parent, **kwargs)

        self.source_label = OptionLabel(self,
                                        title='eTRM Measure Sources',
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
        self.grid_rowconfigure((0, 3), weight=1)
        self.grid_rowconfigure((1, 2), weight=0)

        self.file_label = OptionLabel(self,
                                      title='Measure JSON File',
                                      sub_title='Select an existing eTRM'
                                                ' measure JSON file.',
                                      level=1)
        self.file_label.grid(column=0,
                             row=1,
                             sticky=tk.NSEW)

        self.file_entry = FileEntry(self,
                                    file_type='file',
                                    types=[('JSON File', '.json')])
        self.file_entry.grid(column=0,
                             row=2,
                             sticky=tk.NSEW,
                             pady=(5, 0))


class SourceSeparator(Frame):
    def __init__(self, parent: Frame, **kwargs):
        Frame.__init__(self, parent, **kwargs)

        self.grid_columnconfigure((0, 2), weight=1)
        self.grid_columnconfigure((1), weight=0)
        self.grid_rowconfigure((0, 2),
                               weight=1,
                               uniform='SourceSeparatorV')
        self.grid_rowconfigure((1), weight=0)

        self.top_separator = ttk.Separator(self,
                                           orient='vertical')
        self.top_separator.grid(column=1,
                                row=0,
                                sticky=tk.NS)

        self.label = tk.Label(self,
                              text='OR',
                              font=fonts.BODY,
                              bg=self['bg'])
        self.label.grid(column=1,
                        row=1,
                        sticky=tk.NSEW)

        self.bottom_separator = ttk.Separator(self,
                                              orient='vertical')
        self.bottom_separator.grid(column=1,
                                   row=2,
                                   sticky=tk.NS)


class ETRMSourceFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        Frame.__init__(self, parent, **kwargs)

        self.key_label = OptionLabel(self,
                                     title='API Key',
                                     sub_title='An eTRM API key, used'
                                               ' for authorizing requests to'
                                               ' the eTRM API.',
                                     level=1)
        self.key_label.pack(side=tk.TOP,
                            anchor=tk.NW,
                            fill=tk.X,)

        self.api_key_entry = Entry(self,
                                   placeholder='Token ae38f19b8c03de122...')
        self.api_key_entry.pack(side=tk.TOP,
                                anchor=tk.NW,
                                fill=tk.X,
                                expand=True,
                                ipady=3,
                                pady=(5, 0))

        self.measure_label = OptionLabel(self,
                                         title='Measure Version ID',
                                         sub_title='A full eTRM measure'
                                                   ' version ID.',
                                         level=1)
        self.measure_label.pack(side=tk.TOP,
                                anchor=tk.NW,
                                fill=tk.X,
                                pady=(10, 0))

        self.measure_entry = Entry(self,
                                   placeholder='SWAP001-06')
        self.measure_entry.pack(side=tk.TOP,
                                anchor=tk.NW,
                                fill=tk.X,
                                expand=True,
                                ipady=3,
                                pady=(5, 0))


class OutputFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        Frame.__init__(self, parent, **kwargs)

        self.output_label = OptionLabel(self,
                                        title='Parser Output Options',
                                        level=0)
        self.output_label.pack(side=tk.TOP,
                               anchor=tk.NW,
                               fill=tk.X)

        self.options_frame = self._OutputOptionsFrame(self)
        self.options_frame.pack(side=tk.TOP,
                                anchor=tk.NW,
                                fill=tk.BOTH,
                                expand=True,
                                padx=(10, 10),
                                pady=(10, 0))


    class _OutputOptionsFrame(Frame):
        def __init__(self, parent: Frame, **kwargs):
            Frame.__init__(self, parent, **kwargs)

            self.grid_columnconfigure((0), weight=1)
            self.grid_rowconfigure((0, 1, 2, 3), weight=0)

            self.fname_label = OptionLabel(self,
                                           title='Output File Name',
                                           sub_title='The file name of the'
                                                     ' parser output file.',
                                           level=1)
            self.fname_label.grid(row=0,
                                  column=0,
                                  sticky=tk.NSEW)

            self.fname_entry = FileNameEntry(self,
                                             text='parser_output')
            self.fname_entry.grid(row=1,
                                  column=0,
                                  sticky=tk.NSEW,
                                  ipady=3,
                                  pady=(5, 10))

            self.outdir_label = OptionLabel(self,
                                            title='Output File Location',
                                            sub_title='The folder that the'
                                                      ' parser output file'
                                                      ' will be placed in.',
                                            level=1)
            self.outdir_label.grid(row=2,
                                   column=0,
                                   sticky=tk.NSEW)

            self.outdir_entry = FileEntry(self)
            self.outdir_entry.grid(row=3,
                                   column=0,
                                   sticky=tk.NSEW,
                                   pady=(5, 10))


class ControlsFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        super().__init__(parent, **kwargs)

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
