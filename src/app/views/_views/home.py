import tkinter as tk
import tkinter.ttk as ttk
from typing import Literal

from src.app import fonts
from src.app.types import HomeViewState, MeasureSourceState
from src.app.widgets import (
    Frame,
    Page,
    FileEntry,
    Button,
    Entry,
    Label,
    ScrollableFrame,
)
from src.app.components import OptionLabel, OptionCheckBox
from src.config import app_config


_EtrmEntryOption = Literal["api_key", "measure"]

_DEFAULT_PAGE_STATE: HomeViewState = "parser"
_DEFAULT_SOURCE_STATE: MeasureSourceState = "local"


class HomeView(Page):
    key = "home"

    def __init__(self, parent: Frame, root: tk.Tk, **kwargs):
        Page.__init__(self, parent, root, **kwargs)

        self._state: HomeViewState = _DEFAULT_PAGE_STATE

        self.config(bg="#f0f0f0")
        self.grid(row=0, column=0, sticky=tk.NSEW)

        self.intro_label = OptionLabel(
            self,
            title="eTRM Measure QA/QC Tool",
            sub_title="Simplifies the eTRM measure QA/QC process by providing"
            " accurate measure data validation.",
            bg="#ffffff",
            ipadx=(15, 15),
            ipady=(20, 20),
        )
        self.intro_label.pack(side=tk.TOP, anchor=tk.NW, fill=tk.X)
        self.intro_label.set_image("etrm.png")

        self.notebook = notebook = ttk.Notebook(self)
        self.notebook.pack(side=tk.TOP, anchor=tk.NW, fill=tk.BOTH, expand=tk.TRUE)

        self.parser_container = parser_container = ParserContainer(notebook)
        self.parser_container.pack(
            side=tk.TOP, anchor=tk.NW, fill=tk.BOTH, expand=tk.TRUE
        )
        notebook.add(parser_container, text="QA/QC Measure")

        self.perm_qc_container = perm_qc_container = PermQcContainer(notebook)
        self.perm_qc_container.pack(
            side=tk.TOP, anchor=tk.NW, fill=tk.BOTH, expand=tk.TRUE
        )
        notebook.add(perm_qc_container, text="QA/QC Permutations")

        self.controls_frame = ControlsFrame(self)
        self.controls_frame.pack(side=tk.BOTTOM, anchor=tk.S, fill=tk.X)

    @property
    def state(self) -> HomeViewState:
        match self._state:
            case "parser" | "permqc":
                pass
            case other:
                raise tk.TclError(f"Unknown home view state: {other}")

        return self._state

    @property
    def source_frame(self) -> "MeasureSourceFrame":
        match self.state:
            case "parser":
                return self.parser_container.source_frame
            case "permqc":
                return self.perm_qc_container.source_frame
            case other:
                raise tk.TclError(f"Unknown home view state: {other}")

    def show(self) -> None:
        super().show()


class PermQcContainer(ScrollableFrame):
    def __init__(self, parent: tk.Frame, **kw) -> None:
        super().__init__(parent, scrollbar=True, **kw)

        self.source_frame = MeasureSourceFrame(
            self.interior,
            title="Permutation Sources",
            file_rb_text="Import CSV File",
            file_title="Measure Permutations CSV File",
            file_subtitle="Select an existing eTRM measure permutations CSV file.",
            etrm_rb_text="Select from the eTRM",
            etrm_title="Measure Version ID",
            etrm_subtitle="A full eTRM measure version ID.",
            file_types=[("CSV File", "*.csv")],
            view_state="permqc",
        )
        self.source_frame.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.BOTH,
            expand=tk.TRUE,
            padx=(10, 10),
            pady=(10, 0),
        )

        self.output_frame = OutputFrame(self.interior)
        self.output_frame.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.BOTH,
            expand=tk.TRUE,
            padx=(10, 10),
            pady=(0, 10),
        )

        self.options_frame = OptionsFrame(self.interior)
        self.options_frame.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.BOTH,
            expand=tk.TRUE,
            padx=(10, 10),
            pady=(10, 25),
        )


class ParserContainer(ScrollableFrame):
    def __init__(self, parent: tk.Frame, **kwargs):
        ScrollableFrame.__init__(self, parent, scrollbar=True, **kwargs)

        self.source_frame = MeasureSourceFrame(
            self.interior,
            title="Measure Sources",
            file_rb_text="Import JSON File",
            file_title="Measure JSON File",
            file_subtitle="Select an existing eTRM measure JSON file.",
            etrm_rb_text="Select from the eTRM",
            etrm_title="Measure Version ID",
            etrm_subtitle="A full eTRM measure version ID.",
            file_types=[("JSON File", "*.json")],
            view_state="parser",
        )
        self.source_frame.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.BOTH,
            expand=tk.TRUE,
            padx=(10, 10),
            pady=(10, 0),
        )

        self.output_frame = OutputFrame(self.interior)
        self.output_frame.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.BOTH,
            expand=tk.TRUE,
            padx=(10, 10),
            pady=(0, 10),
        )

        self.options_frame = OptionsFrame(self.interior)
        self.options_frame.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.BOTH,
            expand=tk.TRUE,
            padx=(10, 10),
            pady=(10, 25),
        )


