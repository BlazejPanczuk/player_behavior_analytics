# sklep_style.py – styl cyberpunk terminal dla segmentu Sklep

COLOR_BG = "#0A0A1A"
COLOR_NAV = "#111122"
TEXT_COLOR = "#00ffff"
BTN_BG = "#070713"
BTN_FG = "#00ffff"
FONT = ("Consolas", 12, "bold")

def stylized_nav_button(parent, text, command):
    import tkinter as tk
    return tk.Button(
        parent,
        text=text,
        font=FONT,
        bg=BTN_BG,
        fg=BTN_FG,
        activebackground=BTN_BG,
        activeforeground=BTN_FG,
        bd=0,
        relief='flat',
        cursor='hand2',
        command=command
    )

def stylized_label(parent, text, font=FONT):
    import tkinter as tk
    return tk.Label(
        parent,
        text=text,
        font=font,
        bg=COLOR_NAV,
        fg=TEXT_COLOR
    )
