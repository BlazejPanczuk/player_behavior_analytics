# === Standard library ===
import os
import sys
import subprocess
# === Third-party ===
import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# === Tkinter ===
import tkinter as tk
from tkinter import ttk
# === Project styles & utils ===
from analysis_ui_styles import (
    COLOR_LEFT, COLOR_RIGHT, COLOR_BOTTOM, BORDER_COLOR, BORDER_WIDTH,
    FONT, HEADER_FONT, LISTBOX_BG, LISTBOX_FG, LISTBOX_SELECT_BG, LISTBOX_SELECT_FG,
    CHART_FACE, CHART_AX_FACE, CHART_BAR_COLOR, CHART_TEXT_COLOR, TEXT_COLOR, BTN_BG, BTN_FG
)
from itertools import cycle
from database_connection import with_db_connection
from ai_local_integration import interpret_with_local_ai
from ai_data_analysis import interpretuj_ai_z_kategorii
# === Database (shared utility) ===
from database_connection import with_db_connection
# === Styles (import helpers) ===
from analysis_ui_styles import stylized_button
#=== Bridge to Ai analize ===
from chart_ai_bridge import (ChartSnapshot,register_chart_snapshot,analyze_latest_chart_async, append_log, )
# === Logging ===
def _post_to_log(widget, message: str) -> None:
    if not widget:
        return

    # Jeśli to Frame, spróbuj znaleźć w nim Text
    if isinstance(widget, tk.Frame):
        for child in widget.winfo_children():
            if isinstance(child, tk.Text):
                widget = child
                break
        else:
            # brak Text → stwórz nowy
            txt = tk.Text(widget, wrap="word", bg="#121222", fg="white",
                          font=("Consolas", 10), borderwidth=0)
            txt.pack(fill="both", expand=True)
            widget = txt

    # Jeśli to już Text → wpisz log
    if isinstance(widget, tk.Text):
        try:
            widget.after(0, lambda: (
                widget.insert("end", f"{message}\n"),
                widget.see("end")
            ))
        except Exception:
            pass
    else:
        # fallback: spróbuj ustawić text= (np. Label)
        try:
            prev = widget.cget("text")
            widget.config(text=(prev + ("\n" if prev else "") + message))
        except Exception:
            pass
# === Queries: basic lists ==
def get_game_titles() -> list[str]:
    try:
        with with_db_connection() as (conn, cursor):
            cursor.execute("SELECT name FROM game ORDER BY name ASC;")
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        return [f"Błąd: {e}"]

def get_user_logins() -> list[str]:
    try:
        with with_db_connection() as (conn, cursor):
            cursor.execute("SELECT login FROM user ORDER BY login ASC;")
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        return [f"Błąd: {e}"]
# === Queries: user details ===
def get_user_details(login: str) -> dict:
    try:
        with with_db_connection(dictionary=True) as (conn, cursor):
            cursor.execute(
                """
                SELECT u.id_user, u.login, u.email, u.age, u.phone
                FROM user u
                WHERE u.login = %s
                """,
                (login,),
            )
            user = cursor.fetchone()
            if not user:
                return {"Błąd": "Nie znaleziono użytkownika"}

            user_id = user["id_user"]

            cursor.execute(
                """
                SELECT
                    g.name,
                    l.play_time,
                    l.purchase_date,
                    l.items_owned,
                    l.achievements,
                    l.achievement_progress,
                    (
                        SELECT a.time
                        FROM game_activity ga
                        JOIN activity a ON a.id_activity = ga.id_activity
                        WHERE ga.id_game = g.id_game AND a.id_user = %s
                        ORDER BY a.time DESC
                        LIMIT 1
                    ) AS last_session,
                    (
                        SELECT a.game_time
                        FROM game_activity ga
                        JOIN activity a ON a.id_activity = ga.id_activity
                        WHERE ga.id_game = g.id_game AND a.id_user = %s
                        ORDER BY a.time DESC
                        LIMIT 1
                    ) AS last_session_length
                FROM library l
                JOIN game g ON g.id_game = l.id_game
                WHERE l.id_user = %s
                """,
                (user_id, user_id, user_id),
            )

            user["games"] = cursor.fetchall()
            return user
    except Exception as e:
        return {"Błąd": str(e)}

# === Queries: game info ===
def get_game_info(game_title: str) -> dict:
    try:
        with with_db_connection(dictionary=True) as (conn, cursor):
            cursor.execute(
                """
                SELECT
                    g.name AS NazwaGry,
                    g.price AS CenaPLN,
                    g.positive_rating AS PozytywneOceny,
                    g.negative_rating AS NegatywneOceny,
                    g.release_date AS DataWydania,
                    g.mods AS IloscModow,
                    g.copies_sold AS LiczbaKopiiSprzedanych,
                    g.peak_players AS RekordWszechczasów,
                    g.current_players AS GraczyTeraz,
                    g.peak_24h_players AS Szczyt24h,
                    g.creator AS Tworca,
                    GROUP_CONCAT(DISTINCT IF(gl.has_interface = 1, l.name, NULL) SEPARATOR ', ') AS JezykiInterfejsu,
                    GROUP_CONCAT(DISTINCT IF(gl.has_subtitles = 1, l.name, NULL) SEPARATOR ', ') AS JezykiZNapisy,
                    GROUP_CONCAT(DISTINCT IF(gl.has_dubbing = 1, l.name, NULL) SEPARATOR ', ') AS JezykiZDubbingiem,
                    (SELECT COUNT(*) FROM game_dlc gd2 WHERE gd2.id_game = g.id_game) AS LiczbaDLC,
                    GROUP_CONCAT(DISTINCT d.name SEPARATOR ', ') AS NazwyDLC,
                    GROUP_CONCAT(DISTINCT ge.name SEPARATOR ', ') AS Gatunki,
                    GROUP_CONCAT(DISTINCT p.name SEPARATOR ', ') AS Platformy
                FROM game g
                LEFT JOIN game_language gl ON gl.id_game = g.id_game
                LEFT JOIN language l ON l.id_language = gl.id_language
                LEFT JOIN game_dlc gd ON gd.id_game = g.id_game
                LEFT JOIN dlc d ON d.id_dlc = gd.id_dlc
                LEFT JOIN game_genre gg ON gg.id_game = g.id_game
                LEFT JOIN genre ge ON ge.id_genre = gg.id_genre
                LEFT JOIN game_platform gp ON gp.id_game = g.id_game
                LEFT JOIN platform p ON p.id_platform = gp.id_platform
                WHERE g.name = %s
                GROUP BY g.id_game
                """,
                (game_title,),
            )
            return cursor.fetchone()
    except Exception as e:
        return {"Błąd": str(e)}

# === SteamCharts: fetch current / 24h peak / all-time peak ===
def fetch_steamcharts_data(appid: int, timeout: float = 10.0):
    import re
    from bs4 import BeautifulSoup
    import requests

    def parse_int(txt: str):
        txt = re.sub(r"[^\d]", "", txt or "")
        return int(txt) if txt else None

    try:
        url = f"https://steamcharts.com/app/{appid}"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "close",
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        stats = soup.find_all("div", class_="app-stat")
        if not stats:
            return None, None, None

        current = peak24 = alltime = None

        # mapowanie po etykietach (bardziej odporne niż zakładanie kolejności)
        for box in stats:
            num = box.find("span", class_="num")
            label = box.get_text(" ", strip=True).lower()
            value = parse_int(num.get_text(strip=True) if num else "")

            if "right now" in label or "graczy teraz" in label:
                current = value
            elif "24-hour peak" in label or "24 godz." in label:
                peak24 = value
            elif "all-time peak" in label or "rekord wszechczasów" in label:
                alltime = value

        # fallback: kolejność 0/1/2 jak w klasycznym layoutcie
        if any(v is None for v in (current, peak24, alltime)) and len(stats) >= 3:
            try:
                current = current or parse_int(stats[0].find("span", class_="num").get_text(strip=True))
                peak24  = peak24  or parse_int(stats[1].find("span", class_="num").get_text(strip=True))
                alltime = alltime or parse_int(stats[2].find("span", class_="num").get_text(strip=True))
            except Exception:
                pass

        return current, peak24, alltime

    except Exception:
        return None, None, None
