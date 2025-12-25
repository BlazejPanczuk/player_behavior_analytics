import tkinter as tk
from tkinter import ttk, messagebox
from shop_ui_styles import COLOR_BG, COLOR_NAV, stylized_nav_button, stylized_label
from database_connection import with_db_connection
from io import BytesIO
import os
import decimal
import sys
from database_connection import (
    fetch_game_rating_summary,
    fetch_user_game_rating,
    upsert_rating,
)
# --- Obrazy (opcjonalnie) ---
try:
    from PIL import Image, ImageTk, UnidentifiedImageError
    HAS_PIL = True
except Exception:
    HAS_PIL = False

# Próba rejestracji pluginów AVIF/HEIF (jeśli są zainstalowane)
if HAS_PIL:
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()  # HEIF/HEIC/AVIF
    except Exception:
        pass
    try:
        import pillow_avif  # sam import rejestruje plugin AVIF dla Pillow
    except Exception:
        pass

try:
    import requests
    HAS_REQUESTS = True
except Exception:
    HAS_REQUESTS = False

# === Stałe UI ===
CARD_W = 240
IMG_W, IMG_H = 220, 124
GRID_PAD_X = 12
GRID_PAD_Y = 14
MAX_COLUMNS = 5


# === Cache obrazów ===
_IMAGE_CACHE = {}
_BAD_ONCE = set()

# === Baza ===
def fetch_all_genres() -> list[str]:
    """Zwraca listę nazw gatunków (alfabetycznie)."""
    with with_db_connection(dictionary=True) as (conn, cursor):
        cursor.execute("SELECT name FROM genre ORDER BY name ASC")
        rows = cursor.fetchall() or []
        return [r["name"] for r in rows if r and r.get("name")]
    
def fetch_recommended_games_with_reason(login: str, limit: int = 3, randomize: bool = False) -> list[dict]:
    """
    Zwraca listę gier (max `limit`) nieposiadanych przez usera `login`,
    posortowanych wg dopasowania gatunków do biblioteki użytkownika.
    Jeśli `randomize=True`, w obrębie dobrze dopasowanych wyników dodaj losowanie,
    aby kolejne odświeżenia mogły pokazać inne 3 gry.
    """
    order_clause = "ORDER BY s.score DESC, s.release_date DESC, s.name ASC"
    if randomize:
        # priorytet: score DESC, a w ramach podobnej jakości permutuj losowo
        order_clause = "ORDER BY s.score DESC, RAND()"

    sql = f"""
        WITH user_genres AS (
            SELECT gg.id_genre, COUNT(*) AS cnt
            FROM library l
            JOIN user u    ON u.id_user = l.id_user
            JOIN game_genre gg ON gg.id_game = l.id_game
            WHERE u.login = %s
            GROUP BY gg.id_genre
        ),
        owned AS (
            SELECT l.id_game
            FROM library l
            JOIN user u ON u.id_user = l.id_user
            WHERE u.login = %s
        ),
        candidates AS (
            SELECT g.id_game, g.name, g.price, g.release_date, g.image_url
            FROM game g
            WHERE g.id_game NOT IN (SELECT id_game FROM owned)
        ),
        scored AS (
            SELECT 
                c.id_game,
                c.name,
                c.price,
                c.release_date,
                c.image_url,
                COALESCE(SUM(ug.cnt), 0) AS score
            FROM candidates c
            LEFT JOIN game_genre gg ON gg.id_game = c.id_game
            LEFT JOIN user_genres ug ON ug.id_genre = gg.id_genre
            GROUP BY c.id_game, c.name, c.price, c.release_date, c.image_url
        )
        SELECT 
            s.id_game,
            s.name,
            s.price,
            s.release_date,
            s.image_url,
            s.score,
            (
              SELECT GROUP_CONCAT(DISTINCT ge.name ORDER BY ge.name SEPARATOR ', ')
              FROM game_genre ggi
              LEFT JOIN genre ge ON ge.id_genre = ggi.id_genre
              WHERE ggi.id_game = s.id_game
            ) AS genres,
            (
              SELECT GROUP_CONCAT(DISTINCT ge2.name ORDER BY ge2.name SEPARATOR ', ')
              FROM game_genre ggm
              JOIN user_genres ugm ON ugm.id_genre = ggm.id_genre
              JOIN genre ge2 ON ge2.id_genre = ggm.id_genre
              WHERE ggm.id_game = s.id_game
            ) AS matched_genres
        FROM scored s
        {order_clause}
        LIMIT %s
    """
    with with_db_connection(dictionary=True) as (conn, cursor):
        cursor.execute(sql, (login, login, limit))
        rows = cursor.fetchall() or []
        return rows



def build_reco_reason(row: dict) -> str:
    """
    Buduje zwięzłe 'dlaczego polecone'.
    Priorytet: dopasowane gatunki + prosty tekst.
    """
    mg = (row.get("matched_genres") or "").strip()
    if mg:
        return f"Podobne do Twoich gatunków: {mg}"
    # fallback, gdy user nie ma biblioteki lub brak przecieć
    return "Pasuje do popularnych gatunków i świeższych premier"


def get_user_balance(login: str) -> float:
    with with_db_connection(dictionary=True) as (conn, cursor):
        cursor.execute("SELECT COALESCE(balance, 0) AS balance FROM user WHERE login = %s", (login,))
        row = cursor.fetchone()
        return float(row["balance"] if row else 0.0)

