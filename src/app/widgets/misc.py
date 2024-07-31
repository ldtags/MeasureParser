import tkinter as tk

from src.app.types import TK_EVENT_BINDING


class Widget(tk.Widget):
    def __init__(self,
                 parent: tk.Misc,
                 widget_name: str,
                 events: list[TK_EVENT_BINDING] | None=None,
                 cnf={},
                 kw={},
                 extra=()):
        tk.Widget.__init__(self, parent, widget_name, cnf, kw, extra)
        self.parent = parent
        if events is not None:
            for child in self.winfo_children():
                child_events = set(child.bind())
                for event, callback in events:
                    if event in child_events:
                        continue
                    child.bind(event, callback)
