import math
import tkinter as tk
import ttkbootstrap as ttk

from src import assets
from src.app import fonts
from src.app.widgets.frames import Page


class MainPage(Page):
    def __init__(self, parent: ttk.Frame, root: ttk.Window, **kwargs):
        super().__init__(parent, root, **kwargs)

        self.container = ttk.Frame(self)
        self.container.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.BOTH,
            expand=tk.TRUE
        )
        self.container.grid_columnconfigure((0, 4), weight=1)
        self.container.grid_columnconfigure(
            (1, 2, 3),
            weight=0,
            uniform='MainPageContainer'
        )
        self.container.grid_rowconfigure((0, 2), weight=2)
        self.container.grid_rowconfigure((1), weight=1)

        self.parser_button = ToolButton(
            self.container,
            'cog.png',
            'Measure Parser'
        )
        self.parser_button.grid(
            column=1,
            row=1,
            sticky=tk.NSEW,
            padx=(10, 10)
        )


class ToolButton(ttk.Frame):
    def __init__(self,
                 parent: ttk.Frame,
                 image_name: str,
                 text: str,
                 **kwargs):
        style = ttk.Style()
        style.configure(
            'Main.Button.Border.TFrame',
            background=style.colors.info
        )
        super().__init__(
            parent,
            style='Main.Button.Border.TFrame',
            **kwargs
        )

        border = ttk.Frame(self)
        border.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.BOTH,
            expand=tk.TRUE,
            padx=(2, 2),
            pady=(2, 2)
        )

        self.container = ttk.Frame(border)
        self.container.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.BOTH,
            expand=tk.TRUE,
            padx=(5, 5),
            pady=(5, 5)
        )
        self.container.grid_columnconfigure((0, 2), weight=1)
        self.container.grid_columnconfigure((1), weight=0)
        self.container.grid_rowconfigure((0), weight=2)
        self.container.grid_rowconfigure((1), weight=1)

        self.label = ttk.Label(
            self.container,
            text=text,
            font=fonts.HEADER_2
        )
        self.label.grid(
            column=1,
            row=1,
            sticky=tk.NSEW
        )

        img = assets.get_image(image_name)
        base_width = img.width
        base_height = img.height
        aspect_ratio = base_height / base_width

        border.update()
        img_width = border.winfo_reqwidth()
        img_height = img_width * aspect_ratio
        size = (math.floor(img_height), math.floor(img_width))
        tk_img = assets.get_tkimage(image_name, size)
        self.image = ttk.Label(
            self.container,
            image=tk_img,
            justify=tk.CENTER,
            wraplength=border.winfo_reqwidth()
        )
        self.image.grid(
            column=1,
            row=0,
            sticky=tk.NSEW
        )
