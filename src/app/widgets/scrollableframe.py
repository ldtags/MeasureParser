import tkinter as tk
import tkinter.ttk as ttk


class ScrollableFrame(ttk.Frame):
    def __init__(self, parent: tk.Misc, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)

        self.items: list[ttk.Label] = []

        vscrollbar = ttk.Scrollbar(self,
                                   orient=tk.VERTICAL)
        vscrollbar.pack(fill=tk.Y,
                        side=tk.RIGHT,
                        expand=tk.FALSE)

        self.canvas = canvas = tk.Canvas(self,
                                         bd=0,
                                         highlightthickness=0,
                                         yscrollcommand=vscrollbar.set)
        canvas.pack(side=tk.LEFT,
                    fill=tk.BOTH,
                    expand=tk.TRUE)

        vscrollbar.config(command=canvas.yview)

        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        self.interior = interior = ttk.Frame(canvas)
        self.interior_id = canvas.create_window(0,
                                                0,
                                                window=interior,
                                                anchor=tk.NW)

        interior.bind('<Configure>', self.__configure_interior)
        canvas.bind('<Configure>', self.__configure_canvas)
        canvas.bind_all('<MouseWheel>', self.__on_mousewheel)

    def __configure_interior(self, event: tk.Event) -> None:
        width = self.interior.winfo_reqwidth()
        height = self.interior.winfo_reqheight()
        self.canvas.config(scrollregion=f'0 0 {width} {height}')
        if width != self.canvas.winfo_width():
            self.canvas.config(width=width)

    def __configure_canvas(self, event: tk.Event) -> None:
        if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
            self.canvas.itemconfigure(self.interior_id,
                                      width=self.canvas.winfo_width())

    def __on_mousewheel(self, event: tk.Event) -> None:
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    def add(self, text: str) -> None:
        label = ttk.Label(self.interior, text=text)
        label.pack(side=tk.TOP,
                   anchor=tk.NW,
                   fill=tk.X,
                   expand=tk.FALSE,
                   padx=(5, 5),
                   pady=(5, 5))

        self.items.append(label)

    def clear(self) -> None:
        for label in self.items:
            label.destroy()
