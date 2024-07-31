import tkinter as tk
from typing import Callable, Literal


class Widget(tk.Widget):
    def __init__(self,
                 parent: tk.Misc,
                 widget_name: str,
                 cnf={},
                 kw={},
                 extra=()):
        tk.Widget.__init__(self, parent, widget_name, cnf, kw, extra)
        self.bindings: dict[str, list[Callable[[tk.Event], None]]] = {}
        self.blacklist: list[str] = []
        self.parent = parent
        self.config = self.configure

        if isinstance(parent, Widget):
            for event, callbacks in parent.bindings.items():
                if event not in parent.blacklist:
                    for callback in callbacks:
                        self.bind(event, callback)

    def bind(self,
             event: str | None=None,
             callback: Callable[[tk.Event], None] | None=None,
             add: bool | Literal['+', ''] | None=None
            ) -> str | tuple[str, ...]:
        if event and callback:
            if add is None or not add or add == '':
                self.bindings[event] = [callback]
            else:
                callbacks = self.bindings.get(event, [])
                callbacks.append(callback)
                self.bindings[event] = callbacks

        return super().bind(event, callback, add)

    def bind_all(self,
                 event: str | None=None,
                 callback: Callable[[tk.Event], None] | None=None,
                 add: bool | Literal['+', ''] | None=None
                ) -> str | tuple[str, ...]:
        self.bind(event, callback, add)
        if event not in self.blacklist:
            for child in self.winfo_children():
                if isinstance(child, Widget):
                    child.bind(event, callback, add)
        return super().bind_all(event, callback, add)
