import tkinter as tk

COLOR_RIGHT = "#0A0A1A"        # tło jak w głównym oknie
BTN_BG = "#070713"             # neonowy róż do przycisków
BTN_FG = "#00ffff"             # biały tekst na różowym tle
ENTRY_BG = "#1a1a2a"           # ciemne pola wpisywania
ENTRY_FG = "#00ffff"           # cyjanowy tekst
TEXT_COLOR = "#00ffff"         # domyślny kolor tekstu

BUTTON_FONT = ("Arial Black", 16, "bold")

GRADIENT_COLORS = ["#5a002a", "#2a004f", "#004f4f"]

def stylized_entry(parent):
    return tk.Entry(
        parent,
        font=BUTTON_FONT,
        bg=ENTRY_BG,
        fg=ENTRY_FG,
        insertbackground=ENTRY_FG,
        bd=0,
        justify="center",
        highlightthickness=1,
        highlightbackground="#ff00aa"
    )

def stylized_button(parent, text, command):
    return tk.Button(
        parent,
        text=text,
        font=BUTTON_FONT,
        bg=BTN_BG,
        fg=BTN_FG,
        activebackground=BTN_BG,
        activeforeground=BTN_FG,
        bd=0,
        relief='flat',
        cursor='hand2',
        command=command
    )

def stylized_label(parent, text):
    return tk.Label(
        parent,
        text=text,
        font=BUTTON_FONT,
        bg=COLOR_RIGHT,
        fg=TEXT_COLOR
    )
