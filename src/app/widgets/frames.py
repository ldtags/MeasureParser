import tkinter as tk
import tkinter.ttk as ttk

from src.app.types import TK_EVENT_BINDING


class Frame(tk.Frame):
    def __init__(self,
                 parent: tk.Misc,
                 events: list[TK_EVENT_BINDING] | None=None,
                 **kwargs):
        try:
            kwargs['bg']
        except KeyError:
            if isinstance(parent, tk.Frame):
                kwargs['bg'] = parent['bg']

        tk.Frame.__init__(self, parent, **kwargs)

        self.parent = parent
        self.bind('<Button-1>', lambda _: self.focus())
        for event, callback in events or []:
            self.bind(event, callback)


class Page(Frame):
    key: str

    def __init__(self, parent: tk.Misc, root: tk.Tk, **kwargs):
        Frame.__init__(self, parent, **kwargs)
        self.parent = parent
        self.root = root

    def show(self) -> None:
        self.tkraise()
        self.update()


class Toplevel(tk.Toplevel):
    def __init__(self, parent: tk.BaseWidget, **kwargs):
        tk.Toplevel.__init__(self, parent, **kwargs)

        self.parent = parent

        self.bind('<Button-1>', self.focus)

        x_offset = parent.winfo_width() // 2 - self.winfo_width() // 2
        y_offset = parent.winfo_height() // 2 - self.winfo_height() // 2
        x = parent.winfo_x() + x_offset
        y = parent.winfo_y() + y_offset
        self.geometry(f'+{x}+{y}')


class ScrollableFrame(Frame):
    def __init__(self,
                 parent: tk.Frame,
                 padding: int=5,
                 canvas_bg: str | None=None,
                 scrollbar: bool=False,
                 **kwargs):
        Frame.__init__(self, parent, **kwargs)
        self.parent = parent
        self.padding = padding
        self.static_scrollbar = scrollbar

        self.items: list[ttk.Label] = []

        self.vscrollbar = ttk.Scrollbar(self,
                                        orient=tk.VERTICAL)
        if scrollbar:
            self.vscrollbar.pack(fill=tk.Y,
                                 side=tk.RIGHT,
                                 expand=tk.FALSE)

        self.canvas = canvas = tk.Canvas(self,
                                         bd=0,
                                         highlightthickness=0,
                                         yscrollcommand=self.vscrollbar.set,
                                         bg=canvas_bg or parent['bg'])
        canvas.pack(side=tk.LEFT,
                    fill=tk.BOTH,
                    expand=tk.TRUE)

        self.vscrollbar.config(command=canvas.yview)

        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        self.interior = interior = ttk.Frame(canvas)
        self.interior_id = canvas.create_window(0,
                                                0,
                                                window=interior,
                                                anchor=tk.NW)

        interior.bind('<Configure>', self.__configure_interior)
        canvas.bind('<Configure>', self.__configure_canvas)
        canvas.bind_all('<MouseWheel>', self._on_mousewheel)

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

    def __can_scroll_down(self) -> bool:
        if self.static_scrollbar:
            return True

        if self.items == []:
            return False

        final_y_pos = self.items[-1].winfo_y()
        final_height = self.items[-1].winfo_reqheight()
        canvas_height = self.canvas.winfo_reqheight()
        if final_y_pos + final_height + self.padding < canvas_height:
            return False

        return True

    def _on_mousewheel(self, event: tk.Event) -> None:
        delta = int(-1 * (event.delta / 120))
        if delta < 0 and not self.__can_scroll_down():
            return

        self.canvas.yview_scroll(delta, 'units')

    def update(self) -> None:
        if not self.static_scrollbar and self.__can_scroll_down():
            self.vscrollbar.pack(fill=tk.Y,
                                 side=tk.RIGHT,
                                 expand=tk.FALSE)
        super().update()

    def add(self, text: str) -> None:
        label = ttk.Label(self.interior,
                          text=text,
                          background=self.canvas['bg'],
                          padding=self.padding)
        label.pack(side=tk.TOP,
                   anchor=tk.NW,
                   fill=tk.X,
                   expand=tk.FALSE)

        self.items.append(label)
        self.update()
        self.parent.update()

    def clear(self) -> None:
        for label in self.items:
            label.destroy()
            del label
        self.items = []
