import tkinter as tk
import tkinter.ttk as ttk
from pandas import DataFrame
from typing import Literal

from src import assets
from src.app.widgets import Frame, Page, ScrollableFrame, Button, Label
from src.app.components import OptionLabel
from src.permqaqc import FieldData, Severity


OPTIONAL_COLOR = "#0041c2"
MINOR_COLOR = "#fcd12a"
CRITICAL_COLOR = "#c21807"


class ResultsView(Page):
    key = "results"

    def __init__(self, parent: tk.Misc, root: tk.Tk, **kw) -> None:
        super().__init__(parent, root, **kw)

        self.config(bg="#f0f0f0")
        self.grid(row=0, column=0, sticky=tk.NSEW)

        intro_label = OptionLabel(
            self,
            title="QA/QC Results",
            sub_title="Review the below results of the QA/QC process.",
            bg="#ffffff",
            ipadx=(15, 15),
            ipady=(20, 20),
        )
        intro_label.pack(side=tk.TOP, anchor=tk.NW, fill=tk.X)
        intro_label.set_image("etrm.png")

        scroll_frame = ScrollableFrame(self, scrollbar=True)
        scroll_frame.pack(side=tk.TOP, anchor=tk.NW, fill=tk.BOTH, expand=tk.TRUE)

        self.container = container = Frame(scroll_frame.interior)
        self.container.pack(side=tk.TOP, anchor=tk.NW, fill=tk.BOTH, expand=tk.TRUE)
        self.container.grid_rowconfigure((0), weight=1)
        self.container.grid_columnconfigure((0), weight=1)

        self.parser_frame = ParserResultsFrame(container)
        self.permqc_frame = PermQcResultsFrame(container)

        self.controls_frame = ControlsFrame(self)
        self.controls_frame.pack(side=tk.BOTTOM, anchor=tk.S, fill=tk.X)

    def show_frame(self, frame: Literal["parser", "permqc"]) -> None:
        match frame:
            case "parser":
                if self.permqc_frame.winfo_ismapped():
                    self.permqc_frame.grid_forget()

                self.parser_frame.grid(row=0, column=0, sticky=tk.NSEW)
            case "permqc":
                if self.parser_frame.winfo_ismapped():
                    self.parser_frame.grid_forget()

                self.permqc_frame.grid(row=0, column=0, sticky=tk.NSEW)


class ParserResultsFrame(Frame):
    def __init__(self, parent: Frame, **kw) -> None:
        super().__init__(parent, **kw)