class MeasureSourceFrame(Frame):
    def __init__(
        self,
        parent: Frame,
        title: str,
        file_rb_text: str,
        file_title: str,
        file_subtitle: str,
        file_types: tuple[str, str] | list[tuple[str, str]],
        etrm_rb_text: str,
        etrm_title: str,
        etrm_subtitle: str,
        view_state: HomeViewState,
        **kw,
    ) -> None:
        super().__init__(parent, **kw)

        # state of None implies that the widget has not yet been fully initialized
        self.state: MeasureSourceState | None = None

        self.view_state = view_state

        self.source_label = OptionLabel(self, title=title, level=0)
        self.source_label.pack(side=tk.TOP, anchor=tk.NW, fill=tk.X)

        self.container = container = Frame(self)
        container.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.BOTH,
            expand=tk.TRUE,
            padx=(10, 10),
            pady=(10, 10),
        )

        container.grid_rowconfigure((0, 2, 4, 6), weight=0)
        container.grid_rowconfigure((1, 3, 5, 7), weight=1)
        container.grid_columnconfigure((0), weight=1)

        self.json_rb_var = tk.IntVar(container, 0)
        self.json_rb = ttk.Radiobutton(
            container,
            variable=self.json_rb_var,
            text=file_rb_text,
            cursor="hand2",
        )
        self.json_rb.grid(row=0, column=0, sticky=tk.NSEW, pady=(0, 5))

        self.json_frame = JSONSourceFrame(
            container, title=file_title, subtitle=file_subtitle, file_types=file_types
        )

        self.etrm_rb_var = tk.IntVar(container, 0)
        self.etrm_rb = ttk.Radiobutton(
            container,
            variable=self.etrm_rb_var,
            text=etrm_rb_text,
            cursor="hand2",
        )
        self.etrm_rb.grid(row=4, column=0, sticky=tk.NSEW, pady=(0, 5))

        self.etrm_frame = ETRMSourceFrame(
            container, title=etrm_title, subtitle=etrm_subtitle
        )

        self.set_state(_DEFAULT_SOURCE_STATE)

        for cb in self.bindings.get("<MouseWheel>", []):
            self.json_rb.bind("<MouseWheel>", cb)
            self.etrm_rb.bind("<MouseWheel>", cb)

    def set_state(self, state: MeasureSourceState) -> None:
        if self.state == state:
            return

        match state:
            case "local":
                if self.etrm_frame.winfo_ismapped():
                    self.etrm_frame.grid_forget()

                self.container.grid_rowconfigure((1, 3), weight=1)
                self.container.grid_rowconfigure((5, 8), weight=0)
                self.json_frame.grid(row=2, column=0, sticky=tk.NSEW, padx=(10, 10))
                self.json_rb_var.set(1)
                self.etrm_rb_var.set(0)
            case "api":
                if self.json_frame.winfo_ismapped():
                    self.json_frame.grid_forget()

                self.container.grid_rowconfigure((1, 3), weight=0)
                self.container.grid_rowconfigure((5, 8), weight=1)
                self.etrm_frame.grid(row=6, column=0, sticky=tk.NSEW, padx=(10, 10))
                self.json_rb_var.set(0)
                self.etrm_rb_var.set(1)
            case other:
                raise tk.TclError(f"Unknown measure source state: {other}")

        self.state = state

    def print_err(self, err: str, etrm_option: _EtrmEntryOption | None = None) -> None:
        match self.state:
            case "local":
                self.json_frame.print_err(err)
            case "api":
                if etrm_option is None:
                    raise tk.TclError("Missing etrm entry option")

                self.etrm_frame.print_err(err, etrm_option)
            case other:
                raise tk.TclError(f"Unknown measure source state: {other}")

    def clear_err(self, etrm_option: _EtrmEntryOption | None = None) -> None:
        match self.state:
            case "local":
                self.json_frame.clear_err()
            case "api":
                if etrm_option is None:
                    raise tk.TclError("Missing etrm entry option")

                self.etrm_frame.clear_err(etrm_option)
            case other:
                raise tk.TclError(f"Unknown measure source state: {other}")