# === DB update: SteamCharts stats ===
def update_steamcharts_data(
    appid: int,
    current: int | None,
    peak_24h: int | None,
    peak_all: int | None
) -> bool:
    try:
        with with_db_connection() as (conn, cursor):
            cursor.execute(
                """
                UPDATE game
                SET current_players = %s,
                    peak_24h_players = %s,
                    peak_players = %s
                WHERE steam_appid = %s
                """,
                (current, peak_24h, peak_all, appid),
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception:
        return False
# === UI helpers ===
def _set_info_text(widget, text: str) -> None:
    if not widget:
        return
    try:
        widget.after(0, lambda: widget.config(text=text))
    except Exception:
        pass
# === SteamCharts: refresh all games ===
def refresh_all_games(info_target=None, log_target=None) -> int:
    updated_count = 0
    try:
        _set_info_text(info_target, "Pobieranie danych...")
        _post_to_log(log_target, "Rozpoczynam pobieranie danych ze SteamCharts...")

        with with_db_connection(dictionary=True) as (conn, cursor):
            cursor.execute("SELECT steam_appid, name FROM game WHERE steam_appid IS NOT NULL")
            games = cursor.fetchall()

        for game in games:
            appid = game["steam_appid"]
            current, peak_24h, peak_all = fetch_steamcharts_data(appid)

            if current is not None:
                ok = update_steamcharts_data(appid, current, peak_24h, peak_all)
                if ok:
                    updated_count += 1
                _post_to_log(
                    log_target,
                    f"  • {game['name']}: {current} teraz, {peak_24h} / 24h, rekord {peak_all}"
                )
            else:
                _post_to_log(log_target, f"  • {game['name']}: brak danych")

        _set_info_text(info_target, f"Zaktualizowano {updated_count} gier.")
        if info_target:
            try:
                info_target.after(5000, lambda: _set_info_text(info_target, ""))
            except Exception:
                pass

        _post_to_log(log_target, f"Zaktualizowano {updated_count} gier.\n")
        return updated_count

    except Exception as e:
        _set_info_text(info_target, f"Błąd: {e}")
        _post_to_log(log_target, f"Błąd przy odświeżaniu danych: {e}")
        return updated_count
# === Async wrapper (nie blokuje GUI) ===
def refresh_all_games_async(info_target=None, log_target=None) -> None:
    import threading
    threading.Thread(
        target=lambda: refresh_all_games(info_target, log_target),
        daemon=True
    ).start()

def generate_playtime_chart(parent_frame, log_box):
    try:
        with with_db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT g.name, SUM(l.play_time)/60 AS total_hours
                FROM library l
                JOIN game g ON g.id_game = l.id_game
                GROUP BY g.name
                ORDER BY total_hours DESC
            """)
            data = cursor.fetchall()

        if not data:
            return

        all_titles = [row[0] for row in data]
        hours_dict = {row[0]: row[1] for row in data}

        for widget in parent_frame.winfo_children():
            widget.destroy()

        # === LEWA STRONA: lista gier ===
        listbox_frame = tk.Frame(parent_frame, bg=COLOR_LEFT, bd=BORDER_WIDTH, highlightbackground=BORDER_COLOR, highlightthickness=1)
        listbox_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        label = tk.Label(
            listbox_frame, text="Wybierz gry", font=HEADER_FONT,
            bg=COLOR_LEFT, fg=CHART_TEXT_COLOR
        )
        label.pack(pady=(0, 5))

        listbox = tk.Listbox(
            listbox_frame, selectmode='multiple', exportselection=False, height=30,
            bg=LISTBOX_BG, fg=LISTBOX_FG,
            selectbackground=LISTBOX_SELECT_BG, selectforeground=LISTBOX_SELECT_FG,
            font=("Consolas", 11),
            bd=0, relief="flat", highlightthickness=0  
            )
        for title in all_titles:
            listbox.insert(tk.END, title)
        listbox.pack(fill=tk.Y)

        # === PRAWA STRONA: wykres + przycisk ===
        chart_frame = tk.Frame(
            parent_frame,
            bg=COLOR_RIGHT,
            width=1000,
            height=850,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            bd=0, relief="flat"
        )
        chart_frame.pack_propagate(False)
        chart_frame.pack(side=tk.LEFT, padx=10, pady=10)


        def draw_chart(selected_titles):
            for widget in chart_frame.winfo_children():
                widget.destroy()

            if not selected_titles:
                return

            selected_hours = [hours_dict[title] for title in selected_titles]
            num_bars = len(selected_titles)

            fig, ax = plt.subplots(figsize=(max(12, num_bars * 0.6), 6))
            fig.patch.set_facecolor(CHART_FACE)
            ax.set_facecolor(CHART_AX_FACE)

            bars = ax.bar(range(num_bars), selected_hours, color=CHART_BAR_COLOR, width=0.5)

            for i, bar in enumerate(bars):
                height = bar.get_height()
                ax.annotate(f'{height:.1f}', (bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3), textcoords="offset points",
                            ha='center', va='bottom', fontsize=9, color=CHART_TEXT_COLOR)

            ax.set_title("Łączny czas spędzony w grach (godziny)", color=CHART_TEXT_COLOR, fontsize=14, pad=20)
            ax.set_ylabel("Czas gry [godziny]", color=CHART_TEXT_COLOR, fontsize=11, labelpad=15)
            ax.tick_params(axis='y', colors=CHART_TEXT_COLOR)
            ax.get_yaxis().set_visible(True)
            ax.set_xticks(range(num_bars))
            ax.set_xticklabels(selected_titles, rotation=45, ha='right', fontsize=9, color=CHART_TEXT_COLOR)

            for spine in ax.spines.values():
                spine.set_color(BORDER_COLOR)

            ax.tick_params(axis='x', colors=CHART_TEXT_COLOR)

            fig.tight_layout(rect=[0, 0.18, 1, 1])
            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            canvas.get_tk_widget().config(borderwidth=0, highlightthickness=0)


            # === ZOOM & PAN ===
            pan_start = {"x": None}

            def on_mouse_scroll(event):
                shift = 1
                cur_xlim = ax.get_xlim()
                width = cur_xlim[1] - cur_xlim[0]
                new_left = cur_xlim[0] - shift if event.step > 0 else cur_xlim[0] + shift
                new_left = max(-0.5, min(new_left, num_bars + 0.5 - width))
                ax.set_xlim(new_left, new_left + width)
                fig.canvas.draw_idle()

            def on_press(event):
                if event.button == 1 and event.inaxes == ax:
                    pan_start["x"] = event.xdata

            def on_release(event):
                pan_start["x"] = None

            def on_motion(event):
                if pan_start["x"] is not None and event.inaxes == ax and event.xdata is not None:
                    dx = pan_start["x"] - event.xdata
                    ax.set_xlim(ax.get_xlim()[0] + dx, ax.get_xlim()[1] + dx)
                    pan_start["x"] = event.xdata
                    fig.canvas.draw_idle()

            fig.canvas.mpl_connect("scroll_event", on_mouse_scroll)
            fig.canvas.mpl_connect("button_press_event", on_press)
            fig.canvas.mpl_connect("button_release_event", on_release)
            fig.canvas.mpl_connect("motion_notify_event", on_motion)

            selected_hours = [hours_dict[title] for title in selected_titles]
            df_chart = pd.DataFrame({
                "Game": selected_titles,
                "Hours": selected_hours
            })

            register_chart_snapshot(ChartSnapshot(
                chart_type="bar",
                title="Łączny czas spędzony w grach (godziny)",
                df=df_chart,
                x_col="Game",
                y_col="Hours",
                series_col=None,
                meta={"tryb wyboru": "lista gier", "liczba pozycji": len(selected_titles)}
            ))

        def on_select_change(event):
            selected_titles = [listbox.get(i) for i in listbox.curselection()]
            draw_chart(selected_titles if selected_titles else all_titles)

        listbox.bind('<<ListboxSelect>>', on_select_change)
        draw_chart(all_titles)

    except Exception as e:
        print(f"Błąd generowania wykresu: {e}")

def generate_achievement_pie_chart(parent_frame, log_target=None):
    def _log(msg: str):
        if log_target is not None:
            append_log(log_target, msg)

    try:
        with with_db_connection(dictionary=True) as (conn, cursor):
            cursor.execute("SELECT name, id_game FROM game ORDER BY name ASC")
            games = cursor.fetchall()

        if not games:
            _log("[Pie] Brak gier do wyświetlenia.")
            return

        game_dict = {g['name']: g['id_game'] for g in games}
        game_titles = list(game_dict.keys())

        for w in parent_frame.winfo_children():
            w.destroy()

        listbox = tk.Listbox(
            parent_frame, selectmode='browse', exportselection=False, height=30,
            bg="#0A0A1A", fg="#FFFFFF", selectbackground="#FF0066",
            selectforeground="#FFFFFF", font=("Consolas", 11)
        )
        for title in game_titles:
            listbox.insert(tk.END, title)
        listbox.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        chart_frame = tk.Frame(parent_frame, bg="#121222")
        chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def draw_chart(selected_game: str):
            for w in chart_frame.winfo_children():
                w.destroy()

            try:
                with with_db_connection(dictionary=True) as (conn, cursor):
                    cursor.execute("""
                        SELECT 
                            l.achievement_progress, 
                            l.achievements, 
                            g.name, 
                            g.id_game
                        FROM library l
                        JOIN game g ON g.id_game = l.id_game
                        WHERE g.name = %s
                    """, (selected_game,))
                    data = cursor.fetchall()
                    if not data:
                        _log(f'[Pie] Brak danych dla gry: "{selected_game}".')
                        return

                    cursor.execute(
                        "SELECT MAX(achievements) AS max_ach FROM library WHERE id_game = %s",
                        (data[0]['id_game'],)
                    )
                    row_max = cursor.fetchone()
                    max_ach = row_max['max_ach'] if row_max and row_max['max_ach'] else 1
            except Exception as e:
                print(f"Błąd SQL: {e}")
                _log(f"[Pie] Błąd SQL: {e}")
                return

            # grupowanie: ilu graczy ma daną liczbę osiągnięć
            grouped = {}
            for r in data:
                count = r['achievements'] or 0
                grouped[count] = grouped.get(count, 0) + 1

            achieved = list(grouped.keys())
            counts = list(grouped.values())
            if not counts:
                _log(f'[Pie] Brak wartości do narysowania dla: "{selected_game}".')
                return

            percentages = [(a / max_ach) * 100 if max_ach else 0 for a in achieved]
            labels = [f"{v:.2f}% ({a}/{max_ach})" for a, v in zip(achieved, percentages)]
            colors = plt.cm.viridis([i / max(1, len(counts)) for i in range(len(counts))])

            # --- RYSOWANIE ---
            fig, ax = plt.subplots(figsize=(6, 6))
            fig.patch.set_facecolor("#121222")
            ax.set_facecolor("#1A0033")

            def make_autopct(sizes, raw_labels):
                def pct(pct):
                    total = sum(sizes) if sizes else 1
                    count = int(round(pct / 100.0 * total))
                    # używamy kopii raw_labels przy wywołaniu
                    return f"{count} graczy\n{raw_labels.pop(0)}"
                return pct

            ax.pie(
                counts,
                colors=colors,
                autopct=make_autopct(counts, labels.copy()),
                textprops={'color': 'white', 'fontsize': 10}
            )
            ax.set_title(f'Osiągnięcia graczy w grze "{selected_game}" (%)', color='white', fontsize=13)

            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # --- SNAPSHOT: dane dokładnie jak na wykresie ---
            df_pie = pd.DataFrame({
                "Label": labels,
                "PlayersCount": counts,
                "PercentOfMax": percentages
            })
            register_chart_snapshot(ChartSnapshot(
                chart_type="pie",
                title=f'Osiągnięcia graczy – "{selected_game}"',
                df=df_pie,
                x_col="Label",
                y_col="PlayersCount",
                series_col=None,
                meta={"gra": selected_game, "max_achievements": int(max_ach)}
            ))
            _log(f"[Chart] Snapshot: {selected_game} – {len(counts)} sektorów.")

        def on_select_change(_event):
            sel = listbox.curselection()
            if sel:
                draw_chart(listbox.get(sel[0]))

        listbox.bind('<<ListboxSelect>>', on_select_change)

        # opcjonalnie: auto-rysowanie pierwszej gry
        if game_titles:
            listbox.selection_set(0)
            draw_chart(game_titles[0])

    except Exception as e:
        print(f"Błąd generowania wykresu: {e}")
        if log_target is not None:
            append_log(log_target, f"[Pie] Błąd generowania wykresu: {e}")

def generate_genre_achievement_chart(parent_frame, log_target):
    try:
        with with_db_connection(dictionary=True) as (conn, cursor):
            cursor.execute("""
                SELECT DISTINCT ge.id_genre, ge.name
                FROM genre ge
                JOIN game_genre gg ON gg.id_genre = ge.id_genre
                JOIN game g ON g.id_game = gg.id_game
                JOIN library l ON l.id_game = g.id_game
                WHERE l.achievements > 0
                ORDER BY ge.name ASC
            """)
            genres = cursor.fetchall()

        genre_dict = {g['name']: g['id_genre'] for g in genres}
        genre_names = list(genre_dict.keys())

        for widget in parent_frame.winfo_children():
            widget.destroy()

        listbox = tk.Listbox(
            parent_frame,
            selectmode='multiple',
            exportselection=False,
            height=30,
            bg=LISTBOX_BG,
            fg=LISTBOX_FG,
            selectbackground=LISTBOX_SELECT_BG,
            selectforeground=LISTBOX_SELECT_FG,
            font=("Consolas", 11)
        )
        for name in genre_names:
            listbox.insert(tk.END, name)
        listbox.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        chart_frame = tk.Frame(parent_frame, bg=CHART_FACE)
        chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def draw_chart(selected_genres):
            for w in chart_frame.winfo_children():
                w.destroy()
            if not selected_genres:
                return

            try:
                with with_db_connection(dictionary=True) as (conn, cursor):
                    placeholders = ','.join(['%s'] * len(selected_genres))
                    query = f"""
                        SELECT 
                            ge.name AS genre_name,
                            SUM(l.achievements) AS total_achieved,
                            SUM(l.achievements / NULLIF(l.achievement_progress, 0) * 100) AS estimated_possible
                        FROM library l
                        JOIN game g ON g.id_game = l.id_game
                        JOIN game_genre gg ON gg.id_game = g.id_game
                        JOIN genre ge ON ge.id_genre = gg.id_genre
                        WHERE ge.name IN ({placeholders})
                        GROUP BY ge.name
                    """
                    cursor.execute(query, selected_genres)
                    data = cursor.fetchall()
            except Exception as e:
                print(f"Błąd SQL: {e}")
                return

            labels, values = [], []
            for row in data:
                total = row['total_achieved']
                possible = row['estimated_possible']
                if total and possible:
                    percent = round((total / possible) * 100, 2)
                    labels.append(row['genre_name'])
                    values.append(percent)

            if not values:
                return

            # --- RYSOWANIE ---
            custom_colors = ['#ED006C', '#690759', '#001B7E', "#E50008"]
            color_cycle = cycle(custom_colors)
            colors = []
            for i in range(len(values)):
                c = next(color_cycle)
                while i > 0 and c == colors[-1]:
                    c = next(color_cycle)
                colors.append(c)

            fig, ax = plt.subplots(figsize=(7, 7))
            fig.patch.set_facecolor(CHART_FACE)
            ax.set_facecolor(CHART_AX_FACE)

            wedges, _ = ax.pie(values, labels=labels, colors=colors, autopct=None,
                               textprops={'color': CHART_TEXT_COLOR})
            for i, wedge in enumerate(wedges):
                ang = (wedge.theta2 + wedge.theta1) / 2
                x = np.cos(np.deg2rad(ang))
                y = np.sin(np.deg2rad(ang))
                ax.text(x * 0.6, y * 0.6, f"{values[i]}% osiągnięć",
                        ha='center', va='center', fontsize=10, color=CHART_TEXT_COLOR)

            ax.set_title("Zdobyte osiągnięcia wg gatunku (%)", color=CHART_TEXT_COLOR, fontsize=14)
            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # --- SNAPSHOT dla AI (dokładnie to, co na wykresie) ---
            df_pie = pd.DataFrame({
                "Genre": labels,
                "PercentAchieved": values
            })
            register_chart_snapshot(ChartSnapshot(
                chart_type="pie",
                title="Zdobyte osiągnięcia wg gatunku (%)",
                df=df_pie,
                x_col="Genre",
                y_col="PercentAchieved",
                series_col=None,
                meta={"wybrane_gatunki": selected_genres, "liczba_sektorów": len(values)}
            ))
            if log_target:
                append_log(log_target, f"[Chart] Snapshot (gatunki): {len(values)} sektorów z {len(selected_genres)} wybranych.")

        def on_select_change(event=None):
            selected = [listbox.get(i) for i in listbox.curselection()]
            draw_chart(selected if selected else genre_names)

        listbox.bind('<<ListboxSelect>>', on_select_change)
        draw_chart(genre_names)

    except Exception as e:
        print(f"Błąd generowania wykresu osiągnięć wg gatunków: {e}")

def generate_real_currency_items_chart(parent_frame, log_target):
    try:
        with with_db_connection(dictionary=True) as (conn, cursor):
            cursor.execute("""
                SELECT DISTINCT ge.name
                FROM genre ge
                JOIN game_genre gg ON gg.id_genre = ge.id_genre
                JOIN game g ON g.id_game = gg.id_game
                JOIN library l ON l.id_game = g.id_game
                WHERE l.items_owned > 0
                ORDER BY ge.name ASC
            """)
            genres = [row['name'] for row in cursor.fetchall()]

        for w in parent_frame.winfo_children():
            w.destroy()

        listbox = tk.Listbox(
            parent_frame,
            selectmode='multiple',
            exportselection=False,
            height=30,
            bg="#0A0A1A",
            fg="#FFFFFF",
            selectbackground="#4d004d",
            selectforeground="#FFFFFF",
            font=("Consolas", 11)
        )
        for name in genres:
            listbox.insert(tk.END, name)
        listbox.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        chart_frame = tk.Frame(parent_frame, bg="#121222")
        chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def draw_chart(selected_genres):
            for w in chart_frame.winfo_children():
                w.destroy()
            if not selected_genres:
                return

            try:
                with with_db_connection(dictionary=True) as (conn, cursor):
                    placeholders = ','.join(['%s'] * len(selected_genres))
                    query = f"""
                        SELECT ge.name AS genre_name, SUM(l.items_owned) AS total_items
                        FROM library l
                        JOIN game g ON g.id_game = l.id_game
                        JOIN game_genre gg ON gg.id_game = g.id_game
                        JOIN genre ge ON ge.id_genre = gg.id_genre
                        WHERE ge.name IN ({placeholders}) AND l.items_owned > 0
                        GROUP BY ge.name
                        ORDER BY total_items DESC
                    """
                    cursor.execute(query, selected_genres)
                    data = cursor.fetchall()
            except Exception as e:
                print(f"Błąd SQL: {e}")
                return

            if not data:
                return

            labels = [row['genre_name'] for row in data]
            values = [int(row['total_items'] or 0) for row in data]

            # --- RYSOWANIE ---
            fig, ax = plt.subplots(figsize=(max(10, len(labels) * 0.7), 6))
            fig.patch.set_facecolor("#121222")
            ax.set_facecolor("#1A0033")

            bars = ax.bar(labels, values, color="magenta")
            ax.set_title("Przedmioty za prawdziwą walutę wg gatunku", color='white', fontsize=14)
            ax.set_ylabel("Liczba przedmiotów", color='white')
            ax.tick_params(axis='x', labelrotation=45, colors='white')
            ax.tick_params(axis='y', colors='white')
            for spine in ax.spines.values():
                spine.set_color("#FF00AA")

            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{int(height)}', xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3), textcoords="offset points",
                            ha='center', va='bottom', color='white', fontsize=9)
                fig.tight_layout(rect=[0, 0.08, 1, 1])


            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # --- SNAPSHOT dla AI (dokładnie to, co na wykresie) ---
            df_bar = pd.DataFrame({
                "Genre": labels,
                "ItemsOwned": values
            })
            register_chart_snapshot(ChartSnapshot(
                chart_type="bar",
                title="Przedmioty za prawdziwą walutę wg gatunku",
                df=df_bar,
                x_col="Genre",
                y_col="ItemsOwned",
                series_col=None,
                meta={"wybrane_gatunki": selected_genres, "liczba_słupków": len(values)}
            ))
            append_log(log_target, f"[Chart] Snapshot (items by genre): {len(values)} słupków.")

        def on_select_change(event=None):
            selected = [listbox.get(i) for i in listbox.curselection()]
            draw_chart(selected if selected else genres)

        listbox.bind('<<ListboxSelect>>', on_select_change)
        draw_chart(genres)

    except Exception as e:
        print(f"Błąd generowania wykresu przedmiotów za walutę: {e}")
        append_log(log_target, f"[Items] Błąd: {e}")

def generate_items_by_age_chart(parent_frame, log_target):
    try:
        with with_db_connection(dictionary=True) as (conn, cursor):
            cursor.execute("""
                SELECT u.age, SUM(l.items_owned) AS total_items
                FROM user u
                JOIN library l ON u.id_user = l.id_user
                WHERE l.items_owned > 0
                GROUP BY u.age
            """)
            data = cursor.fetchall()

        # wyczyść panel
        for w in parent_frame.winfo_children():
            w.destroy()

        if not data:
            append_log(log_target, "[AgeItems] Brak danych do wyświetlenia.")
            return

        # z góry zdefiniowana kolejność kubełków
        bins_order = ['0-6', '7-10', '11-15', '16-18', '19-25', '26-30', '30+']
        bins = {k: 0 for k in bins_order}

        for row in data:
            age = row['age']
            items = int(row['total_items'] or 0)
            if age is None:
                continue
            if age <= 6:
                bins['0-6'] += items
            elif age <= 10:
                bins['7-10'] += items
            elif age <= 15:
                bins['11-15'] += items
            elif age <= 18:
                bins['16-18'] += items
            elif age <= 25:
                bins['19-25'] += items
            elif age <= 30:
                bins['26-30'] += items
            else:
                bins['30+'] += items

        labels = [k for k in bins_order if bins[k] > 0]
        values = [bins[k] for k in labels]

        if not values:
            append_log(log_target, "[AgeItems] Wszystkie kubełki puste (po filtrze > 0).")
            return

        # --- UI: osobna ramka na wykres ---
        chart_frame = tk.Frame(parent_frame, bg="#121222")
        chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- RYSOWANIE ---
        colors = ['#FF007F', '#FFAA00', '#66FF66', '#0099FF', '#9933FF', '#FF3333', '#33CCCC']
        fig, ax = plt.subplots(figsize=(7, 7))
        fig.patch.set_facecolor("#121222")
        ax.set_facecolor("#1A0033")

        ax.pie(
            values,
            labels=labels,
            colors=colors[:len(values)],
            autopct='%1.1f%%',
            textprops={'color': 'white', 'fontsize': 10}
        )
        ax.set_title("Przedmioty za prawdziwą walutę wg wieku użytkowników", color='white', fontsize=13)

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- SNAPSHOT dla AI (dokładnie to, co na wykresie) ---
        df_pie = pd.DataFrame({
            "AgeBin": labels,
            "ItemsOwned": values
        })
        register_chart_snapshot(ChartSnapshot(
            chart_type="pie",
            title="Przedmioty za prawdziwą walutę wg wieku użytkowników",
            df=df_pie,
            x_col="AgeBin",
            y_col="ItemsOwned",
            series_col=None,
            meta={"liczba_sektorów": len(values)}
        ))
        append_log(log_target, f"[Chart] Snapshot (items by age): {len(values)} sektorów.")

    except Exception as e:
        print(f"Błąd generowania wykresu wg wieku: {e}")
        append_log(log_target, f"[AgeItems] Błąd: {e}")

def generate_purchase_vs_last_session_user_chart(parent_frame, log_target=None):
    try:
        with with_db_connection(dictionary=True) as (conn, cursor):
            cursor.execute("SELECT login FROM user ORDER BY login ASC;")
            users = [row['login'] for row in cursor.fetchall()]

        for widget in parent_frame.winfo_children():
            widget.destroy()

        listbox = tk.Listbox(
            parent_frame,
            selectmode='browse',
            exportselection=False,
            height=30,
            bg="#0A0A1A",
            fg="white",
            selectbackground="#FF0066",
            selectforeground="white",
            font=("Consolas", 11)
        )
        for login in users:
            listbox.insert(tk.END, login)
        listbox.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        chart_frame = tk.Frame(parent_frame, bg="#121222")
        chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def draw_chart(login):
            for widget in chart_frame.winfo_children():
                widget.destroy()

            with with_db_connection(dictionary=True) as (conn, cursor):
                cursor.execute("SELECT id_user FROM user WHERE login = %s", (login,))
                user = cursor.fetchone()
                if not user:
                    return
                user_id = user["id_user"]

                cursor.execute("""
                    SELECT g.name AS game_name, l.purchase_date, a.time AS last_session, a.game_time
                    FROM library l
                    JOIN game g ON g.id_game = l.id_game
                    JOIN game_activity ga ON ga.id_game = g.id_game
                    JOIN activity a ON a.id_activity = ga.id_activity
                    WHERE l.id_user = %s AND a.id_user = %s AND l.purchase_date IS NOT NULL
                    GROUP BY g.name, l.purchase_date, a.time, a.game_time
                    ORDER BY a.time DESC
                """, (user_id, user_id))
                rows = cursor.fetchall()

            if not rows:
                return

            df = pd.DataFrame(rows)
            # — konwersje typów
            df["purchase_date"] = pd.to_datetime(df["purchase_date"], errors="coerce")
            df["last_session"]  = pd.to_datetime(df["last_session"],  errors="coerce")
            df["game_time"]     = pd.to_numeric(df["game_time"], errors="coerce").fillna(0).astype(int)

            # — wykres
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor("#121222")
            ax.set_facecolor("#1A0033")

            scatter = ax.scatter(df["purchase_date"], df["last_session"], color="#00FFFF", alpha=0.6)

            ax.set_title(f"{login} – Zakup vs Ostatnia sesja", color='white', fontsize=14)
            ax.set_xlabel("Data zakupu", color='white')
            ax.set_ylabel("Data ostatniej sesji", color='white')
            ax.tick_params(axis='x', rotation=45, colors='white')
            ax.tick_params(axis='y', colors='white')
            for spine in ax.spines.values():
                spine.set_color("#FF00AA")

            annot = ax.annotate(
                "", xy=(0, 0), xytext=(15, 15), textcoords="offset points",
                bbox=dict(boxstyle="round", fc="w"),
                arrowprops=dict(arrowstyle="->")
            )
            annot.set_visible(False)

            def update_annot(ind):
                i = ind["ind"][0]
                row = df.iloc[i]
                annot.xy = (row["purchase_date"], row["last_session"])
                annot.set_text(
                    f"{row['game_name']}\nZakup: {row['purchase_date'].date() if pd.notna(row['purchase_date']) else '—'}"
                    f"\nSesja: {row['last_session'].date() if pd.notna(row['last_session']) else '—'}"
                    f"\nCzas: {row['game_time']} min"
                )
                annot.set_color("#00FFFF")
                patch = annot.get_bbox_patch()
                patch.set_facecolor("black")
                patch.set_alpha(0.8)
                patch.set_edgecolor("#00FFFF")
                patch.set_linewidth(1)

            def on_hover(event):
                if event.inaxes == ax:
                    cont, ind = scatter.contains(event)
                    if cont:
                        update_annot(ind)
                        w, h = fig.bbox.width, fig.bbox.height
                        offset_x = -150 if event.x > w / 2 else 15
                        offset_y = -40 if event.y > h / 2 else 15
                        annot.set_position((offset_x, offset_y))
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                    elif annot.get_visible():
                        annot.set_visible(False)
                        fig.canvas.draw_idle()

            fig.canvas.mpl_connect("motion_notify_event", on_hover)

            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # === SNAPSHOT -> bridge (bez żadnych dodatkowych okien) ===
            df_snap = pd.DataFrame({
                "game_name":    df["game_name"].astype(str),
                # zapisujemy ISO stringi, żeby LLM nie tłumaczył znaczników daty
                "purchase_date": df["purchase_date"].dt.strftime("%Y-%m-%d %H:%M:%S").fillna(""),
                "last_session":  df["last_session"].dt.strftime("%Y-%m-%d %H:%M:%S").fillna(""),
                "game_time_min": df["game_time"].astype(int)
            })

            register_chart_snapshot(ChartSnapshot(
                chart_type="scatter",
                title=f'{login} – Zakup vs Ostatnia sesja',
                df=df_snap,
                x_col="purchase_date",
                y_col="last_session",
                series_col=None,
                meta={"login": login, "points": int(len(df_snap))}
            ))
            append_log(log_target or parent_frame, f"[Chart] Snapshot: {login} – {len(df_snap)} punktów.")

        def on_select(event):
            selection = listbox.curselection()
            if selection:
                login = listbox.get(selection[0])
                draw_chart(login)

        listbox.bind("<<ListboxSelect>>", on_select)

    except Exception as e:
        print(f"Błąd generowania wykresu użytkownika: {e}")

def generate_steamcharts_activity_chart(parent_frame, appid, game_name="Wybrana gra", log_target=None):
    try:
        url = f"https://steamcharts.com/app/{appid}/chart-data.json"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            data_points = res.json()
        except Exception as e:
            for widget in parent_frame.winfo_children():
                widget.destroy()
            error = tk.Label(parent_frame, text=f"Błąd pobierania danych z API:\n{e}", fg="white", bg="#121222")
            error.pack(pady=20)
            return

        filtered_data = [row for row in data_points if 946684800000 <= row[0] <= 9223372036854775807]
        if not filtered_data:
            raise ValueError("Brak poprawnych danych wykresu.")

        df = pd.DataFrame(filtered_data, columns=["timestamp", "players"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", errors="coerce")
        df = df.dropna()
        df = df[df["timestamp"] < pd.Timestamp.now() + pd.Timedelta(days=1)]
        df = df[df["players"] > 0]

        df["date"] = df["timestamp"].dt.floor("d")  # datetime64
        df_daily = df.groupby("date")["players"].mean().reset_index()

        for widget in parent_frame.winfo_children():
            widget.destroy()

        options = ["7 dni", "30 dni", "90 dni", "365 dni", "Wszystko"]
        days_map = {"7 dni": 7, "30 dni": 30, "90 dni": 90, "365 dni": 365, "Wszystko": None}

        control_frame = tk.Frame(parent_frame, bg="#121222")
        control_frame.pack(fill="x", pady=5)

        selected_range = tk.StringVar(value="30 dni")
        dropdown = ttk.Combobox(control_frame, textvariable=selected_range, values=options, state="readonly", font=("Consolas", 11))
        dropdown.pack(side=tk.LEFT, padx=10)

        chart_frame = tk.Frame(parent_frame, bg="#121222")
        chart_frame.pack(fill="both", expand=True)

        def resample_for_viewport(df_view, max_points=1000):
            if len(df_view) <= max_points:
                return df_view
            step = max(1, len(df_view) // max_points)
            return df_view.iloc[::step]

        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor("#121222")
        ax.set_facecolor("#1A0033")
        line, = ax.plot([], [], color="lime", linewidth=1)

        annot = ax.annotate("", xy=(0, 0), xytext=(15, 15),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="black", ec="lime", lw=1),
            arrowprops=dict(arrowstyle="->", color="lime"))
        annot.set_visible(False)

        ax.set_xlabel("Data", color="white")
        ax.set_ylabel("Gracze (średnia dzienna)", color="white")
        ax.tick_params(colors="white", rotation=45)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.set_ylim(bottom=0)
        ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))
        fig.tight_layout(rect=[0.05, 0.12, 1, 0.90])
        for spine in ax.spines.values():
            spine.set_color("#FF00AA")

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        

        def on_hover(event):
            if event.inaxes == ax and event.xdata is not None:
                x_vals = visible_points["x"]; y_vals = visible_points["y"]
                if len(x_vals) == 0:
                    return
                idx = np.argmin(np.abs(x_vals - event.xdata))
                x = x_vals[idx]; y = y_vals[idx]
                annot.xy = (x, y)
                annot.set_text(f"Data: {mdates.num2date(x).strftime('%Y-%m-%d')}\nGraczy: {int(y):,}")
                annot.set_color("#00FFFF")
                annot.set_visible(True)
                fig.canvas.draw_idle()
            else:
                if annot.get_visible():
                    annot.set_visible(False)
                    fig.canvas.draw_idle()

        def update_plot_data(xlim=None):
            range_label = selected_range.get()
            days = days_map[range_label]
            df_filtered = df_daily.copy()

            if xlim:
                left = np.datetime64(pd.to_datetime(mdates.num2date(xlim[0])).normalize())
                right = np.datetime64(pd.to_datetime(mdates.num2date(xlim[1])).normalize())
                df_filtered = df_filtered[(df_filtered["date"] >= left) & (df_filtered["date"] <= right)]
            elif days:
                min_date = pd.Timestamp.now().normalize() - pd.Timedelta(days=days)
                df_filtered = df_filtered[df_filtered["date"] >= min_date]

            df_filtered = df_filtered.sort_values("date")
            df_filtered = resample_for_viewport(df_filtered)

            if df_filtered.empty:
                line.set_data([], [])
                ax.set_title("Brak danych", color="white")
                fig.canvas.draw_idle()
                return

            x = df_filtered["date"]
            y = pd.to_numeric(df_filtered["players"], errors='coerce').fillna(0)

            line.set_data(mdates.date2num(x), y)
            visible_points["x"] = mdates.date2num(x)
            visible_points["y"] = y
            ax.xaxis_date()
            ax.set_xlim(mdates.date2num(x.min()), mdates.date2num(x.max()))
            ax.set_ylim(y.min() * 0.95, y.max() * 1.05)
            ax.grid(True, color="#333333", linestyle="--", alpha=0.5)
            ax.set_title(f"{game_name} – Średnia dzienna liczba graczy ({range_label})", color="white")
            fig.canvas.draw_idle()

            # === TU: rejestrujemy SNAPSHOT dla przycisku z main ===
            df_snap = pd.DataFrame({
                "Date": pd.to_datetime(df_filtered["date"]).dt.strftime("%Y-%m-%d"),
                "Players": pd.to_numeric(df_filtered["players"], errors="coerce").fillna(0).astype(int)
            })
            register_chart_snapshot(ChartSnapshot(
                chart_type="line",
                title=f'Aktywność – {game_name} ({range_label})',
                df=df_snap,
                x_col="Date",
                y_col="Players",
                series_col=None,
                meta={"appid": int(appid), "game": game_name, "range": range_label, "points": int(len(df_snap))}
            ))
            if log_target is not None:
                append_log(log_target, f"[Chart] Snapshot: {game_name} – {range_label} – {len(df_snap)} punktów.")

            update_visible_data(df_daily)

        pan_start = {"x": None, "y": None}

        def update_visible_data(df):
            xlim = ax.get_xlim()
            left = np.datetime64(pd.to_datetime(mdates.num2date(xlim[0])).normalize())
            right = np.datetime64(pd.to_datetime(mdates.num2date(xlim[1])).normalize())

            visible_df = df[(df["date"] >= left) & (df["date"] <= right)].copy()
            if visible_df.empty:
                line.set_data([], [])
                fig.canvas.draw_idle()
                return

            visible_df = resample_for_viewport(visible_df, max_points=500)
            x = visible_df["date"]; y = visible_df["players"]

            line.set_data(mdates.date2num(x), y)
            visible_points["x"] = mdates.date2num(x)
            visible_points["y"] = y

            if pd.notnull(y.min()) and pd.notnull(y.max()) and y.max() > y.min():
                y_min = y.min(); y_max = y.max()
                center = (y_max + y_min) / 2
                margin = (y_max - y_min) * 0.6
                ax.set_ylim(center - margin, center + margin)

            fig.canvas.draw_idle()

        def on_scroll(event):
            base_scale = 1.2
            if event.inaxes != ax:
                return
            cur_xlim = ax.get_xlim(); cur_ylim = ax.get_ylim()
            xdata = event.xdata; ydata = event.ydata
            scale_factor = 1 / base_scale if event.step > 0 else base_scale
            new_xlim = [xdata - (xdata - cur_xlim[0]) * scale_factor,
                        xdata + (cur_xlim[1] - xdata) * scale_factor]
            new_ylim = [ydata - (ydata - cur_ylim[0]) * scale_factor,
                        ydata + (cur_ylim[1] - ydata) * scale_factor]
            ax.set_xlim(new_xlim); ax.set_ylim(new_ylim)
            update_visible_data(df_daily)

        visible_points = {"x": [], "y": []}
        pan_start = {"x": None, "y": None}

        def on_press(event):
            if event.button == 1 and event.inaxes == ax:
                pan_start["x"], pan_start["y"] = event.xdata, event.ydata

        def on_release(event):
            pan_start["x"], pan_start["y"] = None, None

        def on_motion(event):
            if pan_start["x"] is not None and event.inaxes == ax and event.xdata is not None and event.ydata is not None:
                dx = pan_start["x"] - event.xdata
                dy = pan_start["y"] - event.ydata
                ax.set_xlim(ax.get_xlim()[0] + dx, ax.get_xlim()[1] + dx)
                ax.set_ylim(ax.get_ylim()[0] + dy, ax.get_ylim()[1] + dy)
                pan_start["x"], pan_start["y"] = event.xdata, event.ydata
                update_visible_data(df_daily)

        fig.canvas.mpl_connect("button_press_event", on_press)
        fig.canvas.mpl_connect("button_release_event", on_release)
        fig.canvas.mpl_connect("motion_notify_event", on_motion)
        fig.canvas.mpl_connect("scroll_event", on_scroll)
        fig.canvas.mpl_connect("motion_notify_event", on_hover)

        dropdown.bind("<<ComboboxSelected>>", lambda e: update_plot_data())
        update_plot_data()

    except Exception as e:
        for widget in parent_frame.winfo_children():
            widget.destroy()
        error = tk.Label(parent_frame, text=f"Błąd pobierania wykresu:\n{e}", fg="white", bg="#121222")
        error.pack(pady=20)

def show_steamcharts_selection(parent_frame):
    try:
        with with_db_connection(dictionary=True) as (conn, cursor):
            cursor.execute("""
                SELECT name, steam_appid FROM game 
                WHERE steam_appid IS NOT NULL 
                ORDER BY name
            """)
            games = cursor.fetchall()
    except Exception as e:
        for widget in parent_frame.winfo_children():
            widget.destroy()
        error = tk.Label(parent_frame, text=f"Błąd bazy danych:\n{e}", fg="white", bg="#121222")
        error.pack(pady=20)
        return

    for widget in parent_frame.winfo_children():
        widget.destroy()

    game_dict = {g["name"]: g["steam_appid"] for g in games}

    listbox = tk.Listbox(parent_frame, selectmode="browse", bg="#0A0A1A", fg="white", font=("Consolas", 11))
    for name in game_dict:
        listbox.insert(tk.END, name)
    listbox.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

    def on_select(event):
        index = listbox.curselection()
        if index:
            selected_name = listbox.get(index[0])
            appid = game_dict[selected_name]
            generate_steamcharts_activity_chart(parent_frame, appid, selected_name)

    listbox.bind("<<ListboxSelect>>", on_select)

def generate_mods_chart(parent_frame, log_target=None):
    try:
        with with_db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT name, mods
                FROM game
                WHERE mods IS NOT NULL
                ORDER BY mods DESC
            """)
            data = cursor.fetchall()

        if not data:
            return

        all_titles = [row[0] for row in data]
        mods_dict  = {row[0]: int(row[1] or 0) for row in data}

        for widget in parent_frame.winfo_children():
            widget.destroy()

        listbox = tk.Listbox(
            parent_frame,
            selectmode='multiple',
            exportselection=False,
            height=30,
            bg=LISTBOX_BG,
            fg=LISTBOX_FG,
            selectbackground=LISTBOX_SELECT_BG,
            selectforeground=LISTBOX_SELECT_FG,
            font=("Consolas", 11)
        )
        for title in all_titles:
            listbox.insert(tk.END, title)
        listbox.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        chart_frame = tk.Frame(parent_frame, bg=CHART_FACE)
        chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def draw_chart(selected_titles):
            for w in chart_frame.winfo_children():
                w.destroy()

            if not selected_titles:
                return

            selected_mods = [mods_dict[t] for t in selected_titles]
            num_bars = len(selected_titles)

            fig, ax = plt.subplots(
            figsize=(max(10, num_bars * 0.55), 6),
            constrained_layout=True
            )
            fig.patch.set_facecolor(CHART_FACE)
            ax.set_facecolor(CHART_AX_FACE)

            bars = ax.bar(range(num_bars), selected_mods, color=CHART_BAR_COLOR)

            for bar in bars:
                h = bar.get_height()
                ax.annotate(f'{int(h)}',
                            xy=(bar.get_x() + bar.get_width() / 2, h),
                            xytext=(0, 3), textcoords="offset points",
                            ha='center', va='bottom', fontsize=9, color='white')

            ax.set_title("Liczba modów do gier", color='magenta', fontsize=14, pad=20)
            ax.set_ylabel("Ilość modów", color='white')
            ax.set_xticks(range(num_bars))
            ax.set_xticklabels(selected_titles, rotation=45, ha='right', fontsize=9, color='white')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            for spine in ax.spines.values():
                spine.set_color(BORDER_COLOR)


            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # --- Pan/Scroll ---
            pan_start = {"x": None}

            def on_mouse_scroll(event):
                shift = 1
                left, right = ax.get_xlim()
                width = right - left
                new_left = left + shift if event.step < 0 else left - shift
                new_left = max(-0.5, min(new_left, num_bars + 0.5 - width))
                ax.set_xlim(new_left, new_left + width)
                fig.canvas.draw_idle()

            def on_press(event):
                if event.button == 1 and event.inaxes == ax:
                    pan_start["x"] = event.xdata

            def on_release(event):
                pan_start["x"] = None

            def on_motion(event):
                if pan_start["x"] is not None and event.inaxes == ax and event.xdata:
                    dx = pan_start["x"] - event.xdata
                    ax.set_xlim(ax.get_xlim()[0] + dx, ax.get_xlim()[1] + dx)
                    pan_start["x"] = event.xdata
                    fig.canvas.draw_idle()

            fig.canvas.mpl_connect("scroll_event", on_mouse_scroll)
            fig.canvas.mpl_connect("button_press_event", on_press)
            fig.canvas.mpl_connect("button_release_event", on_release)
            fig.canvas.mpl_connect("motion_notify_event", on_motion)

            # --- SNAPSHOT dla AI (dokładnie to, co na wykresie) ---
            df_bar = pd.DataFrame({
                "Game": selected_titles,
                "Mods": selected_mods
            })
            register_chart_snapshot(ChartSnapshot(
                chart_type="bar",
                title="Liczba modów do gier",
                df=df_bar,
                x_col="Game",
                y_col="Mods",
                series_col=None,
                meta={"liczba_słupków": len(selected_titles)}
            ))
            if log_target is not None:
                append_log(log_target, f"[Chart] Snapshot (mods): {len(selected_titles)} słupków.")

        def on_select_change(_event):
            selected = [listbox.get(i) for i in listbox.curselection()]
            draw_chart(selected if selected else all_titles)

        listbox.bind('<<ListboxSelect>>', on_select_change)
        draw_chart(all_titles)

    except Exception as e:
        print(f"Błąd generowania wykresu modów: {e}")
        if log_target is not None:
            append_log(log_target, f"[ModsChart] Błąd: {e}")