def top_up_balance(login: str, amount_pln: float) -> float:
    """
    Dodaje kwotę do salda (NULL traktowany jak 0). Zgłasza błąd, jeśli użytkownik nie istnieje.
    """
    with with_db_connection(dictionary=True) as (conn, cursor):
        # Sprawdź istnienie i zablokuj wiersz na czas operacji
        cursor.execute("SELECT COALESCE(balance, 0) AS balance FROM user WHERE login = %s FOR UPDATE", (login,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Użytkownik '{login}' nie istnieje w tabeli user.")

        cursor.execute(
            """
            UPDATE user
            SET balance = COALESCE(balance, 0) + %s
            WHERE login = %s
            """,
            (amount_pln, login),
        )
        if cursor.rowcount == 0:
            # Gdyby mimo wszystko nic nie zaktualizowało
            raise RuntimeError("Nie zaktualizowano żadnego wiersza (rowcount = 0).")

        conn.commit()

        cursor.execute("SELECT COALESCE(balance, 0) AS balance FROM user WHERE login = %s", (login,))
        row = cursor.fetchone()
        return float(row["balance"] if row else 0.0)


def fetch_user_profile(login: str) -> dict:
    """
    Pobiera *wszystkie* kolumny z tabeli user dla danego loginu i zwraca jako dict.
    Filtruje typowe wrażliwe pola.
    """
    with with_db_connection(dictionary=True) as (conn, cursor):
        cursor.execute("SELECT * FROM user WHERE login = %s", (login,))
        row = cursor.fetchone() or {}
    # odfiltruj potencjalnie wrażliwe
    sensitive_keys = {"password", "pass", "pwd", "token", "salt", "secret", "api_key", "hash"}
    clean = {}
    for k, v in row.items():
        if k.lower() in sensitive_keys:
            continue
        clean[k] = v
    return clean

def fetch_games_for_shop() -> list[dict]:
    sql = """
        SELECT 
            g.id_game,
            g.name,
            g.price,
            g.release_date,
            g.image_url,
            (
              SELECT GROUP_CONCAT(DISTINCT ge.name ORDER BY ge.name SEPARATOR ', ')
              FROM game_genre gg
              LEFT JOIN genre ge ON ge.id_genre = gg.id_genre
              WHERE gg.id_game = g.id_game
            ) AS genres
        FROM game g
        ORDER BY g.release_date DESC, g.name ASC
    """
    with with_db_connection(dictionary=True) as (conn, cursor):
        cursor.execute(sql)
        rows = cursor.fetchall() or []
        return rows

def fetch_library_for_user(login: str) -> list[dict]:
    sql = """
        SELECT 
            g.id_game,
            g.name,
            g.price,
            g.release_date,
            g.image_url,
            (
              SELECT GROUP_CONCAT(DISTINCT ge.name ORDER BY ge.name SEPARATOR ', ')
              FROM game_genre gg
              LEFT JOIN genre ge ON ge.id_genre = gg.id_genre
              WHERE gg.id_game = g.id_game
            ) AS genres
        FROM library l
        JOIN user u ON u.id_user = l.id_user
        JOIN game g ON g.id_game = l.id_game
        WHERE u.login = %s
        ORDER BY g.name ASC
    """
    with with_db_connection(dictionary=True) as (conn, cursor):
        cursor.execute(sql, (login,))
        rows = cursor.fetchall() or []
        return rows
    
def get_user_id(login: str) -> int | None:
    with with_db_connection(dictionary=True) as (conn, cursor):
        cursor.execute("SELECT id_user FROM user WHERE login = %s", (login,))
        row = cursor.fetchone()
        return int(row["id_user"]) if row else None

def fetch_owned_game_ids(login: str) -> set[int]:
    sql = """
        SELECT l.id_game
        FROM library l
        JOIN user u ON u.id_user = l.id_user
        WHERE u.login = %s
    """
    with with_db_connection(dictionary=True) as (conn, cursor):
        cursor.execute(sql, (login,))
        rows = cursor.fetchall() or []
        return {int(r["id_game"]) for r in rows}

def purchase_game(login: str, game_id: int) -> tuple[bool, str, float]:
    with with_db_connection(dictionary=True) as (conn, cursor):
        cursor.execute("""
            SELECT u.id_user, COALESCE(u.balance, 0) AS balance, g.price
            FROM user u
            JOIN game g ON g.id_game = %s
            WHERE u.login = %s
            FOR UPDATE
        """, (game_id, login))
        row = cursor.fetchone()
        if not row:
            return (False, "Użytkownik lub gra nie istnieje.", 0.0)
        id_user = int(row["id_user"])
        balance = float(row["balance"])
        price = float(row["price"] if row["price"] is not None else 0.0)
        cursor.execute("SELECT 1 FROM library WHERE id_user = %s AND id_game = %s", (id_user, game_id))
        if cursor.fetchone():
            return (False, "Masz już tę grę.", balance)
        if balance < price:
            return (False, "Za mało środków na koncie.", balance)
        cursor.execute("UPDATE user SET balance = COALESCE(balance, 0) - %s WHERE id_user = %s", (price, id_user))
        cursor.execute("INSERT INTO library (id_user, id_game) VALUES (%s, %s)", (id_user, game_id))
        conn.commit()
        cursor.execute("SELECT COALESCE(balance, 0) AS balance FROM user WHERE id_user = %s", (id_user,))
        nb = cursor.fetchone()
        new_balance = float(nb["balance"] if nb else 0.0)
        return (True, "Zakup zakończony powodzeniem.", new_balance)


# === Obrazy / placeholdery ===
def _placeholder_widget(parent, w, h, text="NO IMAGE", fg="#00FFFF"):
    f = tk.Frame(parent, width=w, height=h, bg="#0A0A1A",
                 highlightbackground="#222", highlightthickness=1)
    f.pack_propagate(False)
    tk.Label(f, text=text, bg="#0A0A1A", fg=fg, font=("Consolas", 10)).pack(expand=True)
    return f

def _image_widget(parent, src, w, h):
    if not HAS_PIL:
        return _placeholder_widget(parent, w, h)

    path = (src or "").strip()

    if not path:
        return _placeholder_widget(parent, w, h)

    if not path.startswith(("http://", "https://")) and not os.path.exists(path):
        return _placeholder_widget(parent, w, h, text="NO IMAGE")

    def _build_photo(img):
        img = img.convert("RGB")
        img.thumbnail((w, h), Image.LANCZOS)
        bg = Image.new("RGB", (w, h), "#0A0A1A")
        x = (w - img.width) // 2
        y = (h - img.height) // 2
        bg.paste(img, (x, y))
        return ImageTk.PhotoImage(bg)

    key = f"{path}|{w}x{h}"

    if key in _IMAGE_CACHE and _IMAGE_CACHE[key] is not None:
        ph = _IMAGE_CACHE[key]
        lbl = tk.Label(parent, image=ph, bg="#111122")
        if not hasattr(parent, "_img_refs"):
            parent._img_refs = []
        parent._img_refs.append(ph)
        return lbl

    if key in _IMAGE_CACHE and _IMAGE_CACHE[key] is None:
        return _placeholder_widget(parent, w, h, text="BAD IMAGE", fg="#FF5577")

    try:
        if not path:
            _IMAGE_CACHE[key] = None
            return _placeholder_widget(parent, w, h)

        if os.path.exists(path):
            img = Image.open(path)
            ph = _build_photo(img)
        elif path.startswith(("http://", "https://")) and HAS_REQUESTS:
            r = requests.get(path, timeout=5)
            r.raise_for_status()
            img = Image.open(BytesIO(r.content))
            ph = _build_photo(img)
        else:
            _IMAGE_CACHE[key] = None
            return _placeholder_widget(parent, w, h)

        _IMAGE_CACHE[key] = ph
        if not hasattr(parent, "_img_refs"):
            parent._img_refs = []
        parent._img_refs.append(ph)
        return tk.Label(parent, image=ph, bg="#111122")

    except UnidentifiedImageError as e:
        _IMAGE_CACHE[key] = None
        if key not in _BAD_ONCE:
            print(f"[IMG BAD FORMAT] {path} -> {e}")
            _BAD_ONCE.add(key)
        return _placeholder_widget(parent, w, h, text="BAD IMAGE", fg="#FF5577")
    except Exception as e:
        _IMAGE_CACHE[key] = None
        if key not in _BAD_ONCE:
            print(f"[IMG ERROR] {path} -> {e}")
            _BAD_ONCE.add(key)
        return _placeholder_widget(parent, w, h, text="IMG ERROR", fg="#FF5577")

# === Scrollowalna siatka ===
class ScrollGrid(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self.canvas = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=COLOR_BG)

        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.vsb.pack(side="right", fill="y")
        self._vsb_shown = True
        self._scroll_enabled = False

        self.inner.bind("<Configure>", self._on_layout_change)
        self.canvas.bind("<Configure>", self._on_layout_change)

        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def _bind_mousewheel(self, _e=None):
        try:
            self.canvas.focus_set()
        except Exception:
            pass
        self.canvas.bind("<MouseWheel>", self._on_mousewheel, add="+")
        self.canvas.bind("<Button-4>", self._on_mousewheel, add="+")
        self.canvas.bind("<Button-5>", self._on_mousewheel, add="+")

    def _unbind_mousewheel(self, _e=None):
        try:
            self.canvas.unbind("<MouseWheel>")
            self.canvas.unbind("<Button-4>")
            self.canvas.unbind("<Button-5>")
        except Exception:
            pass

    def _on_mousewheel(self, event):
        if not self._scroll_enabled:
            return "break"

        if getattr(event, "num", None) in (4, 5):
            step = -1 if event.num == 5 else 1
        else:
            step = 1 if event.delta > 0 else -1

        self.canvas.yview_scroll(-step, "units")

        top, bottom = self.canvas.yview()
        if bottom > 1.0:
            vis = bottom - top
            self.canvas.yview_moveto(max(0.0, 1.0 - vis))
            return "break"
        if top < 0.0:
            self.canvas.yview_moveto(0.0)
            return "break"

        return "break"

    def _on_layout_change(self, _e=None):
        try:
            self.canvas.itemconfigure(self.inner_id, width=self.canvas.winfo_width())
            self.canvas.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

            content_h = self.inner.winfo_reqheight()
            viewport_h = self.canvas.winfo_height()
            need_scroll = content_h > max(1, viewport_h)

            if need_scroll and not self._vsb_shown:
                self.vsb.pack(side="right", fill="y")
                self._vsb_shown = True
            elif not need_scroll and self._vsb_shown:
                self.vsb.forget()
                self._vsb_shown = False
                self.canvas.yview_moveto(0.0)

            self._scroll_enabled = bool(need_scroll)

            top, bottom = self.canvas.yview()
            if top < 0.0:
                self.canvas.yview_moveto(0.0)
            elif bottom > 1.0:
                self.canvas.yview_moveto(1.0)
        except Exception:
            pass

def _compute_columns(container_width: int) -> int:
    col_unit = CARD_W + GRID_PAD_X
    if container_width <= 0:
        return 1
    cols = max(1, container_width // col_unit)
    return min(cols, MAX_COLUMNS)

def render_grid(container: tk.Frame, games: list[dict]):
    def _add_rating_label(card: tk.Frame, row: dict, gid: int):
        """Pokazuje 'Ocena: x/10 (n)' (lub 'Brak ocen') pod przyciskiem."""
        try:
            avg = row.get("avg_rating")
            cnt = int(row.get("rating_count") or 0)
            if avg is None or cnt == 0:
                avg, cnt = fetch_game_rating_summary(gid)
        except Exception:
            avg, cnt = (None, 0)

        text = "Brak ocen" if not cnt else f"Ocena: {avg}/10  ({cnt})"
        tk.Label(card, text=text, fg="#A0AEC0", bg=card["bg"], font=("Consolas", 9)).pack(pady=(6, 0))

    def _add_rate_button_if_library(card: tk.Frame, container: tk.Frame, login: str, gid: int, title: str):
        """Jeśli to widok Biblioteki (brak akcji kupna), pokaż moją ocenę i przycisk 'Oceń'."""
        # Jeśli jest akcja zakupu, to jesteśmy w SKLEPIE -> tutaj nie robimy przycisku "Oceń"
        if callable(getattr(container, "purchase_game", None)):
            return

        # Moja ocena (mały napis)
        try:
            my = fetch_user_game_rating(login, gid) if login and gid else None
        except Exception:
            my = None

        tk.Label(
            card,
            text=(f"Moja ocena: {my}/10" if my else "Nie oceniono"),
            fg="#94a3b8",
            bg=card["bg"],
            font=("Consolas", 9),
        ).pack(pady=(2, 0))

        # callback do odświeżenia biblioteki po zapisie
        on_saved = getattr(container, "on_rating_saved", None)

        ttk.Button(
            card,
            text="Oceń",
            command=lambda: open_rating_dialog(
                container,
                login,
                gid,
                title,
                on_saved=on_saved,
            ),
        ).pack(pady=(6, 0))
    
    for w in container.winfo_children():
        w.destroy()

    if not games:
        tk.Label(container, text="Brak gier w bazie.", fg="#888888", bg=COLOR_BG,
                 font=("Consolas", 14)).pack(pady=40)
        return

    # --- kontekst sklepu przekazany przez parenta ---
    login = getattr(container, "login", None)
    owned_ids = set(getattr(container, "owned_ids", set()))
    purchase_game = getattr(container, "purchase_game", None)  # callable(login, id_game)->(ok,msg,new_balance)
    on_balance_change = getattr(container, "on_balance_change", None)
    on_purchase_success = getattr(container, "on_purchase_success", None)

    container._img_refs = []
    container._last_cols = None
    container._last_offset = None
    container._rows_count = 0

    def adjust_offset():
        width = max(container.winfo_width(), 1)
        cols = container._last_cols or 1
        total_width = cols * CARD_W + (cols - 1) * GRID_PAD_X
        offset_x = max(0, (width - total_width) // 2)

        if container._last_offset == offset_x:
            return
        container._last_offset = offset_x

        for r in range(container._rows_count):
            first_col_widgets = container.grid_slaves(row=r, column=0)
            if not first_col_widgets:
                continue
            w0 = first_col_widgets[0]
            if (container._last_cols or 1) == 1:
                w0.grid_configure(padx=(offset_x, offset_x))
            else:
                w0.grid_configure(padx=(offset_x, GRID_PAD_X // 2))

    def rebuild(cols: int):
        for w in container.winfo_children():
            w.destroy()

        for idx, row in enumerate(games):
            r, c = divmod(idx, cols)
            card = tk.Frame(container, bg="#111122",
                            highlightbackground="#00FFFF", highlightthickness=1,
                            width=CARD_W)
            padx = (GRID_PAD_X // 2, GRID_PAD_X // 2)
            if c == cols - 1 and cols > 1:
                padx = (GRID_PAD_X // 2, GRID_PAD_X // 2)

            is_last_row = (r == (len(games) + cols - 1) // cols - 1)
            pad_y = (GRID_PAD_Y, GRID_PAD_Y if not is_last_row else GRID_PAD_Y // 2)

            card.grid(row=r, column=c, padx=padx, pady=pad_y, sticky="n")
            card.grid_propagate(False)

            _image_widget(card, row.get("image_url"), IMG_W, IMG_H).pack(pady=(8, 6))

            title = row.get("name") or "—"
            price = row.get("price")
            genres = row.get("genres") or "—"
            rel = row.get("release_date")
            rel_txt = rel.strftime("%Y-%m-%d") if rel else "—"
            gid = int(row.get("id_game") or 0)

            tk.Label(card, text=title, fg="#00FFFF", bg="#111122",
                     font=("Consolas", 11, "bold"), wraplength=CARD_W-16,
                     justify="center").pack(padx=8)
            tk.Label(card, text=(f"{price:.2f} zł" if price is not None else "—"),
                     fg="#E5008A", bg="#111122", font=("Consolas", 11)).pack(pady=(2, 0))
            tk.Label(card, text=genres, fg="#CCCCCC", bg="#111122",
                     font=("Consolas", 9), wraplength=CARD_W-16,
                     justify="center").pack(padx=8, pady=(2, 0))
            tk.Label(card, text=f"Premiera: {rel_txt}", fg="#AAAAAA",
                     bg="#111122", font=("Consolas", 9)).pack(pady=(2, 8))

            # ---------- PRZYCISK „KUP” ----------
            btn = tk.Button(
                card, text="Kup", bg="#22223A", fg="#00FFFF",
                activebackground="#1a1a2b", activeforeground="#00FFFF",
                font=("Consolas", 11, "bold"), relief="flat", padx=12, pady=6, cursor="hand2"
            )
            btn.pack(pady=(0, 12))

            _add_rating_label(card, row, gid)
            _add_rate_button_if_library(card, container, login, gid, title)

            def set_owned(b=btn):
                b.config(text="Posiadane", state="disabled", fg="#AAAAAA", bg="#1a1a1a", cursor="arrow")

            if gid and gid in owned_ids:
                set_owned()
            else:
                def do_buy(g=gid, card_ref=card, b=btn):
                    if not (callable(purchase_game) and login and g):
                        info = tk.Label(card_ref, text="Brak akcji zakupu (purchase_game).",
                                        bg="#111122", fg="#FF5577", font=("Consolas", 9))
                        info.pack()
                        info.after(3000, info.destroy)
                        return

                    ok, msg, new_balance = purchase_game(login, g)
                    status = tk.Label(card_ref, text=msg, bg="#111122",
                                      fg=("#7CFC00" if ok else "#FF5577"),
                                      font=("Consolas", 9))
                    status.pack()
                    status.after(2500, status.destroy)
                    if ok:
                        owned_ids.add(g)
                        set_owned(b)
                        if callable(on_balance_change):
                            try: on_balance_change(new_balance)
                            except Exception: pass
                        if callable(on_purchase_success):
                            try: on_purchase_success()
                            except Exception: pass

                btn.config(command=do_buy)
            # -----------------------------------

        container._rows_count = (len(games) + cols - 1) // cols
        container.update_idletasks()
        adjust_offset()

    def do_layout(_e=None):
        width = max(container.winfo_width(), 1)
        cols = _compute_columns(width)
        if container._last_cols != cols:
            container._last_cols = cols
            container._last_offset = None
            rebuild(cols)
        else:
            adjust_offset()

    container.after(50, do_layout)
    container.bind("<Configure>", do_layout)


# === Widoki ===
def build_shop_view(parent: tk.Frame, login: str, on_balance_change, on_purchase_success=None) -> tk.Frame:
    frame = tk.Frame(parent, bg=COLOR_BG)
    
    # Górny pasek statusu
    top = tk.Frame(frame, bg=COLOR_BG)
    top.pack(fill=tk.X)
    dbg = tk.Label(top, text="Wczytywanie…", bg=COLOR_BG, fg="#888")
    dbg.pack(anchor="w", padx=8, pady=(4, 2))

    # --- dane do widoku
    games_all = fetch_games_for_shop()          # pełna lista gier z bazy
    owned_ids = fetch_owned_game_ids(login)     # posiadane
    dbg.config(text=f"Wczytano gier: {len(games_all)} | Posiadane: {len(owned_ids)}")

    # =========================
    # FILTRY NAD KAFELKAMI
    # =========================
    filters = tk.Frame(frame, bg=COLOR_BG, highlightbackground="#00FFFF", highlightthickness=1)
    filters.pack(fill=tk.X, padx=8, pady=(8, 4))

    # Zmienne filtrów
    genre_var = tk.StringVar(value="(wszystkie)")
    date_from_var = tk.StringVar()
    date_to_var = tk.StringVar()
    price_max_var = tk.StringVar()  # puste = bez limitu

    # Wiersz 1: Gatunek + Cena max
    row1 = tk.Frame(filters, bg=COLOR_BG)
    row1.pack(fill=tk.X, padx=8, pady=(8, 4))

    # Gatunek (Combobox)
    tk.Label(row1, text="Gatunek:", bg=COLOR_BG, fg="#CCCCCC", font=("Consolas", 11)).pack(side=tk.LEFT)
    try:
        genres = fetch_all_genres()
    except Exception:
        genres = []
    genre_choices = ["(wszystkie)"] + genres
    genre_cb = ttk.Combobox(row1, textvariable=genre_var, values=genre_choices, state="readonly", width=28)
    genre_cb.pack(side=tk.LEFT, padx=(8, 20))
    genre_cb.current(0)

    # Cena maks
    tk.Label(row1, text="Cena do (PLN):", bg=COLOR_BG, fg="#CCCCCC", font=("Consolas", 11)).pack(side=tk.LEFT)
    price_entry = tk.Entry(row1, textvariable=price_max_var, width=12,
                           bg="#0A0A1A", fg="#E5E5E5", insertbackground="#E5E5E5",
                           highlightbackground="#00FFFF", highlightthickness=1, relief="flat")
    price_entry.pack(side=tk.LEFT, padx=(8, 0))

    # Wiersz 2: Data od / do
    row2 = tk.Frame(filters, bg=COLOR_BG)
    row2.pack(fill=tk.X, padx=8, pady=(0, 8))

    tk.Label(row2, text="Data od (YYYY-MM-DD):", bg=COLOR_BG, fg="#CCCCCC", font=("Consolas", 11)).pack(side=tk.LEFT)
    date_from_entry = tk.Entry(row2, textvariable=date_from_var, width=14,
                               bg="#0A0A1A", fg="#E5E5E5", insertbackground="#E5E5E5",
                               highlightbackground="#00FFFF", highlightthickness=1, relief="flat")
    date_from_entry.pack(side=tk.LEFT, padx=(8, 20))

    tk.Label(row2, text="Data do (YYYY-MM-DD):", bg=COLOR_BG, fg="#CCCCCC", font=("Consolas", 11)).pack(side=tk.LEFT)
    date_to_entry = tk.Entry(row2, textvariable=date_to_var, width=14,
                             bg="#0A0A1A", fg="#E5E5E5", insertbackground="#E5E5E5",
                             highlightbackground="#00FFFF", highlightthickness=1, relief="flat")
    date_to_entry.pack(side=tk.LEFT, padx=(8, 20))

    # Przyciski: Zastosuj / Wyczyść
    btns = tk.Frame(filters, bg=COLOR_BG)
    btns.pack(fill=tk.X, padx=8, pady=(0, 10))

    # =========================
    # POLECANE (z odświeżaniem)
    # =========================
    reco_wrap = tk.Frame(frame, bg=COLOR_BG)
    reco_wrap.pack(fill=tk.X, padx=8, pady=(6, 10))

    title_row = tk.Frame(reco_wrap, bg=COLOR_BG)
    title_row.pack(fill=tk.X)
    tk.Label(title_row, text="Polecane dla Ciebie", bg=COLOR_BG, fg="#00FFFF",
             font=("Consolas", 14, "bold")).pack(side=tk.LEFT)

    # Kontener na karty i separator (stałe)
    reco_row = tk.Frame(reco_wrap, bg=COLOR_BG)
    reco_row.pack(fill=tk.X, pady=(8, 4))
    sep = tk.Frame(reco_wrap, bg="#00FFFF", height=1)
    sep.pack(fill=tk.X, pady=(6, 0))

    # Pula już pokazanych gier (rotacja bez powtórek aż do wyczerpania)
    already_shown = set()

    def render_recommendations(randomize: bool = False):
        nonlocal already_shown

        for w in reco_row.winfo_children():
            w.destroy()

        recommended = fetch_recommended_games_with_reason(login, limit=50, randomize=randomize)

        # odfiltruj już pokazane
        filtered = [r for r in recommended if r["id_game"] not in already_shown]

        # jeśli się wyczerpało -> reset
        if len(filtered) < 5:
            already_shown.clear()
            filtered = recommended

        selected = filtered[:5]
        for r in selected:
            already_shown.add(r["id_game"])

        if not selected:
            tk.Label(reco_row, text="Brak rekomendacji.", bg=COLOR_BG, fg="#888",
                     font=("Consolas", 10)).pack()
            return

        # wyśrodkowanie kart
        tk.Frame(reco_row, bg=COLOR_BG).pack(side=tk.LEFT, expand=True)
        cards_holder = tk.Frame(reco_row, bg=COLOR_BG)
        cards_holder.pack(side=tk.LEFT)
        tk.Frame(reco_row, bg=COLOR_BG).pack(side=tk.LEFT, expand=True)

        RECO_CARD_W = CARD_W + 10
        for idx, row in enumerate(selected):
            card = tk.Frame(cards_holder, bg="#111122",
                            highlightbackground="#00FFFF", highlightthickness=1,
                            width=RECO_CARD_W)
            card.grid(row=0, column=idx, padx=(0 if idx == 0 else GRID_PAD_X, GRID_PAD_X), pady=2, sticky="n")
            card.grid_propagate(False)

            _image_widget(card, row.get("image_url"), IMG_W, IMG_H).pack(pady=(10, 8))

            gid     = int(row.get("id_game"))
            title   = row.get("name") or "—"
            price   = row.get("price")
            genres  = row.get("genres") or "—"
            rel     = row.get("release_date")
            rel_txt = rel.strftime("%Y-%m-%d") if rel else "—"

            tk.Label(card, text=title, fg="#00FFFF", bg="#111122",
                     font=("Consolas", 11, "bold"), wraplength=RECO_CARD_W-16, justify="center").pack(padx=10)
            tk.Label(card, text=(f"{price:.2f} zł" if price is not None else "—"),
                     fg="#E5008A", bg="#111122", font=("Consolas", 11)).pack(pady=(2, 0))
            tk.Label(card, text=genres, fg="#CCCCCC", bg="#111122",
                     font=("Consolas", 9), wraplength=RECO_CARD_W-16, justify="center").pack(padx=10, pady=(2, 0))

            why = build_reco_reason(row)
            tk.Label(card, text=why, fg="#AAAAAA", bg="#111122",
                     font=("Consolas", 9), wraplength=RECO_CARD_W-16, justify="center").pack(padx=10, pady=(4, 8))

            btn = tk.Button(card, text="Kup", bg="#22223A", fg="#00FFFF",
                            activebackground="#1a1a2b", activeforeground="#00FFFF",
                            font=("Consolas", 11, "bold"), relief="flat", padx=12, pady=6)
            btn.pack(pady=(0, 12))

            def set_owned():
                btn.config(text="Posiadane", state="disabled", fg="#AAAAAA", bg="#1a1a1a")

            if gid in owned_ids:
                set_owned()
            else:
                def do_buy(gid=gid, card_ref=card):
                    ok, msg, new_balance = purchase_game(login, gid)
                    status = tk.Label(card_ref, text=msg, bg="#111122",
                                      fg=("#7CFC00" if ok else "#FF5577"),
                                      font=("Consolas", 9))
                    status.pack()
                    status.after(2500, status.destroy)
                    if ok:
                        owned_ids.add(gid)
                        set_owned()
                        if callable(on_balance_change):
                            on_balance_change(new_balance)
                        if callable(on_purchase_success):
                            on_purchase_success()
                btn.config(command=do_buy)

    # przycisk Odśwież (losuje inne 5)
    refresh_btn = tk.Button(
        title_row, text="Odśwież",
        bg="#111122", fg="#00FFFF",
        activebackground="#1a1a2b", activeforeground="#00FFFF",
        font=("Consolas", 10, "bold"), relief="flat", padx=10, pady=4,
        command=lambda: render_recommendations(randomize=True)
    )
    refresh_btn.pack(side=tk.LEFT, padx=10)

    # =========================
    # SIATKA SKLEPU + FILTROWANIE
    # =========================
    grid = ScrollGrid(frame)
    grid.pack(fill="both", expand=True)
    grid.inner.login = login
    grid.inner.owned_ids = set(owned_ids)               # startowa lista posiadanych
    grid.inner.purchase_game = purchase_game            # Twoja funkcja z pliku
    grid.inner.on_balance_change = on_balance_change    # callback do odświeżenia salda
    grid.inner.on_purchase_success = on_purchase_success  # np. odśwież bibliotekę
    def parse_date(s: str):
        s = (s or "").strip()
        if not s:
            return None
        try:
            # Tkinter nie ma datetime – użyj standardu
            import datetime as _dt
            y, m, d = s.split("-")
            return _dt.date(int(y), int(m), int(d))
        except Exception:
            return "ERR"

    def parse_price(s: str):
        s = (s or "").strip().replace(",", ".")
        if not s:
            return None
        try:
            v = float(s)
            if v < 0:
                return "ERR"
            return v
        except Exception:
            return "ERR"

    def apply_filters_and_render():
        # start od pełnej listy
        filtered = list(games_all)

        # gatunek
        gsel = (genre_var.get() or "").strip()
        if gsel and gsel != "(wszystkie)":
            filtered = [g for g in filtered if g.get("genres") and gsel in g["genres"].split(", ")]

        # data od/do
        df = parse_date(date_from_var.get())
        dt = parse_date(date_to_var.get())
        # sygnalizacja błędu w polach (kolor ramki)
        for ent, ok in [(date_from_entry, df not in ("ERR",)), (date_to_entry, dt not in ("ERR",))]:
            ent.config(highlightbackground=("#00FFFF" if ok else "#FF5577"))

        if df == "ERR" or dt == "ERR":
            # błędny format – nic nie filtruj po dacie
            pass
        else:
            if df:
                filtered = [g for g in filtered if (g.get("release_date") and g["release_date"] >= df)]
            if dt:
                filtered = [g for g in filtered if (g.get("release_date") and g["release_date"] <= dt)]

        # cena max
        pmax = parse_price(price_max_var.get())
        price_entry.config(highlightbackground=("#00FFFF" if pmax not in ("ERR",) else "#FF5577"))
        if pmax not in (None, "ERR"):
            filtered = [g for g in filtered if (g.get("price") is not None and float(g["price"]) <= pmax)]

        render_grid(grid.inner, filtered)
        dbg.config(text=f"Wczytano gier: {len(games_all)} | Posiadane: {len(owned_ids)} | Po filtrach: {len(filtered)}")

    def clear_filters():
        genre_var.set("(wszystkie)")
        date_from_var.set("")
        date_to_var.set("")
        price_max_var.set("")
        date_from_entry.config(highlightbackground="#00FFFF")
        date_to_entry.config(highlightbackground="#00FFFF")
        price_entry.config(highlightbackground="#00FFFF")
        render_grid(grid.inner, games_all)
        dbg.config(text=f"Wczytano gier: {len(games_all)} | Posiadane: {len(owned_ids)} | Po filtrach: {len(games_all)}")

    # przyciski
    tk.Button(btns, text="Zastosuj filtry", command=apply_filters_and_render,
              bg="#111122", fg="#00FFFF", activebackground="#1a1a2b", activeforeground="#00FFFF",
              font=("Consolas", 11, "bold"), relief="flat", padx=12, pady=6
              ).pack(side=tk.LEFT, padx=(0, 8))
    tk.Button(btns, text="Wyczyść", command=clear_filters,
              bg="#22223A", fg="#00FFFF", activebackground="#1a1a2b", activeforeground="#00FFFF",
              font=("Consolas", 11, "bold"), relief="flat", padx=12, pady=6
              ).pack(side=tk.LEFT)

    # pierwsze renderowanie: polecane + pełna siatka
    render_recommendations(randomize=False)
    render_grid(grid.inner, games_all)

    return frame





def build_library_view(parent: tk.Frame, login: str) -> tk.Frame:
    frame = tk.Frame(parent, bg=COLOR_BG)

    header = tk.Frame(frame, bg=COLOR_BG)
    header.pack(fill=tk.X)
    tk.Label(
        header,
        text=f"Biblioteka – {login}",
        bg=COLOR_BG,
        fg="#00FFFF",
        font=("Consolas", 16, "bold"),
    ).pack(side=tk.LEFT, padx=10, pady=(8, 6))

    info = tk.Label(header, text="Wczytywanie…", bg=COLOR_BG, fg="#888")
    info.pack(side=tk.LEFT, padx=10, pady=(8, 6))

    grid = ScrollGrid(frame)
    grid.pack(fill="both", expand=True)

    # --- funkcja odświeżająca zawartość biblioteki ---
    def _refresh():
        
        games = fetch_library_for_user(login)
        info.config(text=f"Łącznie pozycji: {len(games)}")

        # kontekst dla render_grid – potrzebny do ocen
        grid.inner.login = login
        # callback, który przekażemy do open_rating_dialog (przez _add_rate_button_if_library)
        grid.inner.on_rating_saved = frame.refresh

        render_grid(grid.inner, games)

    # expose do późniejszych wywołań
    frame.refresh = _refresh

    # nasłuch na globalne zdarzenie (wysyłane w save_rating)
    frame.bind("<<RatingSaved>>", lambda e: frame.refresh())

    # pierwszy render
    _refresh()

    return frame

def open_rating_dialog(parent, login: str, game_id: int, game_name: str, on_saved=None):
    """Okno dialogowe do wystawienia oceny (1–10)."""
    win = tk.Toplevel(parent)
    win.title(f"Oceń: {game_name}")
    win.configure(bg="#0b0f19")
    win.transient(parent)
    win.grab_set()

    # --- nagłówek ---
    tk.Label(win, text=f"Oceń grę: {game_name}",
             bg="#0b0f19", fg="#00ffff",
             font=("Consolas", 12, "bold")).pack(padx=12, pady=(10, 8))

    # --- aktualna ocena użytkownika ---
    current = fetch_user_game_rating(login, game_id)
    default_val = str(current) if current is not None else "10"

    entry_frame = tk.Frame(win, bg="#0b0f19")
    entry_frame.pack(pady=(4, 6))

    tk.Label(entry_frame, text="Twoja ocena:", bg="#0b0f19",
             fg="#cbd5e1", font=("Consolas", 10)).pack(side="left", padx=(0, 6))

    rating_var = tk.StringVar(value=default_val)
    entry = ttk.Entry(entry_frame, textvariable=rating_var, width=4, justify="center")
    entry.pack(side="left")
    tk.Label(entry_frame, text="/10", bg="#0b0f19",
             fg="#a1a1aa", font=("Consolas", 10)).pack(side="left", padx=(4, 0))

    # --- zapis oceny ---
    def save_rating():
        try:
            val = int(rating_var.get())
            if not (1 <= val <= 10):
                raise ValueError("Ocena musi być w zakresie 1–10")

            # zapis do bazy
            upsert_rating(login, game_id, val)

            messagebox.showinfo("Zapisano", f"Twoja ocena: {val}/10")

            # odśwież aktualny widok (bibliotekę)
            if callable(on_saved):
                on_saved()

            # wyślij globalny sygnał, aby sklep (i inne widoki) też odświeżyły się
            try:
                root = parent.winfo_toplevel()   # główne okno aplikacji
                root.event_generate("<<RatingSaved>>", when="tail")
            except Exception:
                pass

            win.destroy()

        except ValueError:
            messagebox.showwarning("Niepoprawna ocena", "Wpisz liczbę całkowitą od 1 do 10")
        except PermissionError:
            messagebox.showwarning("Brak uprawnień", "Nie posiadasz tej gry w bibliotece.")
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    ttk.Button(win, text="Zapisz ocenę", command=save_rating).pack(pady=(8, 12))

def build_profile_view(parent: tk.Frame, login: str, on_balance_change) -> tk.Frame:
    """
    Widok profilu z tabelą danych usera oraz formularzem doładowania salda.
    on_balance_change: callback(new_balance_float) – odświeża UI w pasku nawigacji itp.
    """
    frame = tk.Frame(parent, bg=COLOR_BG)

    # Nagłówek
    header = tk.Frame(frame, bg=COLOR_BG)
    header.pack(fill=tk.X)
    title_lbl = tk.Label(header, text=f"Profil – {login}",
                         bg=COLOR_BG, fg="#00FFFF", font=("Consolas", 16, "bold"))
    title_lbl.pack(side=tk.LEFT, padx=10, pady=(8, 6))

    # Dane użytkownika (siatka)
    body = tk.Frame(frame, bg=COLOR_BG)
    body.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

    # lewa: tabela danych
    left = tk.LabelFrame(body, text="Dane użytkownika", bg=COLOR_BG, fg="#00FFFF",
                         font=("Consolas", 11, "bold"), labelanchor="nw", bd=1, highlightthickness=0)
    left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

    profile = fetch_user_profile(login)

    # pokaż w siatce klucz: wartość (ładniejszy klucz: spacje, kapitalizacja)
    def prettify(k: str) -> str:
        return k.replace("_", " ").capitalize()

    row_idx = 0
    for k in sorted(profile.keys()):
        v = profile[k]
        # formatowanie wartości dat/Decimal
        if isinstance(v, (decimal.Decimal, float, int)) and k.lower() == "balance":
            v_str = f"{float(v):.2f} zł"
        else:
            v_str = str(v) if v is not None else "—"

        tk.Label(left, text=f"{prettify(k)}:",
                 bg=COLOR_BG, fg="#CCCCCC", font=("Consolas", 11), anchor="w").grid(row=row_idx, column=0, sticky="w", padx=10, pady=4)
        tk.Label(left, text=v_str,
                 bg=COLOR_BG, fg="#E5E5E5", font=("Consolas", 11), anchor="w", wraplength=600, justify="left"
                 ).grid(row=row_idx, column=1, sticky="w", padx=10, pady=4)
        row_idx += 1

    for c in (0, 1):
        left.grid_columnconfigure(c, weight=1)

    # prawa: doładowanie
    right = tk.LabelFrame(body, text="Doładowanie salda", bg=COLOR_BG, fg="#00FFFF",
                          font=("Consolas", 11, "bold"), labelanchor="nw", bd=1, highlightthickness=0)
    right.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 0))

    tk.Label(right, text="Kwota (PLN):", bg=COLOR_BG, fg="#CCCCCC", font=("Consolas", 11)).pack(anchor="w", padx=10, pady=(10, 4))
    amount_var = tk.StringVar()
    entry = tk.Entry(right, textvariable=amount_var, font=("Consolas", 12), width=16,
                     bg="#0A0A1A", fg="#E5E5E5", insertbackground="#E5E5E5",
                     highlightbackground="#00FFFF", highlightthickness=1, relief="flat")
    entry.pack(anchor="w", padx=10, pady=(0, 8))

    status_lbl = tk.Label(right, text="", bg=COLOR_BG, fg="#888", font=("Consolas", 10))
    status_lbl.pack(anchor="w", padx=10, pady=(2, 6))

    def parse_amount(txt: str) -> float:
        txt = (txt or "").strip().replace(",", ".")
        # tylko dodatnie, max 2 miejsca po przecinku
        val = round(float(txt), 2)
        if val <= 0:
            raise ValueError("Kwota musi być dodatnia.")
        return val

    def do_topup():
        try:
            amt = parse_amount(amount_var.get())
        except Exception as e:
            status_lbl.config(text=f"Błędna kwota: {e}", fg="#FF5577")
            return

        try:
            new_balance = top_up_balance(login, amt)
        except Exception as e:
            status_lbl.config(text=f"Błąd bazy: {e}", fg="#FF5577")
            return

        status_lbl.config(text=f"Doładowano {amt:.2f} zł. Nowe saldo: {new_balance:.2f} zł", fg="#7CFC00")
        amount_var.set("")
        # zaktualizuj tabelę (pole balance) i nagłówek nawigacji
        # znajdź w lewej kolumnie label z kluczem 'Balance' (lub 'balance') i zaktualizuj wartość
        for child in left.grid_slaves():
            info = child.grid_info()
            if info.get("column") == 1:
                # kolumna z wartościami – spróbujemy złapać parę po lewej (kolumna 0)
                r = info.get("row")
                key_widget = left.grid_slaves(row=r, column=0)
                if key_widget:
                    key_text = key_widget[0].cget("text").strip(": ").lower()
                    if key_text in ("balance", "saldo"):
                        child.config(text=f"{new_balance:.2f} zł")
                        break

        # callback aby odświeżyć pasek nawigacji
        try:
            on_balance_change(new_balance)
        except Exception:
            pass

    topup_btn = tk.Button(
        right, text="Doładuj", command=do_topup,
        bg="#111122", fg="#00FFFF", activebackground="#1a1a2b", activeforeground="#00FFFF",
        font=("Consolas", 12, "bold"), relief="flat", padx=14, pady=6
    )
    topup_btn.pack(anchor="w", padx=10, pady=(4, 10))

    return frame

# === Główne okno ===
def shop_ui(login: str):
    root = tk.Tk()
    root.title("Sklep")
    root.configure(bg=COLOR_BG)
    try:
        root.state("zoomed")
    except Exception:
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{sw}x{sh}+0+0")

    # Pasek nawigacji
    nav = tk.Frame(root, bg=COLOR_NAV, height=50)
    nav.pack(fill=tk.X, side=tk.TOP)

    # Kontener widoków
    view_stack = tk.Frame(root, bg=COLOR_BG)
    view_stack.pack(fill=tk.BOTH, expand=True)

    # Saldo w nav
    balance = get_user_balance(login)
    balance_label = stylized_label(nav, f"{login} | Saldo: {balance:.2f} zł")
    balance_label.pack(side=tk.RIGHT, padx=10)

    # >>> NAJPIERW callback, POTEM budowa widoków <<<
    def update_nav_balance(new_balance: float):
        balance_label.config(text=f"{login} | Saldo: {new_balance:.2f} zł")

    library_view = None
    profile_view = None

    def refresh_library_if_present():
        nonlocal library_view
        if library_view is not None and library_view.winfo_exists():
            # biblioteka już zbudowana – odśwież
            if hasattr(library_view, "refresh"):
                library_view.refresh()

    # Sklep musi dostać callback już teraz
    shop_view = build_shop_view(
        view_stack,
        login,
        on_balance_change=update_nav_balance,
        on_purchase_success=refresh_library_if_present
    )

    library_view = None
    profile_view = None

    def show_view(name: str):
        nonlocal library_view, profile_view
        for child in view_stack.winfo_children():
            child.pack_forget()

        if name == "shop":
            shop_view.pack(fill=tk.BOTH, expand=True)
        elif name == "library":
            if library_view is None or not library_view.winfo_exists():
                library_view = build_library_view(view_stack, login)
            library_view.pack(fill=tk.BOTH, expand=True)
        elif name == "profile":
            if profile_view is None or not profile_view.winfo_exists():
                profile_view = build_profile_view(view_stack, login, on_balance_change=update_nav_balance)
            profile_view.pack(fill=tk.BOTH, expand=True)

    # Przyciski nav
    stylized_nav_button(nav, "Sklep", lambda: show_view("shop")).pack(side=tk.LEFT, padx=10, pady=5)
    stylized_nav_button(nav, "Biblioteka", lambda: show_view("library")).pack(side=tk.LEFT, padx=10, pady=5)
    stylized_nav_button(nav, "Profil",   lambda: show_view("profile")).pack(side=tk.LEFT, padx=10, pady=5)

    show_view("shop")
    root.mainloop()



if __name__ == "__main__":
    if len(sys.argv) > 1:
        login = sys.argv[1]   # login przekazany z login_register_ui.py
    else:
        login = "TestUser"    # fallback, np. dla testów
    shop_ui(login)