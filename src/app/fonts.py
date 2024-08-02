from tkinter import font as tkfont


_DEF_FONT = 'Segoe UI'


BODY = (_DEF_FONT, 8)

BODY_LG = (BODY[0], 9)

BODY_SM = (BODY[0], 7)

BODY_BOLD = (*BODY, tkfont.BOLD)

TITLE = (_DEF_FONT, 12, tkfont.BOLD)

HEADER = (_DEF_FONT, 11, tkfont.BOLD)

HEADER_2 = (_DEF_FONT, 9, tkfont.BOLD)


# legacy fonts

SUB_HEADER = (HEADER[0], 9, tkfont.BOLD)
