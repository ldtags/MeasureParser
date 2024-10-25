import tkinter as tk
import tkinter.ttk as ttk

from .misc import Widget
from .labels import Label


class Frame(Widget):
    def __init__(self, parent: tk.Misc, **kw):
        try:
            kw['bg']
        except KeyError:
            if isinstance(parent, Frame):
                kw['bg'] = parent['bg']

        Widget.__init__(self, parent, 'frame', kw=kw)

        self.parent = parent
        self.bind('<Button-1>', lambda _: self.focus())


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

        style = ttk.Style(self)
        style.layout(
            'Vertical.TScrollbar', 
            [
                (
                    'Vertical.Scrollbar.trough',
                    {
                        'children': [
                            (
                                'Vertical.Scrollbar.thumb', 
                                {
                                    'expand': '1', 
                                    'sticky': 'nswe'
                                }
                            )
                        ],
                        'sticky': 'ns'
                    }
                )
            ]
        )
        self.vscrollbar = ttk.Scrollbar(self,
                                        orient=tk.VERTICAL,
                                        style='Vertical.TScrollbar')
        if scrollbar:
            self.vscrollbar.pack(fill=tk.Y,
                                 side=tk.RIGHT,
                                 expand=tk.FALSE)

        _bg = canvas_bg
        if _bg is None:
            try:
                _bg = parent['bg']
            except tk.TclError:
                _bg = None

        self.canvas = canvas = tk.Canvas(self,
                                         bd=0,
                                         highlightthickness=0,
                                         yscrollcommand=self.vscrollbar.set,
                                         bg=_bg)
        canvas.pack(side=tk.LEFT,
                    fill=tk.BOTH,
                    expand=tk.TRUE)

        self.vscrollbar.config(command=canvas.yview)

        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        self.interior = interior = Frame(canvas,
                                         bg=canvas['bg'])
        self.interior_id = canvas.create_window(0,
                                                0,
                                                window=interior,
                                                anchor=tk.NW)

        canvas.bind('<Configure>', self.__configure_canvas)

        interior.blacklist.append('<Configure>')
        interior.bind('<Configure>', self.__configure_interior)
        interior.bind_all('<MouseWheel>', self._on_mousewheel)

    def __configure_interior(self, event: tk.Event) -> None:
        width = self.interior.winfo_reqwidth()
        height = self.interior.winfo_reqheight()
        self.canvas.config(scrollregion=f'0 0 {width} {height}')
        if width != self.canvas.winfo_reqwidth():
            self.canvas.config(width=width)

    def __configure_canvas(self, event: tk.Event) -> None:
        canvas_width = self.canvas.winfo_width()
        if self.interior.winfo_reqwidth() != canvas_width:
            self.canvas.itemconfigure(self.interior_id, width=canvas_width)

    def __can_scroll_down(self) -> bool:
        if self.static_scrollbar:
            return True

        if self.items == []:
            return False

        self.items[-1].update()
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

    def add(self, text: str, **kwargs) -> None:
        bg = self.canvas['bg']
        try:
            bg = kwargs['bg']
        except KeyError:
            pass
        try:
            bg = kwargs['background']
        except KeyError:
            pass
        kwargs['bg'] = bg
        label = Label(self.interior,
                      text=text,
                      **kwargs)
        label.pack(side=tk.TOP,
                   anchor=tk.NW,
                   fill=tk.X,
                   expand=tk.FALSE,
                   padx=(self.padding, self.padding),
                   pady=(self.padding, self.padding))

        self.items.append(label)
        self.update()
        self.parent.update()

    def clear(self) -> None:
        for label in self.items:
            label.destroy()
            del label
        self.items = []
