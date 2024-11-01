"""This module contains all custom entry-based Tkinter widgets."""

__all__ = ["Entry", "FileNameEntry", "FileEntry"]


import tkinter as tk
import tkinter.font as tkf
import tkinter.filedialog as filedialog
from typing import Literal

from .misc import Widget
from .labels import Label
from .frames import Frame
from .buttons import Button

from src import utils, _ROOT
from src.app import fonts


_DEFAULT_IPADX = 3
_DEFAULT_IPADY = 3


class _Entry(Widget):
    def __init__(
        self,
        parent: tk.Misc,
        text_color: str = "black",
        relief: str = tk.SOLID,
        font: tuple[str, int, str | None] = fonts.BODY,
        **kwargs,
    ):
        kw = {"fg": text_color, "relief": relief, "font": font, "borderwidth": 0}
        for key, val in kwargs.items():
            kw[key] = val

        super().__init__(parent, "entry", kw=kw)


class Entry(Widget, tk.XView):
    """Custom Tkinter entry widget."""

    def __init__(
        self,
        parent: tk.Misc,
        placeholder: str | None = None,
        placeholder_color: str = "grey",
        text: str | None = None,
        text_color: str = "black",
        relief: str = tk.FLAT,
        border_width: float = 1,
        border_color: str = "#adadad",
        font: tuple[str, int, str | None] = fonts.BODY,
        bg: str = "#ffffff",
        disabledbackground: str = "#dfdfdf",
        ipadx: int = _DEFAULT_IPADX,
        ipady: int = _DEFAULT_IPADY,
        **kwargs,
    ):
        """Initializes a new custom Tkinter entry widget.

        Used to create a Tkinter entry with more customization options.

        Supports all standard Tkinter entry options, as well as:
            - `placeholder` placeholder text that disappears when the entry
            is focused.

            - `placeholder_color` the color of the placeholder text. This
            cannot be the same color as `text_color`.

            - `ipadx` the left-sided internal padding of the entry.

            - `border_width` specifies the width of the entry border.

            - `border_color` specifies the color of the entry border.

        Some standard Tkinter entry options have been renamed, such as:
            - `text_color` replaces `fg`

        If a standard Tkinter entry options that has been replaced is included
        in `kwargs`, it will override the replacement arg.

        New methods include:
            - `enable` sets the state to normal and cursor type to hand2.

            - `disable` sets the state to disabled and the cursor type to
            arrow.

            - `selection_all` | `select_all` selects all text within the entry

            - `clear` clears all text within the entry.

            - `set_text` clears and sets text within the entry.

            - `set_validator` sets an input validator
        """

        assert text_color != placeholder_color

        kw = {
            "highlightcolor": border_color,
            "highlightbackground": border_color,
            "highlightthickness": border_width,
            "height": font[1],
            "bg": bg,
        }

        Widget.__init__(self, parent, "frame", cnf={}, kw=kw)

        self.pad_frame = Frame(self, relief=relief, bg=bg)
        self.pad_frame.pack(side=tk.RIGHT, anchor=tk.NW, fill=tk.BOTH, expand=tk.TRUE)

        self.is_placeholder = False
        self.placeholder = placeholder
        self.placeholder_color = placeholder_color
        self.text_color = text_color
        self.text = text
        self._entry_var = tk.StringVar(self, "")
        self.entry = _Entry(
            self.pad_frame,
            text_color,
            relief,
            font,
            bg=bg,
            disabledbackground=disabledbackground,
            textvariable=self._entry_var,
            **kwargs,
        )

        self.entry.pack(
            side=tk.TOP,
            anchor=tk.NW,
            fill=tk.BOTH,
            expand=tk.TRUE,
            padx=(ipadx, 0),
            pady=(ipady, ipady),
        )

        if text:
            self.insert(0, text)
        elif placeholder:
            self.__put_placeholder()

        self.bind("<FocusIn>", self.__focus_in)
        self.bind("<FocusOut>", self.__focus_out)
        self.__bind_dynamic_events()

    def __put_placeholder(self) -> None:
        if self.placeholder is None:
            return

        if self.is_placeholder:
            return

        self.is_placeholder = True
        self.entry["fg"] = self.placeholder_color
        self.insert(0, self.placeholder)

    def __focus_in(self, event: tk.Event) -> None:
        if self.placeholder is not None and self.is_placeholder:
            self.is_placeholder = False
            self.delete(0, tk.END)
            self.entry["fg"] = self.text_color

    def __focus_out(self, event: tk.Event) -> None:
        if self.placeholder is not None and self.get() == "":
            self.__put_placeholder()

    def __on_pad_frame_click(self, event: tk.Event) -> None:
        self.entry.focus()
        self.icursor(0)

    def __on_pad_frame_double_click(self, event: tk.Event) -> None:
        self.entry.focus()
        self.selection_range(0, tk.END)

    def __bind_dynamic_events(self) -> None:
        self.entry.bind("<Double-Button-1>", lambda _: self.select_all())
        self.pad_click_id = self.pad_frame.bind(
            "<Button-1>",
            self.__on_pad_frame_click,
        )
        self.pad_double_click_id = self.pad_frame.bind(
            "<Double-Button-1>", self.__on_pad_frame_double_click
        )

    def __unbind_dynamic_events(self) -> None:
        self.entry.unbind("<Double-Button-1>")
        self.pad_frame.unbind("<Button-1>")
        self.pad_frame.unbind("<Double-Button-1>")

    def delete(self, first: str | int, last: str | int | None = None) -> None:
        """Delete text from FIRST to LAST (not included)."""

        self.entry.tk.call(self.entry._w, "delete", first, last)

    def get(self) -> str:
        """Return the text."""

        if self.is_placeholder:
            return ""

        return self.entry.tk.call(self.entry._w, "get")

    def icursor(self, index: str | int) -> None:
        """Insert cursor at INDEX."""

        self.entry.tk.call(self.entry._w, "icursor", index)

    def index(self, index: str | int) -> int:
        """Return position of cursor."""

        return self.entry.tk.getint(self.entry.tk.call(self.entry._w, "index", index))

    def insert(self, index: str | int, string: str) -> None:
        """Insert STRING at INDEX."""

        self.entry.tk.call(self.entry._w, "insert", index, string)

    def scan_mark(self, x) -> None:
        """Remember the current X, Y coordinates."""

        self.entry.tk.call(self.entry._w, "scan", "mark", x)

    def scan_dragto(self, x) -> None:
        """Adjust the view of the canvas to 10 times the
        difference between X and Y and the coordinates given in
        scan_mark.
        """

        self.entry.tk.call(self.entry._w, "scan", "dragto", x)

    def selection_adjust(self, index: str | int) -> None:
        """Adjust the end of the selection near the cursor to INDEX."""

        self.entry.tk.call(self.entry._w, "selection", "adjust", index)

    select_adjust = selection_adjust

    def selection_clear(self) -> None:
        """Clear the selection if it is in this widget."""

        self.entry.tk.call(self.entry._w, "selection", "clear")

    select_clear = selection_clear

    def selection_from(self, index: str | int) -> None:
        """Set the fixed end of a selection to INDEX."""

        self.entry.tk.call(self.entry._w, "selection", "from", index)

    select_from = selection_from

    def selection_present(self) -> bool:
        """Return True if there are characters selected in the entry, False
        otherwise.
        """

        return self.entry.tk.getboolean(
            self.entry.tk.call(self.entry._w, "selection", "present")
        )

    select_present = selection_present

    def selection_range(self, start: str | int, end: str | int) -> None:
        """Set the selection from START to END (not included)."""

        self.entry.tk.call(self.entry._w, "selection", "range", start, end)

    select_range = selection_range

    def selection_to(self, index: str | int) -> None:
        """Set the variable end of a selection to INDEX."""

        self.entry.tk.call(self.entry._w, "selection", "to", index)

    select_to = selection_to

    def selection_all(self) -> None:
        """Set the selection to include all text."""

        self.selection_range(0, tk.END)

    select_all = selection_all

    def disable(self) -> None:
        self.entry.config(cursor="arrow", state=tk.DISABLED)
        self.pad_frame.config(cursor="arrow", bg=self.entry.cget("disabledbackground"))
        self.__unbind_dynamic_events()

    def enable(self) -> None:
        self.entry.config(cursor="xterm", state=tk.NORMAL)
        self.pad_frame.config(cursor="xterm", bg=self.entry.cget("bg"))
        self.__bind_dynamic_events()

        if self.is_placeholder:
            self.entry.config(fg=self.placeholder_color)

    def clear(self) -> None:
        self.delete(0, tk.END)
        self.__put_placeholder()

    def set_text(self, text: str) -> None:
        if self.placeholder is not None and self.is_placeholder:
            self.entry["fg"] = self.text_color

        self.is_placeholder = False
        # self.delete(0, tk.END)
        # self.insert(0, text)
        self._entry_var.set(text)

    def set_validator(self, validate: str, command: tuple[str, str]) -> None:
        self.entry.config(validate=validate, validatecommand=command)


