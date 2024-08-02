import tkinter as tk
import tkinter.ttk as ttk

from src.app.widgets import (
    Page,
    Frame,
    ScrollableFrame,
    OptionLabel,
    Button
)


class ProgressPage(Page):
    key = 'progress'

    def __init__(self, parent: tk.Misc, root: tk.Tk, **kwargs):
        Page.__init__(self, parent, root, **kwargs)

        # self.intro_label = OptionLabel(self,
        #                                title='Parsing',
        #                                sub_title='Please wait while the'
        #                                          ' measure is being parsed.'
        #                                          '\nThis may take a few'
        #                                          ' minutes.',
        #                                img_name='etrm.png',
        #                                ipadx=(15, 15),
        #                                ipady=(20, 20),
        #                                bg='#ffffff')
        # self.intro_label.pack(side=tk.TOP,
        #                       anchor=tk.NW,
        #                       fill=tk.X)

        # self.log_frame = ScrollableFrame(self,
        #                                  canvas_bg='#ffffff',
        #                                  scrollbar=True)
        # self.log_frame.pack(side=tk.TOP,
        #                     anchor=tk.NW,
        #                     fill=tk.BOTH,
        #                     expand=tk.TRUE,
        #                     padx=(20, 20),
        #                     pady=(20, 20))

        # self.controls_frame = ControlsFrame(self)
        # self.controls_frame.pack(side=tk.BOTTOM,
        #                          anchor=tk.S,
        #                          fill=tk.X)

    def show(self) -> None:
        self.log_frame.clear()
        self.controls_frame.progress_var.set(0)
        super().show()


class ControlsFrame(Frame):
    def __init__(self, parent: Frame, **kwargs):
        Frame.__init__(self, parent, **kwargs)

        self.separator = ttk.Separator(self)
        self.separator.pack(side=tk.TOP,
                            anchor=tk.S,
                            fill=tk.X)

        self.progress_var = tk.IntVar(self, 0)
        self.progress_bar = ttk.Progressbar(self,
                                            variable=self.progress_var)
        self.progress_bar.pack(side=tk.LEFT,
                               anchor=tk.CENTER,
                               fill=tk.X,
                               expand=tk.TRUE,
                               padx=(30, 15),
                               pady=(20, 20))

        self.cont_btn = Button(self,
                               pady=0,
                               padx=30,
                               text='Close',
                               state='disabled')
        self.cont_btn.pack(side=tk.RIGHT,
                           anchor=tk.E,
                           padx=(15, 30),
                           pady=(20, 20))

        self.back_btn = Button(self,
                               pady=0,
                               padx=30,
                               text='Back')
        self.back_btn.pack(side=tk.RIGHT,
                           anchor=tk.E,
                           padx=(30, 15),
                           pady=(20, 20))