class PermQcResultsFrame(Frame):
    def __init__(self, parent: Frame, **kw) -> None:
        super().__init__(parent, **kw)

        self.data: DataFrame | None = None
        self.field_data: FieldData | None = None
        self.items: list[list[Frame]] = []
        self.visible_errs: dict[str, Frame] = {}

        self.grid_columnconfigure((0), weight=2)  # arrow icon column
        self.grid_columnconfigure((2), weight=15)  # field name column
        self.grid_columnconfigure((4, 6, 8), weight=4)  # error columns
        self.grid_columnconfigure((1, 3, 5, 7), weight=0)  # grid lines

        arrow_sep = ttk.Separator(self, orient="vertical")
        arrow_sep.grid(row=0, column=1, sticky=tk.NS)

        field_name_label = Label(self, text="Field")
        field_name_label.grid(row=0, column=2, sticky=tk.NSEW)

        field_name_sep = ttk.Separator(self, orient="vertical")
        field_name_sep.grid(row=0, column=3, sticky=tk.NS)

        error_label = Label(self, text="Optional")
        error_label.grid(row=0, column=4, sticky=tk.NSEW)

        minor_sep = ttk.Separator(self, orient="vertical")
        minor_sep.grid(row=0, column=5, sticky=tk.NS)

        minor_label = Label(self, text="Minor")
        minor_label.grid(row=0, column=6, sticky=tk.NSEW)

        crit_sep = ttk.Separator(self, orient="vertical")
        crit_sep.grid(row=0, column=7, sticky=tk.NS)

        crit_label = Label(self, text="Critical")
        crit_label.grid(row=0, column=8, sticky=tk.NSEW)

        separator = ttk.Separator(self)
        separator.grid(row=1, column=0, columnspan=9, sticky=tk.EW)

    def _show_errs(self, field: str, index: int) -> None:
        if field in self.visible_errs:
            return

        container = Frame(self)
        container.grid(row=index, column=0, columnspan=9, sticky=tk.NSEW)
        container.grid_columnconfigure((0), weight=1)
        container.grid_columnconfigure((1), weight=10)
        container.grid_columnconfigure((2), weight=15)
        container.grid_columnconfigure((3), weight=5)
        self.visible_errs[field] = container
        errs = self.field_data.get(column=field)
        errs.sort(key=lambda entry: entry.severity)
        for i, err in enumerate(errs):
            try:
                field_value = self.data.at[err.y, field]
            except KeyError:
                continue

            field_label = Label(container, text=f"({err.y + 2}) [{field_value}]")
            field_label.grid(row=i, column=1, sticky=tk.NSEW)

            err_label = Label(container, text=err.description)
            err_label.grid(row=i, column=2, sticky=tk.NSEW)

            severity_label = Label(container)
            match err.severity:
                case Severity.OPTIONAL:
                    severity_label.configure(text="optional", text_color=OPTIONAL_COLOR)
                case Severity.SEMI_MINOR | Severity.MINOR:
                    severity_label.configure(text="minor", text_color=MINOR_COLOR)
                case Severity.SEMI_CRITICAL | Severity.CRITICAL:
                    severity_label.configure(text="critical", text_color=CRITICAL_COLOR)
                case other:
                    raise tk.TclError(f"Unknown severity: {other}")

            severity_label.grid(row=i, column=3, sticky=tk.NSEW)

    def _hide_errs(self, field: str) -> None:
        """Removes the permutation items from the view."""

        try:
            self.visible_errs[field]
        except KeyError:
            return

        for child in self.visible_errs[field].winfo_children():
            child.destroy()

        self.visible_errs[field].destroy()
        del self.visible_errs[field]

    def _arrow_on_click(self, event: tk.Event, field: str, index: int) -> None:
        if not isinstance(event.widget, Arrow):
            return

        if self.field_data.get(field) == []:
            return

        if event.widget.state == "down":
            self._hide_errs(field)
            event.widget.state = "up"
        elif event.widget.state == "up":
            self._show_errs(field, index)
            event.widget.state = "down"

    def add_item(self, field: str) -> None:
        if self.field_data is None or self.data is None:
            return

        item_count = len(self.items)
        if item_count == 0:
            index = 0
        else:
            index = item_count * 2  # account for the previous separator and error dropdown

        index += 2  # account for the table header and separator

        arrow = Arrow(self)
        field_label = Label(self, text=field)

        optional_errs = self.field_data.get(column=field, severity=Severity.OPTIONAL)
        optional_err_label = Label(
            self, text=f"{len(optional_errs)}", text_color=OPTIONAL_COLOR
        )

        minor_errs = self.field_data.get(column=field, severity=Severity.MINOR)
        semi_minor_errs = self.field_data.get(
            column=field, severity=Severity.SEMI_MINOR
        )
        minor_err_label = Label(
            self,
            text=f"{len(minor_errs) + len(semi_minor_errs)}",
            text_color=MINOR_COLOR,
        )

        critical_errs = self.field_data.get(column=field, severity=Severity.CRITICAL)
        semi_critical_errs = self.field_data.get(
            column=field, severity=Severity.SEMI_CRITICAL
        )
        critical_err_label = Label(
            self,
            text=f"{len(critical_errs) + len(semi_critical_errs)}",
            text_color=CRITICAL_COLOR,
        )

        row = [
            arrow,
            field_label,
            optional_err_label,
            minor_err_label,
            critical_err_label,
        ]
        self.items.append(row)

        arrow.grid(row=index, column=0, sticky=tk.NSEW)
        ttk.Separator(self, orient="vertical").grid(row=index, column=1, sticky=tk.NS)
        field_label.grid(row=index, column=2, sticky=tk.NSEW)
        ttk.Separator(self, orient="vertical").grid(row=index, column=3, sticky=tk.NS)
        optional_err_label.grid(row=index, column=4, sticky=tk.NSEW)
        ttk.Separator(self, orient="vertical").grid(row=index, column=5, sticky=tk.NS)
        minor_err_label.grid(row=index, column=6, sticky=tk.NSEW)
        ttk.Separator(self, orient="vertical").grid(row=index, column=7, sticky=tk.NS)
        critical_err_label.grid(row=index, column=8, sticky=tk.NSEW)
        ttk.Separator(self).grid(row=index + 1, column=0, columnspan=9, sticky=tk.EW)

        arrow.bind("<Button-1>", lambda e: self._arrow_on_click(e, field, index + 2))

    def load_data(self, data: DataFrame, field_data: FieldData) -> None:
        self.data = data
        self.field_data = field_data
        for field in field_data.data:
            self.add_item(field)

    def clear_data(self) -> None:
        self.field_data = None
        for row in self.items:
            for col in row:
                col.destroy()

        self.items.clear()


class Arrow(Frame):
    def __init__(self, parent: tk.Misc, **kw) -> None:
        super().__init__(parent, cursor="hand2", **kw)

        size = (20, 20)
        self.state: Literal["up", "down"] = "up"
        self.up_arrow = assets.get_tkimage("up-arrow.png", size=size)
        self.down_arrow = assets.get_tkimage("up-arrow.png", size=size, rotation=180)

        self.img_label = Label(self, image=self.up_arrow)

    def flip(self) -> None:
        img = None
        match self.state:
            case "up":
                img = self.down_arrow
            case "down":
                img = self.up_arrow
            case other:
                raise tk.TclError(f"Unknown arrow state: {other}")

        self.img_label.configure(image=img)


class ControlsFrame(Frame):
    def __init__(self, parent: Frame, **kw) -> None:
        super().__init__(parent, **kw)

        self.separator = ttk.Separator(self)
        self.separator.pack(side=tk.TOP, anchor=tk.S, fill=tk.X)

        self.close_btn = Button(self, pady=0, padx=30, text="Close")
        self.close_btn.pack(side=tk.RIGHT, anchor=tk.E, padx=(15, 35), pady=(20, 20))
