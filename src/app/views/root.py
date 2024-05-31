import tkinter as tk


class Root(tk.Tk):
    def __init__(self, width: int=300, height: int=800):
        super().__init__()
        
        self.title('Measure Parser')
        self.iconbitmap()
