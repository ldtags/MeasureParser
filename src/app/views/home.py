import tkinter as tk
from tkinter import ttk

# from src import utils
from src.app import fonts
from src.app.tkobjects import (
    Frame,
    Page,
    FileEntry,
    Button,
    Toplevel,
    OptionLabel,
    Entry,
    MeasureFilePopup
)


HOME = 'home'


class HomePage(Page):
    def __init__(self, parent: Frame, **kwargs):
        super().__init__(parent, **kwargs)
        self.grid(row=0,
                  column=0,
                  sticky=tk.NSEW)

        self.popup: MeasureFilePopup | None = None

        self.intro_frame = IntroFrame(self,
                                      title='eTRM Measure Parser',
                                      body='Validate eTRM Measures',
                                      image_asset='config.png',
                                      bg='#ffffff')
        self.intro_frame.pack(side=tk.TOP,
                              anchor=tk.N,
                              fill=tk.X)

        self.tabbed_page = TabbedPage(self)
        self.tabbed_page.pack(side=tk.TOP,
                              anchor=tk.N,
                              fill=tk.BOTH,
                              expand=True)

        self.controls_frame = ControlsFrame(self,
                                            bg='#f0f0f0')
        self.controls_frame.pack(side=tk.BOTTOM,
                                 anchor=tk.S,
                                 fill=tk.X)

    def show(self):
        self.tkraise()

    def json_popup(self) -> str:
        if self.popup is None or not self.popup.winfo_exists():
            self.popup = MeasureFilePopup(self)
        self.popup.wm_transient()
        self.popup.focus_set()
        file_path = self.popup.wait()
        self.popup = None
        return file_path


class TabbedPage(ttk.Notebook):
    def __init__(self, parent: Frame, **kwargs):
        super().__init__(parent, **kwargs)

        self.measure_source_frame = MeasureSourceFrame(self,
                                                       bg='#ffffff')
        self.measure_source_frame.pack()
        self.add(self.measure_source_frame, text=' Select Measures ')

        self.selected_measures_frame = SelectedMeasuresFrame(self,
                                                             bg='#ffffff')
        self.selected_measures_frame.pack()
        self.add(self.selected_measures_frame, text=' View Selected Measures ')

        self.info_frame = InfoFrame(self, bg='#ffffff')
        self.info_frame.pack()
        self.add(self.info_frame, text=' Info ')


class IntroFrame(Frame):
    def __init__(self,
                 parent: HomePage,
                 title: str='',
                 body: str='',
                 image_asset: str | None=None,
                 **kwargs):
        super().__init__(parent, **kwargs)

        self.intro_title = tk.Label(self,
                                    text=title,
                                    font=fonts.SUB_HEADER,
                                    bg=self['bg'])
        self.intro_title.pack(side=tk.TOP,
                              anchor=tk.NW,
                              padx=(15, 15),
                              pady=(20, 0))

        self.intro_body = tk.Label(self,
                                   text=body,
                                   font=fonts.BODY,
                                   bg=self['bg'])
        self.intro_body.pack(side=tk.TOP,
                             anchor=tk.NW,
                             padx=(15, 15),
                             pady=(0, 20))

        # if image_asset:
        #     img = utils.get_tkimage(image_asset, size=(32, 32))
        #     self.intro_image = tk.Label(self, image=img)
        #     self.intro_image.pack()
        # change layout style to grid if implemented

        self.intro_sep = ttk.Separator(self)
        self.intro_sep.pack(side=tk.TOP,
                            fill=tk.X,
                            anchor=tk.S,
                            padx=(0, 0),
                            pady=(5, 0))


class MeasureSourceFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        super().__init__(parent, **kwargs)

        self.selection_frame = MeasureSelectionFrame(self,
                                                     bg=self['bg'])
        self.selection_frame.pack(side=tk.TOP,
                                  anchor=tk.NW,
                                  fill=tk.BOTH,
                                  padx=(20, 20),
                                  pady=(30, 30))

        self.options_frame = OptionsFrame(self,
                                          bg=self['bg'])
        self.options_frame.pack(side=tk.TOP,
                               anchor=tk.NW,
                               fill=tk.BOTH,
                               padx=(20, 20),
                               pady=(30, 30))


class MeasureSelectionFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        super().__init__(parent, **kwargs)

        self.grid_columnconfigure((0, 1), weight=1, uniform='source_buttons')

        self.label = OptionLabel(self,
                                 title='eTRM Measure Sources',
                                 sub_title='Select eTRM measures'
                                           ' to be parsed',
                                 separate=True)
        self.label.grid(row=0,
                        column=0,
                        columnspan=2,
                        sticky=tk.NSEW,
                        padx=(0, 0),
                        pady=(10, 10))

        self.etrm_btn = Button(self,
                               text='Select Measure(s) from eTRM')
        self.etrm_btn.grid(row=1,
                           column=0,
                           padx=(10, 10),
                           pady=(10, 10))

        self.json_btn = Button(self,
                               text='Import Measure from JSON File')
        self.json_btn.grid(row=1,
                           column=1,
                           padx=(10, 10),
                           pady=(10, 10))


class OptionsFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        super().__init__(parent, **kwargs)

        self.label = OptionLabel(self,
                                 title='Parser Options',
                                 sub_title='Specify how the parser'
                                           ' should be run',
                                 separate=True)
        self.label.pack(side=tk.TOP,
                        anchor=tk.N,
                        fill=tk.X,
                        padx=(0, 0),
                        pady=(0, 10))

        self.options_frame = Frame(self)
        self.options_frame.pack(side=tk.TOP,
                                anchor=tk.N,
                                fill=tk.BOTH,
                                padx=(10, 10),
                                pady=(0, 0))
        self.options_frame.grid_columnconfigure((0, 1),
                                                weight=1,
                                                uniform='options')

        self.output_folder = FolderOutputOption(self.options_frame)
        self.output_folder.grid(row=0,
                                column=0,
                                sticky=tk.NSEW,
                                padx=(0, 15),
                                pady=(0, 0))

        self.output_name = FileNameOption(self.options_frame)
        self.output_name.grid(row=0,
                              column=1,
                              sticky=tk.NSEW,
                              padx=(15, 0),
                              pady=(0, 0))


class FolderOutputOption(Frame):
    def __init__(self, parent: Frame, **kwargs):
        super().__init__(parent, **kwargs)

        self.output_label = OptionLabel(self,
                                        title='Parser Output Location',
                                        sub_title='Folder to store'
                                                  ' the parser results'
                                                  ' file',
                                        level=1)
        self.output_label.pack(side=tk.TOP,
                               anchor=tk.N,
                               fill=tk.X,
                               padx=(0, 0),
                               pady=(0, 5))

        self.output_entry = FileEntry(self, file_type='directory')
        self.output_entry.pack(side=tk.TOP,
                               anchor=tk.NW,
                               fill=tk.X,
                               expand=True,
                               padx=(0, 0),
                               pady=(0, 5))

        self.err_var = tk.StringVar(self, '')
        self.err_label = tk.Label(self,
                                  textvariable=self.err_var,
                                  font=fonts.BODY,
                                  bg=self['bg'],
                                  fg='red',
                                  wraplength=self.output_entry.winfo_width())
        self.err_label.pack(side=tk.TOP,
                            anchor=tk.N,
                            fill=tk.BOTH,
                            expand=True,
                            padx=(0, 0),
                            pady=(0, 10))

    def display_err(self, text: str):
        self.err_var.set(text)

    def clear_err(self):
        self.err_var.set('')


class FileNameOption(Frame):
    def __init__(self, parent: Frame, **kwargs):
        super().__init__(parent, **kwargs)

        self.output_label = OptionLabel(self,
                                        title='Parser Output File Name',
                                        sub_title='File name for the parser'
                                                  ' results file (.txt)',
                                        level=1)
        self.output_label.pack(side=tk.TOP,
                               anchor=tk.N,
                               fill=tk.X,
                               padx=(0, 0),
                               pady=(0, 5))

        self.entry = Entry(self, text='parser_results')
        self.entry.pack(side=tk.TOP,
                        anchor=tk.NW,
                        fill=tk.BOTH,
                        expand=True,
                        padx=(0, 0),
                        pady=(0, 5),
                        ipadx=1,
                        ipady=4)

        self.err_var = tk.StringVar(self, '')
        self.err_label = tk.Label(self,
                                  textvariable=self.err_var,
                                  font=fonts.BODY,
                                  bg=self['bg'],
                                  fg='red',
                                  wraplength=self.entry.winfo_width())
        self.err_label.pack(side=tk.TOP,
                            anchor=tk.N,
                            fill=tk.BOTH,
                            expand=True,
                            padx=(0, 0),
                            pady=(0, 10))

    def display_err(self, text: str):
        self.err_var.set(text)

    def clear_err(self):
        self.err_var.set('')


class SelectedMeasuresFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        super().__init__(parent, **kwargs)

        self.label = tk.Label(self,
                              text='Selected Measures',
                              font=fonts.BODY_BOLD,
                              bg=self['bg'])
        self.label.pack(side=tk.TOP,
                        anchor=tk.N,
                        padx=(10, 10),
                        pady=(5, 0))

        self.separator = ttk.Separator(self)
        self.separator.pack(side=tk.TOP,
                            fill=tk.X,
                            padx=(5, 5),
                            pady=(0, 5))


class InfoFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        super().__init__(parent, **kwargs)


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


class FileEntryPopup(Toplevel):
    def __init__(self, parent: tk.BaseWidget, **kwargs):
        super().__init__(parent, **kwargs)

        self.label = tk.Label(self,
                              text='Select eTRM Measure JSON File',
                              bg=self['bg'],
                              font=fonts.SUB_HEADER)
        self.label.pack(side=tk.TOP,
                        anchor=tk.NW,
                        fill=tk.X,
                        expand=False,
                        padx=(5, 5),
                        pady=(5, 0))

        self.separator = ttk.Separator(self)
        self.separator.pack(side=tk.TOP,
                            fill=tk.X,
                            padx=(5, 5),
                            pady=(0, 5))
