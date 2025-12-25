# analiza_style.py – styl Cyberpunk Terminal

# Gradient / kolory tła
GRADIENT_COLORS = ["#0B001B", "#0F001F", "#1A002F"]

# Kolory interfejsu
COLOR_LEFT = "#0F0F1F"
COLOR_RIGHT = "#121222"
COLOR_BOTTOM = "#1A0022"
BORDER_COLOR = "#00FFFF"  # cyjanowy neon
BORDER_WIDTH = 2

# Czcionki i styl tekstu
FONT = ("Consolas", 11, "bold")
HEADER_FONT = ("Orbitron", 14, "bold")

# Styl przycisków – cyberpunk: jasny tekst, kontrastowe tło
BTN_BG = "#111122"
BTN_FG = "#00FFFF"
BUTTON_FONT = ("Consolas", 11, "bold")

# Styl Listboxa
LISTBOX_BG = "#111122"
LISTBOX_FG = "#FFFFFF"
LISTBOX_SELECT_BG = "#003344"
LISTBOX_SELECT_FG = "#00FFFF"

# Styl wykresów
CHART_FACE = "#0B001B"
CHART_AX_FACE = "#1A0033"
CHART_BAR_COLOR = "#580292"
CHART_TEXT_COLOR = "#00FFFF"

TEXT_COLOR = "#00FFFF"

# === Widgets ===
def stylized_button(parent, text, command, **kwargs):
    import tkinter as tk
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=BTN_BG,
        fg=BTN_FG,
        font=FONT,
        activebackground=BTN_BG,
        activeforeground=BTN_FG,
        relief="flat",
        bd=1,
        highlightbackground=BORDER_COLOR,
        highlightthickness=1,
        cursor="hand2",
        **kwargs
    )
