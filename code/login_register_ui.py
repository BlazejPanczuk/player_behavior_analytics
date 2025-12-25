import tkinter as tk
from tkinter import messagebox
import os
import sys
import mysql.connector
from start_ui_styles import (
    BTN_BG, BTN_FG, BUTTON_FONT, COLOR_RIGHT, TEXT_COLOR,
    stylized_entry, stylized_button, stylized_label
)

# === BAZA ===
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="gamedb"
    )

# === ROOT ===
root = tk.Tk()
root.title("Start")
root.configure(bg=COLOR_RIGHT)
root.resizable(False, False)

def center_window(width, height):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))
    root.geometry(f"{width}x{height}+{x}+{y}")

# startowy rozmiar
center_window(600, 200)

def show_main_menu():
    root.destroy()
    os.system(f"{sys.executable} analiza.py")

def toggle_form(form_type):
    for widget in form_frame.winfo_children():
        widget.destroy()

    # Oblicz wysokość na podstawie liczby pól
    fields = 2 if form_type == "login" else 5
    entry_height = 70
    base_height = 300
    total_height = base_height + fields * entry_height
    center_window(600, total_height)

    entries = {}

    def add_field(label_text, key, is_password=False):
        stylized_label(form_frame, label_text).pack(pady=5)
        ent = stylized_entry(form_frame)
        if is_password:
            ent.config(show="*")
        ent.pack(pady=2)
        entries[key] = ent

    if form_type == "login":
        add_field("Login", "login")
        add_field("Hasło", "password", is_password=True)
    else:
        add_field("Email", "email")
        add_field("Login", "login")
        add_field("Hasło", "password", is_password=True)
        add_field("Telefon (9 cyfr)", "phone")
        add_field("Wiek", "age")

    def submit():
        data = {k: v.get().strip() for k, v in entries.items()}

        if not all(data.values()):
            messagebox.showwarning("Uwaga", "Wypełnij wszystkie pola.")
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            if form_type == "login":
                cursor.execute("SELECT * FROM user WHERE login = %s AND password = %s", (data["login"], data["password"]))
                user = cursor.fetchone()
                if user:
                    show_main_menu(data["login"])
                else:
                    messagebox.showerror("Błąd", "Nieprawidłowy login lub hasło.")
            else:
                cursor.execute("SELECT * FROM user WHERE login = %s", (data["login"],))
                if cursor.fetchone():
                    messagebox.showwarning("Uwaga", "Taki login już istnieje.")
                    return

                cursor.execute("""
                    INSERT INTO user (email, login, password, phone, age)
                    VALUES (%s, %s, %s, %s, %s)
                """, (data["email"], data["login"], data["password"], data["phone"], int(data["age"])))
                conn.commit()
                messagebox.showinfo("Sukces", "Rejestracja zakończona!")
                toggle_form("login")

        except Exception as e:
            messagebox.showerror("Błąd bazy danych", str(e))
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    stylized_button(form_frame, "Wyślij", submit).pack(pady=20)

def show_main_menu(login):
    root.withdraw()  # ukryj główne okno

    menu_win = tk.Toplevel()
    menu_win.title("Start")
    menu_win.configure(bg=COLOR_RIGHT)
    menu_win.resizable(False, False)
    menu_win.protocol("WM_DELETE_WINDOW", sys.exit)  # zamknięcie = wyjście z aplikacji

    def center_menu_window(width, height):
        screen_width = menu_win.winfo_screenwidth()
        screen_height = menu_win.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        menu_win.geometry(f"{width}x{height}+{x}+{y}")

    center_menu_window(600, 300)

    # Nagłówek powitalny
    label = stylized_label(menu_win, f"Salve {login}, co dziś będziemy robić?")
    label.config(font=("Arial Black", 20), fg="#00ffff")  # neonowy niebieski
    label.pack(pady=40)

    # Ramka na przyciski
    menu_btn_frame = tk.Frame(menu_win, bg=COLOR_RIGHT)
    menu_btn_frame.pack(pady=10)

    def launch_analysis():
        menu_win.destroy()
        os.system(f"{sys.executable} game_data_analysis_ui.py")
        
    def launch_skelp():
        menu_win.destroy()
        os.system(f"{sys.executable} shop_interface.py {login}")

    stylized_button(menu_btn_frame, "Analiza", launch_analysis).pack(side=tk.LEFT, padx=20)
    stylized_button(menu_btn_frame, "Sklep", launch_skelp).pack(side=tk.LEFT, padx=20)

# === INTERFEJS ===
button_frame = tk.Frame(root, bg=COLOR_RIGHT)
button_frame.pack(pady=30)

stylized_button(button_frame, "Login", lambda: toggle_form("login")).pack(side=tk.LEFT, padx=20)
stylized_button(button_frame, "Rejestracja", lambda: toggle_form("register")).pack(side=tk.LEFT, padx=20)

form_frame = tk.Frame(root, bg=COLOR_RIGHT)
form_frame.pack()

root.mainloop()