def generate_mods_by_genre_chart(parent_frame, log_target=None):
    try:
        with with_db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT ge.name AS genre_name, SUM(g.mods) AS total_mods
                FROM game g
                JOIN game_genre gg ON gg.id_game = g.id_game
                JOIN genre ge ON ge.id_genre = gg.id_genre
                WHERE g.mods IS NOT NULL
                GROUP BY ge.name
                ORDER BY total_mods DESC
            """)
            data = cursor.fetchall()

        if not data:
            return

        all_genres = [row[0] for row in data]
        mods_dict = {row[0]: int(row[1] or 0) for row in data}

        for w in parent_frame.winfo_children():
            w.destroy()

        listbox = tk.Listbox(
            parent_frame,
            selectmode='multiple',
            exportselection=False,
            height=30,
            bg=LISTBOX_BG,
            fg=LISTBOX_FG,
            selectbackground=LISTBOX_SELECT_BG,
            selectforeground=LISTBOX_SELECT_FG,
            font=("Consolas", 11)
        )
        for genre in all_genres:
            listbox.insert(tk.END, genre)
        listbox.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        chart_frame = tk.Frame(parent_frame, bg=CHART_FACE)
        chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def draw_chart(selected_genres):
            for w in chart_frame.winfo_children():
                w.destroy()
            if not selected_genres:
                return

            selected_mods = [mods_dict[g] for g in selected_genres]
            num_bars = len(selected_genres)

            fig, ax = plt.subplots(
            figsize=(max(10, num_bars * 0.55), 6),
            constrained_layout=True
            )
            fig.patch.set_facecolor(CHART_FACE)
            ax.set_facecolor(CHART_AX_FACE)

            bars = ax.bar(range(num_bars), selected_mods, color=CHART_BAR_COLOR)

            for i, bar in enumerate(bars):
                h = bar.get_height()
                ax.annotate(f'{int(h)}',
                            xy=(bar.get_x() + bar.get_width() / 2, h),
                            xytext=(0, 3), textcoords="offset points",
                            ha='center', va='bottom',
                            fontsize=9, color='white')

            ax.set_title("Liczba modów wg gatunku", color='magenta', fontsize=14, pad=20, loc='left')
            ax.set_ylabel("Ilość modów", color='white')
            ax.set_xticks(range(num_bars))
            ax.set_xticklabels(selected_genres, rotation=45, ha='right', fontsize=9, color='white')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            for spine in ax.spines.values():
                spine.set_color(BORDER_COLOR)


            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # --- Pan / Scroll (jak było) ---
            pan_start = {"x": None}

            def on_mouse_scroll(event):
                shift = 1
                left, right = ax.get_xlim()
                width = right - left
                new_left = left + shift if event.step < 0 else left - shift
                new_left = max(-0.5, min(new_left, num_bars + 0.5 - width))
                ax.set_xlim(new_left, new_left + width)
                fig.canvas.draw_idle()

            def on_press(event):
                if event.button == 1 and event.inaxes == ax:
                    pan_start["x"] = event.xdata

            def on_release(event):
                pan_start["x"] = None

            def on_motion(event):
                if pan_start["x"] is not None and event.inaxes == ax and event.xdata:
                    dx = pan_start["x"] - event.xdata
                    ax.set_xlim(ax.get_xlim()[0] + dx, ax.get_xlim()[1] + dx)
                    pan_start["x"] = event.xdata
                    fig.canvas.draw_idle()

            fig.canvas.mpl_connect("scroll_event", on_mouse_scroll)
            fig.canvas.mpl_connect("button_press_event", on_press)
            fig.canvas.mpl_connect("button_release_event", on_release)
            fig.canvas.mpl_connect("motion_notify_event", on_motion)

            # --- SNAPSHOT dla AI (dokładnie to, co na wykresie) ---
            df_bar = pd.DataFrame({
                "Genre": selected_genres,
                "Mods": selected_mods
            })
            register_chart_snapshot(ChartSnapshot(
                chart_type="bar",
                title="Liczba modów wg gatunku",
                df=df_bar,
                x_col="Genre",
                y_col="Mods",
                series_col=None,
                meta={"liczba_słupków": len(selected_genres)}
            ))
            if log_target is not None:
                append_log(log_target, f"[Chart] Snapshot (mods by genre): {len(selected_genres)} słupków.")

        def on_select_change(_event):
            selected = [listbox.get(i) for i in listbox.curselection()]
            draw_chart(selected if selected else all_genres)

        listbox.bind('<<ListboxSelect>>', on_select_change)
        draw_chart(all_genres)

    except Exception as e:
        print(f"Błąd generowania wykresu modów wg gatunku: {e}")
        if log_target is not None:
            append_log(log_target, f"[ModsByGenre] Błąd: {e}")

def generate_playtime_vs_achievements_chart(parent_frame, log_box):
    try:
        with with_db_connection(dictionary=True) as (conn, cursor):
            cursor.execute("""
                SELECT g.name AS game_name, g.id_game
                FROM game g
                ORDER BY g.name ASC
            """)
            games = cursor.fetchall()

        if not games:
            return

        game_dict = {g['game_name']: g['id_game'] for g in games}
        game_titles = list(game_dict.keys())

        # wyczyść panel
        for w in parent_frame.winfo_children():
            w.destroy()

        # lista gier
        listbox = tk.Listbox(
            parent_frame,
            selectmode='browse',
            exportselection=False,
            height=30,
            bg=LISTBOX_BG,
            fg=LISTBOX_FG,
            selectbackground=LISTBOX_SELECT_BG,
            selectforeground=LISTBOX_SELECT_FG,
            font=("Consolas", 11)
        )
        for title in game_titles:
            listbox.insert(tk.END, title)
        listbox.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # ramka na wykres
        chart_frame = tk.Frame(parent_frame, bg=CHART_FACE)
        chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def draw_chart(game_name):
            for w in chart_frame.winfo_children():
                w.destroy()

            id_game = game_dict[game_name]

            with with_db_connection(dictionary=True) as (conn, cursor):
                cursor.execute("""
                    SELECT play_time/60 AS hours_played, achievements, achievement_progress
                    FROM library
                    WHERE id_game = %s AND play_time > 0 AND achievements > 0
                """, (id_game,))
                data = cursor.fetchall()

            if not data:
                append_log(log_box, f"[Chart] Brak danych dla gry: {game_name}.")
                return

            # dane do wykresu
            x = np.array([row['hours_played'] for row in data])              # godziny gry
            y = np.array([row['achievement_progress'] for row in data])      # % osiągnięć
            ach = np.array([row['achievements'] for row in data])            # liczba osiągnięć

            labels = [
                f"{row['hours_played']:.1f}h\n{row['achievements']} osią.\n{row['achievement_progress']}%"
                for row in data
            ]

            # wykres
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor(CHART_FACE)
            ax.set_facecolor(CHART_AX_FACE)
            scatter = ax.scatter(x, y, color="#00FFFF", alpha=0.7)

            ax.set_title(f"{game_name} – Wpływ czasu gry na osiągnięcia (%)", color='white', fontsize=14)
            ax.set_xlabel("Czas gry (godziny)", color='white')
            ax.set_ylabel("Procent osiągnięć", color='white')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            for spine in ax.spines.values():
                spine.set_color(BORDER_COLOR)

            annot = ax.annotate(
                "", xy=(0, 0), xytext=(15, 15), textcoords="offset points",
                fontsize=9, color='#00FFFF',
                bbox=dict(boxstyle="round", fc="black", ec="#00FFFF", lw=1),
                arrowprops=dict(arrowstyle="->", color="#00FFFF")
            )
            annot.set_visible(False)

            def update_annot(ind):
                idx = ind["ind"][0]
                annot.xy = (x[idx], y[idx])
                annot.set_text(labels[idx])
                annot.set_visible(True)

            def on_hover(event):
                if event.inaxes == ax:
                    cont, ind = scatter.contains(event)
                    if cont:
                        update_annot(ind)
                        fig.canvas.draw_idle()
                    elif annot.get_visible():
                        annot.set_visible(False)
                        fig.canvas.draw_idle()

            fig.canvas.mpl_connect("motion_notify_event", on_hover)

            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # === SNAPSHOT dla AI (1:1 z tym co widać) ===
            df_snap = pd.DataFrame({
                "HoursPlayed": x.astype(float),
                "AchievementPercent": y.astype(float),
                "AchievementsCount": ach.astype(int),
            })
            register_chart_snapshot(ChartSnapshot(
                chart_type="scatter",
                title=f"{game_name} – Czas gry vs % osiągnięć",
                df=df_snap,
                x_col="HoursPlayed",
                y_col="AchievementPercent",
                series_col=None,
                meta={"game": game_name, "points": int(len(df_snap))}
            ))
            append_log(log_box, f"[Chart] Snapshot ({game_name}): {len(df_snap)} punktów.")

        def on_select(_event):
            sel = listbox.curselection()
            if sel:
                draw_chart(listbox.get(sel[0]))

        listbox.bind('<<ListboxSelect>>', on_select)

        # opcjonalnie automatycznie narysuj pierwszą grę
        if game_titles:
            listbox.selection_set(0)
            draw_chart(game_titles[0])

    except Exception as e:
        print(f"Błąd generowania wykresu zależności czasu i osiągnięć: {e}")
        append_log(log_box, f"[Playtime vs Ach] Błąd: {e}")

def main_ui():
    root = tk.Tk()
    root.title("Panel główny – Edgerunners UI")
    root.configure(bg=COLOR_RIGHT)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}+0+0")

    # ---- wymiary
    w_left = int(screen_width * 0.40)
    w_right = screen_width - w_left
    h_top = int(screen_height * 0.60)     # górny panel (wykresy)
    h_bottom = screen_height - h_top      # dolny panel (info/log)

    # ---- lewy panel (Opcje) na pełną wysokość
    OknoOpcje = tk.Frame(
        root, width=w_left, height=screen_height,
        bg=COLOR_LEFT, highlightbackground=BORDER_COLOR, highlightthickness=BORDER_WIDTH
    )
    OknoOpcje.place(x=0, y=0)

    # wiersze na przyciski w lewym panelu
    h_row = 50
    OknoOpcje_1 = tk.Frame(OknoOpcje, width=w_left, height=h_row, bg=COLOR_LEFT); OknoOpcje_1.place(x=10, y=60)
    OknoOpcje_2 = tk.Frame(OknoOpcje, width=w_left, height=h_row, bg=COLOR_LEFT); OknoOpcje_2.place(x=10, y=60 + h_row)
    OknoOpcje_3 = tk.Frame(OknoOpcje, width=w_left, height=h_row, bg=COLOR_LEFT); OknoOpcje_3.place(x=10, y=60 + h_row*2)
    OknoOpcje_4 = tk.Frame(OknoOpcje, width=w_left, height=h_row, bg=COLOR_LEFT); OknoOpcje_4.place(x=10, y=60 + h_row*3)
    OknoOpcje_5 = tk.Frame(OknoOpcje, width=w_left, height=180,  bg=COLOR_LEFT); OknoOpcje_5.place(x=10, y=60 + h_row*4)

    # górne: wykresy
    OknoWykres = tk.Frame(
        root, width=w_right, height=h_top,
        bg=COLOR_RIGHT, highlightbackground=BORDER_COLOR, highlightthickness=BORDER_WIDTH
    )
    OknoWykres.place(x=w_left, y=0)

    # dolne: info
    OknoInfo = tk.Frame(
        root, width=w_right, height=h_bottom,
        bg=COLOR_BOTTOM, highlightbackground=BORDER_COLOR, highlightthickness=BORDER_WIDTH
    )
    OknoInfo.place(x=w_left, y=h_top)

    # ---- status (mały) i log/info tekst
    # przenosimy status_label do lewego panelu (prawy górny róg)
    status_label = tk.Label(OknoOpcje, text="", bg=COLOR_LEFT, fg="white", font=("Courier New", 11))
    status_label.place(relx=1.0, y=10, x=-10, anchor="ne")

    # Jeden wspólny box na informacje o grze/graczu ORAZ logi
    info_text = tk.Text(
        OknoInfo, wrap="word", bg=COLOR_BOTTOM, fg="white",
        font=("Courier New", 11), borderwidth=0
    )
    info_text.place(relwidth=1, relheight=1)

    log_box = info_text

    combo = ttk.Combobox(OknoOpcje, width=50, font=FONT)
    combo_users = ttk.Combobox(OknoOpcje, width=50, font=FONT)

    info_text = tk.Text(OknoWykres, wrap="word", bg=COLOR_LEFT, fg="white", font=("Courier New", 11), borderwidth=0)
    info_text.place(relwidth=1, relheight=1)

    checkbox_vars = {
        # LIBRARY
        "Czas gry": tk.BooleanVar(),
        "Osiągnięcia": tk.BooleanVar(),
        "Procent osiągnięć": tk.BooleanVar(),
        "Przedmioty": tk.BooleanVar(),
        "Data zakupu": tk.BooleanVar(),

        # USER
        "Wiek gracza": tk.BooleanVar(),

        # GAME
        "Cena": tk.BooleanVar(),
        "Pozytywne oceny": tk.BooleanVar(),
        "Negatywne oceny": tk.BooleanVar(),
        "Data wydania": tk.BooleanVar(),
        "Liczba modów": tk.BooleanVar(),
        "Kopie sprzedane": tk.BooleanVar(),
        "Graczy teraz": tk.BooleanVar(),
        "Szczyt graczy w ostatnich 24h": tk.BooleanVar(),
        "Rekord wszechczasów": tk.BooleanVar(),
        "Twórca": tk.BooleanVar(),

        # RELACJE
        "Gatunki": tk.BooleanVar(),
        "Platformy": tk.BooleanVar(),
        "Języki interfejsu": tk.BooleanVar(),
        "Języki z napisami": tk.BooleanVar(),
        "Języki z dubbingiem": tk.BooleanVar(),
    }

    for i, (label, var) in enumerate(checkbox_vars.items()):
        cb = tk.Checkbutton(
            OknoOpcje_5,
            text=label,
            variable=var,
            bg=COLOR_LEFT,
            fg=TEXT_COLOR,
            font=FONT,
            selectcolor=COLOR_LEFT,
            anchor="w"
        )
        cb.grid(row=i // 2, column=i % 2, sticky="w", padx=10, pady=2)

    prompt_row = (len(checkbox_vars) // 2) + 1
    prompt_entry = tk.Text(OknoOpcje_5, height=4, bg="#1a1a2a", fg="white", font=("Consolas", 10), wrap="word")
    prompt_entry.grid(row=prompt_row, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="ew")

    btn_row = prompt_row + 1
    tk.Button(
        OknoOpcje_5,
        text="Analizuj dane (AI)",
        font=FONT,
        command=lambda: interpretuj_ai_z_kategorii(checkbox_vars, prompt_entry.get("1.0", "end").strip(), OknoWykres, OknoInfo)
    ).grid(row=btn_row, column=0, columnspan=2, pady=10)

    row_base = btn_row + 1
    ai_chart_btn_container = tk.Frame(OknoOpcje_5, bg=COLOR_LEFT)
    ai_chart_btn_container.grid(row=row_base, column=0, columnspan=2, padx=10, pady=(4, 6), sticky="ew")

    tk.Button(
        OknoOpcje_5,
        text="Zinterpretuj wykres",
        font=FONT,
        command=lambda: analyze_latest_chart_async(OknoInfo, user_hint="")
    ).grid(row=row_base+1, column=0, columnspan=2, pady=6)




    tk.Button(
    OknoOpcje,
    text="Odśwież dane",
    font=FONT,
    command=lambda: refresh_all_games(status_label, log_box)
).place(relx=1.0, y=10, x=-180, anchor="ne")
    
    tk.Button(
    OknoOpcje_1,
    text="Wykres czasu gry",
    font=FONT,
    command=lambda: generate_playtime_chart(OknoWykres, log_box)
).pack(side=tk.LEFT, padx=10, pady=5)
    
    tk.Button(
        OknoOpcje_1,
        text="Wykres osiągnięć",
        font=FONT,
        command=lambda: generate_achievement_pie_chart(OknoWykres)
    ).pack(side=tk.LEFT, padx=10, pady=5)

    tk.Button(
    OknoOpcje_1,
    text="Wykres osiągnięć a gatunki",
    font=FONT,
    command=lambda: generate_genre_achievement_chart(OknoWykres, log_box)
    ).pack(side=tk.LEFT, padx=10, pady=5)

    tk.Button(
    OknoOpcje_2,
    text="Wykres przedmiotów a gatunki",
    font=FONT,
    command=lambda: generate_real_currency_items_chart(OknoWykres, log_box)
    ).pack(side=tk.LEFT, padx=10, pady=5)

    tk.Button(
    OknoOpcje_2,
    text="Przedmioty według wieku",
    font=("Consolas", 11, "bold"),
    command=lambda: generate_items_by_age_chart(OknoWykres, log_box)
    ).pack(side=tk.LEFT, padx=10, pady=5)

    tk.Button(
    OknoOpcje_2,
    text="Zakup vs sesja",
    font=("Consolas", 11, "bold"),
    command=lambda: generate_purchase_vs_last_session_user_chart(OknoWykres, log_box)
    ).pack(side=tk.LEFT, padx=10, pady=5)
    
    tk.Button(
    OknoOpcje_3,
    text="Aktywność graczy (SteamCharts)",
    font=FONT,
    command=lambda: show_steamcharts_selection(OknoWykres)
    ).pack(side=tk.LEFT, padx=10, pady=5)

    tk.Button(
    OknoOpcje_3,
    text="Liczba modów do gier",
    font=FONT,
    command=lambda: generate_mods_chart(OknoWykres, log_box)
    ).pack(side=tk.LEFT, padx=10, pady=5)

    tk.Button(
    OknoOpcje_3,
    text="Mody wg gatunku",
    font=FONT,
    command=lambda: generate_mods_by_genre_chart(OknoWykres, log_box)
    ).pack(side=tk.LEFT, padx=10, pady=5)

    tk.Button(
    OknoOpcje_4,
    text="Czas vs osiągnięcia",
    font=FONT,
    command=lambda: generate_playtime_vs_achievements_chart(OknoWykres, log_box)
    ).pack(side=tk.LEFT, padx=10, pady=5)


    def restore_initial():
        root.destroy()
        python = sys.executable
        script_path = os.path.abspath(__file__)
        subprocess.Popen([python, script_path])

    def pokaz_info():
        dane = get_game_info(combo.get())
        info_text.delete("1.0", "end")
        info_text.insert("end", f"""