class FileNameEntry(Entry):
    """Custom entry widget for restricting file name inputs."""

    def __init__(
        self,
        parent: tk.Widget,
        placeholder: str | None = None,
        placeholder_color="grey",
        text: str | None = None,
        relief=tk.SOLID,
        border_width: int = 1,
        border_color: str = "#adadad",
        font=fonts.BODY,
        file_ext: str = "txt",
        ipadx=_DEFAULT_IPADX,
        ipady=_DEFAULT_IPADY,
        **kwargs,
    ):
        """Initializes a new `FileNameEntry` instance.

        Ensures that any input into this entry ends with a specified
        file extension.

        Class-specific args:
            - `file_ext` specifies the file extension that all entry
            input is required to end with.
        """

        Entry.__init__(
            self,
            parent,
            placeholder=placeholder,
            placeholder_color=placeholder_color,
            text=f"{text}.{file_ext}",
            relief=relief,
            border_width=border_width,
            border_color=border_color,
            font=font,
            ipadx=ipadx,
            ipady=ipady,
            **kwargs,
        )
        self.file_ext = file_ext

        self.bind("<FocusIn>", self.shift_cursor)

    def shift_cursor(self, *args) -> None:
        self.focus_set()

        try:
            index = self.get().rindex(f".{self.file_ext}")
        except ValueError:
            return

        self.icursor(index)


