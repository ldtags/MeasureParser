import tkinter as tk

from src import utils


class Root(tk.Tk):
    def __init__(self, width: int=700, height: int=700):
        super().__init__()

        self.title('Measure Parser')
        self.iconbitmap(utils.get_asset_path('app.ico'))
        self.geometry(f'{width}x{height}')
        self.minsize(width=width, height=height)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.container = tk.Frame(self, bg='#ffffff')
        self.container.grid(row=0, column=0, sticky=tk.NSEW)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