Nazwa gry: {dane['NazwaGry']}
Cena: {dane['CenaPLN']} PLN
Oceny: +{dane['PozytywneOceny']}, -{dane['NegatywneOceny']}
Data wydania: {dane['DataWydania']}
Modów: {dane['IloscModow']}
Kopie sprzedane: {dane['LiczbaKopiiSprzedanych']}
Graczy teraz: {dane['GraczyTeraz']}
Szczyt 24h: {dane['Szczyt24h']}
Rekord wszechczasów: {dane['RekordWszechczasów']}
Twórca: {dane['Tworca']}

Języki: Interfejs: {dane['JezykiInterfejsu']}, Napisy: {dane['JezykiZNapisy']}, Dubbing: {dane['JezykiZDubbingiem']}
DLC ({dane['LiczbaDLC']}): {dane['NazwyDLC']}
Gatunki: {dane['Gatunki']}
Platformy: {dane['Platformy']}
""")

    def pokaz_lista():
        combo.place(x=20, y=50)
        combo['values'] = get_game_titles()
        combo.set("Wybierz grę...")
        combo.bind("<<ComboboxSelected>>", lambda e: (pokaz_info(), combo.place_forget()))

    def pokaz_uzytkownikow():
        combo_users.place(x=20, y=50)
        combo_users['values'] = get_user_logins()
        combo_users.set("Wybierz gracza...")
        combo_users.bind("<<ComboboxSelected>>", lambda e: (pokaz_uzytkownika(combo_users.get().strip()), combo_users.place_forget()))

    def pokaz_uzytkownika(login):
        dane = get_user_details(login)
        info_text.delete("1.0", "end")
        if "Błąd" in dane:
            info_text.insert("end", f"Błąd: {dane['Błąd']}")
            return
        info_text.insert("end", f"""Login: {dane['login']}
Email: {dane['email']}
Wiek: {dane['age']}
Telefon: {dane['phone']}

Gry:
""")
        for g in dane['games']:
            info_text.insert("end", f"""  • {g['name']}
     - Czas gry: {g['play_time']} minut
     - Zakup: {g['purchase_date']}
     - Ostatnia sesja: {g['last_session']} ({g['last_session_length']} min)
     - Przedmioty: {g['items_owned']}
     - Osiągnięcia: {g['achievements']} ({g['achievement_progress']}%)\n""")

    def show_menu_buttons():
        przycisk_info.place_forget()
        tk.Button(OknoOpcje, text="Wstecz", font=FONT, command=restore_initial).place(x=20, y=10)
        tk.Button(OknoOpcje, text="Grach", font=FONT, command=pokaz_lista).place(x=150, y=10)
        tk.Button(OknoOpcje, text="Graczach", font=FONT, command=pokaz_uzytkownikow).place(x=280, y=10)

    przycisk_info = tk.Button(OknoOpcje, text="Informacje o", font=FONT, command=show_menu_buttons)
    przycisk_info.place(x=20, y=10)

    root.mainloop()

if __name__ == "__main__":
        main_ui()