class JSONSourceFrame(Frame):
    def __init__(
        self,
        parent: Frame,
        title: str,
        subtitle: str,
        file_types: tuple[str, str] | list[tuple[str, str]],
        **kw,
    ) -> None:
        Frame.__init__(self, parent, **kw)

        self.grid_columnconfigure((0), weight=1)
        self.grid_rowconfigure((0, 4), weight=1)
        self.grid_rowconfigure((1, 2, 3), weight=0)

        self.file_label = OptionLabel(
            self,
            title=title,
            sub_title=subtitle,
            level=1,
        )
        self.file_label.grid(column=0, row=1, sticky=tk.NSEW)

        self.file_entry = FileEntry(self, file_type="file", types=file_types)
        self.file_entry.grid(column=0, row=2, sticky=tk.NSEW, pady=(5, 0))

        self.file_err_var = tk.StringVar(self, "")
        self.file_err_label = Label(
            self, variable=self.file_err_var, text_color="#ff0000"
        )
        self.file_err_label.grid(column=0, row=3, sticky=tk.NSEW, pady=(2.5, 0))

    def print_err(self, err: str) -> None:
        self.file_err_var.set(err)

    def clear_err(self) -> None:
        self.file_err_var.set("")

    def disable(self) -> None:
        self.file_entry.disable()

    def enable(self) -> None:
        self.file_entry.enable()

    def clear(self) -> None:
        self.file_entry.clear()

    def is_empty(self) -> bool:
        if self.file_entry.get() != "":
            return False

        return True


class ETRMSourceFrame(Frame):
    def __init__(self, parent: Frame, title: str, subtitle: str, **kw):
        Frame.__init__(self, parent, **kw)

        self.measure_label = OptionLabel(
            self,
            title=title,
            sub_title=subtitle,
            level=1,
        )
        self.measure_label.pack(side=tk.TOP, anchor=tk.NW, fill=tk.X)

        self.measure_entry = Entry(self, placeholder="SWAP001-06")
        self.measure_entry.pack(
            side=tk.TOP, anchor=tk.NW, fill=tk.X, expand=tk.TRUE, pady=(5, 0)
        )

        self.measure_err_var = tk.StringVar(self, "")
        self.measure_err_label = Label(
            self, variable=self.measure_err_var, text_color="#ff0000"
        )
        self.measure_err_label.pack(side=tk.TOP, anchor=tk.NW, fill=tk.X, pady=(2.5, 0))

        self.key_label = OptionLabel(
            self,
            title="API Key",
            sub_title="An eTRM API key, used for authorizing requests to"
            " the eTRM API.",
            level=1,
        )
        self.key_label.pack(side=tk.TOP, anchor=tk.NW, fill=tk.X)

        self.api_key_entry = Entry(self, placeholder="Token ae38f19b8c03de122...")
        self.api_key_entry.pack(
            side=tk.TOP, anchor=tk.NW, fill=tk.X, expand=tk.TRUE, pady=(5, 0)
        )

        self.rm_var = tk.IntVar(self, 0)
        ttk.Style().configure("RM.TCheckbutton", font=fonts.BODY)
        self.rm_checkbox = ttk.Checkbutton(
            self,
            text="Remember Me",
            variable=self.rm_var,
            cursor="hand2",
            style="RM.TCheckbutton",
        )
        self.rm_checkbox.pack(
            side=tk.TOP, anchor=tk.NW, pady=(1, 0)
        )

        self.api_key_err_var = tk.StringVar(self, "")
        self.api_key_err_label = Label(
            self, variable=self.api_key_err_var, text_color="#ff0000"
        )
        self.api_key_err_label.pack(side=tk.TOP, anchor=tk.NW, fill=tk.X, pady=(2.5, 0))

    def print_err(self, err: str, entry: Literal["api_key", "measure"]) -> None:
        match entry:
            case "api_key":
                self.api_key_err_var.set(err)
            case "measure":
                self.measure_err_var.set(err)
            case _:
                pass

    def clear_err(self, entry: Literal["api_key", "measure"] | None = None) -> None:
        if entry is None:
            self.api_key_err_var.set("")
            self.measure_err_var.set("")
            return

        match entry:
            case "api_key":
                self.api_key_err_var.set("")
            case "measure":
                self.measure_err_var.set("")
            case _:
                pass

    def disable(self) -> None:
        self.api_key_entry.disable()
        self.measure_entry.disable()

    def enable(self) -> None:
        self.api_key_entry.enable()
        self.measure_entry.enable()

    def is_empty(self) -> bool:
        if self.api_key_entry.get() != "":
            return False

        if self.measure_entry.get() != "":
            return False

        return True


class OutputFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        Frame.__init__(self, parent, **kwargs)

        self.output_label = OptionLabel(self, title="Output")
        self.output_label.pack(side=tk.TOP, anchor=tk.NW, fill=tk.X)

        self.options_frame = self._OutputOptionsFrame(self)
        self.options_frame.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.BOTH,
            expand=True,
            padx=(10, 10),
            pady=(10, 0),
        )

        self.file_entry = self.options_frame.fname_entry
        self.dir_entry = self.options_frame.outdir_entry

    class _OutputOptionsFrame(Frame):
        def __init__(self, parent: Frame, **kwargs):
            Frame.__init__(self, parent, **kwargs)

            self.grid_columnconfigure((0), weight=1)
            self.grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=0)

            self.fname_label = OptionLabel(
                self,
                title="Output File Name",
                sub_title="The file name of the parser output file.",
                level=1,
            )
            self.fname_label.grid(row=0, column=0, sticky=tk.NSEW)

            self.fname_entry = Entry(self, text="parser_output")
            self.fname_entry.grid(row=1, column=0, sticky=tk.NSEW, pady=(5, 0))

            self.file_err_var = tk.StringVar(self, " ")
            self.file_err_label = Label(
                self, textvariable=self.file_err_var, fg="#ff0000"
            )
            self.file_err_label.grid(row=2, column=0, sticky=tk.NSEW, pady=(0, 10))

            self.outdir_label = OptionLabel(
                self,
                title="Output File Location",
                sub_title="The folder that the parser output file will be"
                " placed in.",
                level=1,
            )
            self.outdir_label.grid(row=3, column=0, sticky=tk.NSEW)

            self.outdir_entry = FileEntry(self, text=app_config.output_path)
            self.outdir_entry.grid(row=4, column=0, sticky=tk.NSEW, pady=(5, 0))

            self.outdir_err_var = tk.StringVar(self, " ")
            self.outdir_err_label = Label(
                self, textvariable=self.outdir_err_var, fg="#ff0000"
            )
            self.outdir_err_label.grid(row=5, column=0, sticky=tk.NSEW)

    def print_err(self, err: str, entry: Literal["dir", "file"]) -> None:
        match entry:
            case "dir":
                self.options_frame.outdir_err_var.set(err)
            case "file":
                self.options_frame.file_err_var.set(err)
            case other:
                raise tk.TclError(f"Unknown output entry: {other}")

    def clear_err(self, entry: Literal["dir", "file"] | None = None) -> None:
        if entry is None:
            self.options_frame.file_err_var.set("")
            self.options_frame.outdir_err_var.set("")
        match entry:
            case "dir":
                self.options_frame.outdir_err_var.set("")
            case "file":
                self.options_frame.file_err_var.set("")
            case other:
                raise tk.TclError(f"Unknown output entry: {other}")


class OptionsFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        Frame.__init__(self, parent, **kwargs)

        self.label = OptionLabel(self, title="Options")
        self.label.pack(side=tk.TOP, anchor=tk.NW, fill=tk.X, pady=(0, 10))

        self.container = Frame(self)
        self.container.pack(
            side=tk.TOP, anchor=tk.NW, fill=tk.BOTH, expand=tk.TRUE, padx=(10, 10)
        )

        self.container.grid_columnconfigure(
            (0, 1, 2), weight=1, uniform="OptionsFrameCols"
        )
        self.container.grid_rowconfigure((0), weight=1)

        self.override_file = OptionCheckBox(
            self.container,
            text="Override File",
            sub_text="Override the existing file if a file conflict occurs",
        )
        self.override_file.grid(row=0, column=0, sticky=tk.NSEW)

        self.validate_permutations = OptionCheckBox(
            self.container,
            text="Validate Permutations",
            sub_text="Validate the mapped permutation fields (JSON file" " only)",
        )
        # self.validate_permutations.grid(row=0, column=1, sticky=tk.NSEW, padx=(0, 5))

        self.qa_qc_permutations = OptionCheckBox(
            self.container,
            text="QA/QC Permutations",
            sub_text="QA/QC the measure's permutations (eTRM API only)",
        )
        # self.qa_qc_permutations.grid(row=0, column=2, sticky=tk.NSEW, padx=(5, 5))


class ControlsFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        Frame.__init__(self, parent, **kwargs)

        self.separator = ttk.Separator(self)
        self.separator.pack(side=tk.TOP, anchor=tk.S, fill=tk.X)

        self.start_btn = Button(self, pady=0, padx=30, text="Start")
        self.start_btn.pack(side=tk.RIGHT, anchor=tk.E, padx=(15, 30), pady=(20, 20))

        self.close_btn = Button(self, pady=0, padx=30, text="Close")
        self.close_btn.pack(side=tk.RIGHT, anchor=tk.E, padx=(30, 15), pady=(20, 20))
