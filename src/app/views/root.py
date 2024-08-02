import tkinter as tk
import ttkbootstrap as ttk

from src import utils


class Root(ttk.Window):
    def __init__(self, width: int=800, height: int=750):
        ttk.Window.__init__(
            self,
            title='Utility Tool',
            size=(width, height),
            minsize=(width, height),
            themename='simplex'
        )

        self.iconbitmap(utils.get_asset_path('app.ico'))
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.container = ttk.Frame(self)
        self.container.grid(row=0, column=0, sticky=tk.NSEW)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.place_window_center()
