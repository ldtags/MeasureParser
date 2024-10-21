import tkinter as tk
import tkinter.ttk as ttk

from src.app.widgets import Frame, Page, ScrollableFrame, Button
from src.app.components import OptionLabel


class ResultsPage(Page):
    key = "results"

    def __init__(self, parent: tk.Misc, root: tk.Tk, **kwargs):
        Page.__init__(self, parent, root, **kwargs)

        self.config(bg="#f0f0f0")
        self.grid(row=0, column=0, sticky=tk.NSEW)

        self.intro_label = OptionLabel(
            self,
            title="Parsing",
            sub_title="Please wait while the measure is being parsed."
            "\nThis may take a few minutes.",
            bg="#ffffff",
            ipadx=(15, 15),
            ipady=(20, 20),
        )
        self.intro_label.pack(side=tk.TOP, anchor=tk.NW, fill=tk.X)
        self.intro_label.set_image("etrm.png")

        self.scroll_frame = ScrollableFrame(self, scrollbar=True)
        self.scroll_frame.pack(side=tk.TOP, anchor=tk.NW, fill=tk.BOTH, expand=tk.TRUE)

        self.results_frame = ParserResultsFrame(self.scroll_frame.interior)
        self.results_frame.pack(side=tk.TOP, anchor=tk.NW, fill=tk.BOTH, expand=tk.TRUE)

        self.controls_frame = ControlsFrame(self)
        self.controls_frame.pack(side=tk.BOTTOM, anchor=tk.S, fill=tk.X)


class ParserResultsFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        Frame.__init__(self, parent, **kwargs)


class ControlsFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        Frame.__init__(self, parent, **kwargs)

        self.separator = ttk.Separator(self)
        self.separator.pack(side=tk.TOP, anchor=tk.S, fill=tk.X)

        self.close_btn = Button(self, pady=0, padx=30, text="Close")
        self.close_btn.pack(side=tk.RIGHT, anchor=tk.E, padx=(15, 35), pady=(20, 20))
