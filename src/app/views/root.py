import tkinter as tk

from src import utils


class Root(tk.Tk):
    def __init__(self, width: int=300, height: int=800):
        super().__init__()

        self.title('Measure Parser')
        self.iconbitmap(utils.asset_path('etrm.ico'))
        self.geometry(f'{width}x{height}')
        self.minsize(width=width // 2, height=height // 2)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.container = tk.Frame(self)
        self.container.grid(row=0, column=0, sticky=tk.NSEW)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