class FileEntry(Entry):
    """Custom widget that opens either a file or directory dialog."""

    def __init__(
        self,
        parent: tk.Widget,
        initial_dir: str | None = None,
        text: str | None = None,
        file_type: Literal["file", "directory"] = "directory",
        types: list[tuple[str, str | list[str] | None]] | None = None,
        label_text: str | None = None,
        font=fonts.BODY,
        textvariable: tk.Variable | None = None,
        ipadx: int = _DEFAULT_IPADX,
        ipady: int = _DEFAULT_IPADY,
        **kwargs,
    ):
        Entry.__init__(
            self, parent, text=text, font=font, ipadx=ipadx, ipady=ipady, **kwargs
        )

        self.types = types
        self.file_type = file_type
        self.initial_dir = initial_dir or _ROOT
        self.file_path = tk.StringVar(self, "")

        if label_text:
            self.label = Label(self, text=label_text, font=font, bg=self["bg"])
            self.label.pack(side=tk.LEFT, anchor=tk.NE, padx=(0, 5))

        if textvariable:
            self.entry.config(textvariable=textvariable)

        entry_height = tkf.Font(font=font).metrics("linespace") + ipady + 1
        img_size = (entry_height, entry_height)
        dir_img = utils.get_tkimage("folder.png", size=img_size)
        self.button = Button(
            self,
            pady=0,
            padx=0,
            image=dir_img,
            highlightbackground="grey",
            highlightcolor="grey",
            highlightthickness=1,
            command=self.open_dialog,
        )
        self.button.pack(side=tk.RIGHT, anchor=tk.NW, padx=(0, 0), pady=(0, 0))

    def configure(self, **kw) -> None:
        self.entry.config(**kw)

    def disable(self) -> None:
        self.button.disable()
        super().disable()

    def enable(self) -> None:
        self.button.enable()
        super().enable()

    def open_dialog(self, *args):
        initial_file = self.file_path.get()
        if initial_file == "":
            initial_file = None

        if self.file_type == "file":
            file_path = filedialog.askopenfilename(
                initialdir=self.initial_dir,
                initialfile=initial_file,
                filetypes=self.types,
            )
        else:
            file_path = filedialog.askdirectory(
                initialdir=self.initial_dir, mustexist=True
            )
        if file_path != "":
            self.file_path.set(file_path)
            self.delete(0, tk.END)
            self.insert(0, file_path)
