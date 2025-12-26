
import pandas as pd
import numpy as np
import tkinter as tk
from database_connection import with_db_connection
from ai_local_integration import interpret_with_local_ai
import threading
from textwrap import shorten

MAX_PROMPT_CHARS = 120_000         # twardy limit znaków wysyłanych do LLM
MAX_SAMPLE_ROWS = 800              # łączna liczba wierszy próbek przekazywana do LLM
TOP_N_CATS = 10                    # top-N wartości dla kolumn kategorycznych
CHUNK_ROWS = 50_000                # kiedy robić map-reduce (chunkowanie ramki)
ENABLE_MAP_REDUCE = True

# ====== OPISY KOLUMN DLA AI ======
COLUMN_DESCRIPTIONS = {
    "creator": "nazwa studia/twórcy (tekst) — może grupować gry i tłumaczyć różnice jakościowe/marketingowe",
    "genres": "gatunek/gatunki (lista/tekst rozdzielany przecinkami) — wpływa na profil gracza i typ zaangażowania",
    "negative_rating": "liczba negatywnych recenzji (int) — wskaźnik ryzyka niezadowolenia",
    "positive_rating": "liczba pozytywnych recenzji (int) — przybliżony sygnał jakości/word-of-mouth",
    "play_time": "czas gry w minutach (int) — proxy za angażowanie i retencję; rozkład często silnie skośny",
    "price": "cena w PLN (float) — bariera wejścia; interakcja z promocjami i popularnością",
    "age": "wiek gracza w latach (int) — segmentacja demograficzna (ostrożnie: możliwe luki lub bias)",
    "purchase_date": "data zakupu (date) — użyteczna do sezonowości i efektów wyprzedaży",
    "release_date": "data wydania (date) — wiek produktu; wpływa na bazę graczy i cykl życia",
    "achievements": "liczba zdobytych osiągnięć (int) — aktywność i głębokość grania",
    "achievement_progress": "procent osiągnięć (float 0–100) — jakościowa miara eksploracji treści",
    "items_owned": "liczba przedmiotów płatnych (int) — monetyzacja i zaangażowanie ekonomiczne",
    "platforms": "platformy docelowe (lista/tekst) — zasięg i bariery sprzętowe",
    "jezyki_interfejsu": "języki interfejsu (lista) — dostępność; może zwiększać popularność regionalnie",
    "jezyki_napisy": "języki napisów (lista) — dostępność treści fabularnej",
    "jezyki_dubbing": "języki dubbingu (lista) — wyższy koszt produkcji; może wzmacniać komfort i NPS",
    "current_players": "liczba graczy teraz (int) — chwilowa popularność (szum; patrz trend)",
    "peak_24h_players": "szczyt graczy w 24h (int) — dobowy potencjał aktywności",
    "peak_players": "rekord wszechczasów (int) — historyczny zasięg gry",
    "copies_sold": "sprzedane kopie (int) — skala komercyjna (często brak pełnych danych)"
}

def summarize_dataframe(df: pd.DataFrame) -> str:
    md = []

    # Info ogólne
    md.append(f"**Kształt danych:** {df.shape[0]} wierszy × {df.shape[1]} kolumn")
    nulls = df.isna().sum()
    if not nulls.empty:
        null_pct = (nulls / len(df) * 100).round(2)
        na_table = pd.DataFrame({"braki": nulls, "%": null_pct})
        md.append("\n**Braki danych (top 20):**\n" + na_table.sort_values("braki", ascending=False).head(20).to_markdown())

    # Numeryczne
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if num_cols:
        desc = df[num_cols].describe(percentiles=[.05,.25,.5,.75,.95]).T
        md.append("\n**Statystyki numeryczne:**\n" + desc.to_markdown())

        out_md = []
        for c in num_cols:
            s = df[c].dropna()
            if len(s) == 0:
                continue
            q1, q3 = s.quantile([.25, .75])
            iqr = q3 - q1
            lower, upper = q1 - 1.5*iqr, q3 + 1.5*iqr
            out_count = int(((s < lower) | (s > upper)).sum())
            if out_count:
                out_md.append(f"- {c}: odchyleń poza IQR = {out_count} ({round(out_count/len(s)*100,2)}%)")
        if out_md:
            md.append("\n**Potencjalne obserwacje odstające (IQR):**\n" + "\n".join(out_md))

    cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    if cat_cols:
        cat_md = []
        for c in cat_cols[:30]:
            vc = df[c].astype("string").fillna("<NA>").value_counts(dropna=False).head(TOP_N_CATS)
            uniq = df[c].nunique(dropna=False)
            cat_md.append(f"\n**{c}** (unikalnych: {uniq}, top {TOP_N_CATS}):\n" + vc.to_markdown())
        md.append("\n**Rozkłady kategoryczne:**\n" + "\n".join(cat_md))

    dt_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    if dt_cols:
        dt_md = []
        for c in dt_cols:
            s = df[c].dropna()
            try:
                rng = (s.min(), s.max())
                by_month = s.dt.to_period("M").value_counts().sort_index().tail(24)
                dt_md.append(f"\n**{c}**: zakres {rng[0]} → {rng[1]}\nOstatnie 24 miesiące:\n" + by_month.to_markdown())
            except Exception:
                pass
        if dt_md:
            md.append("\n**Pola dat/czas:**\n" + "\n".join(dt_md))

    return "\n\n".join(md)


def build_samples(df: pd.DataFrame) -> pd.DataFrame:
    rows_left = MAX_SAMPLE_ROWS
    samples = []

    strat_cols = [c for c in ["genres", "creator"] if c in df.columns]
    used = set()

    for col in strat_cols:
        vc = df[col].astype("string").fillna("<NA>").value_counts().head(10).index.tolist()
        for v in vc:
            sub = df[df[col].astype("string").fillna("<NA>") == v]
            take = min(max(5, rows_left // (len(vc) or 1)), len(sub))
            if take > 0:
                samples.append(sub.sample(take, random_state=42))
                rows_left -= take
                used.add(col)
            if rows_left <= 0:
                break
        if rows_left <= 0:
            break

    if rows_left > 0:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if num_cols:
            key = num_cols[0]
            qs = df[key].quantile([0, .25, .5, .75, 1]).drop_duplicates()
            per_bin = max(10, rows_left // max(1, len(qs)-1))
            for i in range(len(qs)-1):
                lo, hi = qs.iloc[i], qs.iloc[i+1]
                sub = df[(df[key] >= lo) & (df[key] <= hi)]
                take = min(per_bin, len(sub))
                if take > 0:
                    samples.append(sub.sample(take, random_state=42))
                    rows_left -= take
                if rows_left <= 0:
                    break

    if rows_left > 0 and len(df) > 0:
        take = min(rows_left, len(df))
        samples.append(df.sample(take, random_state=42))

    if samples:
        out = pd.concat(samples, ignore_index=True).drop_duplicates().head(MAX_SAMPLE_ROWS)
        return out
    return df.head(min(MAX_SAMPLE_ROWS, len(df)))


def build_ai_prompt(df, selected_categories, user_prompt="", sample_df=None, summary_md=None):
    columns = df.columns.tolist()

    desc_lines = []
    for col in columns:
        if col in COLUMN_DESCRIPTIONS:
            desc_lines.append(f"- {col}: {COLUMN_DESCRIPTIONS[col]}")
        else:
            desc_lines.append(f"- {col}: brak opisu (typ: {df[col].dtype})")
    columns_desc = "\n".join(desc_lines)

    project_context = (
        "Kontekst projektu i oczekiwania:\n"
        "- Analizujemy dane graczy/gier w celu: (a) zrozumienia czynników popularności i zaangażowania, "
        "(b) wykrycia anomalii oraz problemów z jakością danych, (c) wyciągnięcia praktycznych wniosków i hipotez.\n"
        "- Jeśli czegoś brakuje albo nie można wnioskować — napisz to wprost.\n"
        "- Preferowana forma: krótkie sekcje z nagłówkami i punktami; liczby podawaj z rzędem wielkości.\n"
    )

    checks = []
    has = lambda *cols: all(c in columns for c in cols)

    if has("play_time", "genres"):
        checks.append("Zależność czasu gry (play_time) od gatunków (genres).")
    if has("price", "play_time"):
        checks.append("Wpływ ceny (price) na play_time — czy wyższa cena koreluje z krótszym czasem gry?")
    if has("positive_rating", "negative_rating"):
        checks.append("Balans recenzji (pozytywne vs negatywne) a popularność/retencja.")
    if has("release_date", "play_time"):
        checks.append("Efekt wieku gry (release_date) na aktywność — starzejące się tytuły vs nowsze.")
    if has("purchase_date"):
        checks.append("Sezonowość zakupów (purchase_date) — skoki podczas wyprzedaży/świąt.")
    if has("platforms", "play_time"):
        checks.append("Różnice zaangażowania między platformami.")
    if has("jezyki_interfejsu") or has("jezyki_napisy") or has("jezyki_dubbing"):
        checks.append("Wpływ liczby wspieranych języków na popularność.")
    if has("items_owned", "play_time"):
        checks.append("Związek monetyzacji (items_owned) z czasem gry (engagement).")
    if has("current_players", "peak_24h_players", "peak_players"):
        checks.append("Sprawdź spójność bieżącej popularności z historycznymi rekordami (trend/odchylenia).")
    if has("copies_sold", "positive_rating"):
        checks.append("Czy wysoka sprzedaż idzie w parze z jakością (pozytywne recenzje).")

    checks_md = ""
    if checks:
        checks_md = "**Relacje, na które szczególnie warto spojrzeć:**\n- " + "\n- ".join(checks) + "\n"

    if summary_md is None:
        summary_md = summarize_dataframe(df)

    sample_md = ""
    if sample_df is not None and not sample_df.empty:
        sample_md = "\n\n**Przykładowe wiersze (reprezentatywne próbki, nie całość):**\n"
        sample_md += sample_df.to_markdown(index=False)

    prompt = f"""
    Masz dane w Pandas DataFrame z kolumnami:
    {columns_desc}

    {project_context}
    {checks_md}

    **Podsumowanie danych (skondensowane):**
    {summary_md}
    {sample_md}

    Twoje zadanie: wykonaj szczegółową analizę według poniższych kroków.

    1. **Opis danych**
    - Wymień kolumny i krótko opisz, co zawierają.
    - Podaj liczbę wierszy i kolumn.
    - Powiedz, ile jest braków w każdej kolumnie (%).

    2. **Analiza zmiennych numerycznych**
    - Dla każdej kolumny numerycznej podaj: średnią, medianę, min, max, odchylenie standardowe, 5% i 95% percentyl.
    - Zidentyfikuj outliery metodą IQR i wypisz kilka przykładów (np. nazwy gier, jeśli jest kolumna tytułu).

    3. **Analiza zmiennych kategorycznych**
    - Podaj liczbę unikalnych wartości i TOP 5 najczęstszych.
    - Jeśli występują kolumny typu gatunek/platforma/język – porównaj średnie wartości kolumn numerycznych w tych grupach.

    4. **Analiza dat**
    - Podaj zakres dat i średni odstęp między nimi.
    - Jeśli są kolumny dat, opisz, jak zmieniają się inne zmienne w czasie.

    5. **Korelacje i zależności**
    - Sprawdź korelacje między kolumnami numerycznymi i wypisz TOP 5 dodatnich i ujemnych.
    - Opisz, co mogą oznaczać w kontekście gier.

    6. **Wnioski i rekomendacje**
    - Wypisz 3–5 najważniejszych wniosków.
    - Jeśli są anomalie, wskaż ich możliwe przyczyny.
    - Zaproponuj, jakie dodatkowe dane mogłyby poprawić analizę.

    Zasady:
    - Nie generuj wykresów.
    - Nie zgaduj — jeżeli brak danych, zaznacz to.
    - Odpowiadaj po polsku, w formie punktów.
    """

    if user_prompt:
        prompt += f"\n\nUżytkownik dodał polecenie: {user_prompt}"


    if len(prompt) > MAX_PROMPT_CHARS:
        from textwrap import shorten
        prompt = shorten(prompt, width=MAX_PROMPT_CHARS, placeholder="\n\n...[ucięto dla limitu]")

    return prompt

def fetch_data_for_categories(selected):
    query_parts = []
    joins = set()
    conditions = []
    group_by_cols = [] 

    if not selected:
        return pd.DataFrame()

    if "Czas gry" in selected:
        query_parts.append("l.play_time")
        group_by_cols.append("l.play_time")
        joins.add("library l")
    if "Osiągnięcia" in selected:
        query_parts.append("l.achievements")
        group_by_cols.append("l.achievements")
        joins.add("library l")
    if "Procent osiągnięć" in selected:
        query_parts.append("l.achievement_progress")
        group_by_cols.append("l.achievement_progress")
        joins.add("library l")
    if "Przedmioty" in selected:
        query_parts.append("l.items_owned")
        group_by_cols.append("l.items_owned")
        joins.add("library l")
    if "Data zakupu" in selected:
        query_parts.append("l.purchase_date")
        group_by_cols.append("l.purchase_date")
        joins.add("library l")

    # ===== USER =====
    if "Wiek gracza" in selected:
        query_parts.append("u.age")
        group_by_cols.append("u.age")
        joins.update(["library l", "user u"])
        conditions.append("l.id_user = u.id_user")

    # ===== GAME =====
    if any(opt in selected for opt in [
        "Cena", "Pozytywne oceny", "Negatywne oceny", "Data wydania",
        "Liczba modów", "Kopie sprzedane", "Graczy teraz",
        "Szczyt 24h", "Rekord wszechczasów", "Twórca"
    ]):
        joins.update(["library l", "game g"])
        conditions.append("l.id_game = g.id_game")

    col_map = {
        "Cena": "g.price",
        "Pozytywne oceny": "g.positive_rating",
        "Negatywne oceny": "g.negative_rating",
        "Data wydania": "g.release_date",
        "Liczba modów": "g.mods",
        "Kopie sprzedane": "g.copies_sold",
        "Graczy teraz": "g.current_players",
        "Szczyt 24h": "g.peak_24h_players",
        "Rekord wszechczasów": "g.peak_players",
        "Twórca": "g.creator"
    }
    for opt, col in col_map.items():
        if opt in selected:
            query_parts.append(col)
            group_by_cols.append(col)

    # ===== GENRES =====
    if "Gatunki" in selected:
        query_parts.append("GROUP_CONCAT(DISTINCT ge.name) AS genres")
        joins.update(["library l", "game g", "game_genre gg", "genre ge"])
        conditions.extend([
            "l.id_game = g.id_game",
            "gg.id_game = g.id_game",
            "gg.id_genre = ge.id_genre"
        ])

    # ===== PLATFORMY =====
    if "Platformy" in selected:
        query_parts.append("GROUP_CONCAT(DISTINCT p.name) AS platforms")
        joins.update(["library l", "game g", "game_platform gp", "platform p"])
        conditions.extend([
            "l.id_game = g.id_game",
            "gp.id_game = g.id_game",
            "gp.id_platform = p.id_platform"
        ])

    # ===== LANGUAGES =====
    lang_fields = [
        ("Języki interfejsu", "l2.name", "jezyki_interfejsu", "gl.has_interface = 1"),
        ("Języki z napisami", "l3.name", "jezyki_napisy", "gl.has_subtitles = 1"),
        ("Języki z dubbingiem", "l4.name", "jezyki_dubbing", "gl.has_dubbing = 1")
    ]
    for opt, lname, alias, cond in lang_fields:
        if opt in selected:
            query_parts.append(f"GROUP_CONCAT(DISTINCT IF({cond}, {lname}, NULL)) AS {alias}")
            joins.update(["library l", "game g", "game_language gl", f"language {lname.split('.')[0]}"])
            conditions.extend([
                "l.id_game = g.id_game",
                "gl.id_game = g.id_game",
                f"gl.id_language = {lname.split('.')[0]}.id_language"
            ])

    base = "FROM " + ", ".join(sorted(joins))
    where = "WHERE " + " AND ".join(set(conditions)) if conditions else ""
    group_by = f"GROUP BY {', '.join(sorted(set(group_by_cols)))}" if group_by_cols else ""

    sql = f"""
        SELECT {', '.join(sorted(set(query_parts)))}
        {base}
        {where}
        {group_by}
    """

    try:
        with with_db_connection(dictionary=True) as (conn, cursor):
            cursor.execute(sql)
            rows = cursor.fetchall()
            df = pd.DataFrame(rows)

            if 'genres' in df.columns:
                df['genres'] = df['genres'].str.split(',')
                df = df.explode('genres')
                df['genres'] = df['genres'].str.strip()

            for col in df.columns:
                if "date" in col.lower():
                    try:
                        df[col] = pd.to_datetime(df[col], errors="coerce")
                    except Exception:
                        pass

            return df

    except Exception as e:
        print(f"[Błąd bazy danych]: {e}")
        return pd.DataFrame()


def map_reduce_analysis(df: pd.DataFrame, selected, user_prompt: str) -> str:
  
    parts = []
    for start in range(0, len(df), CHUNK_ROWS):
        part = df.iloc[start:start+CHUNK_ROWS].copy()
        summary = summarize_dataframe(part)
        sample = build_samples(part)
        prompt = build_ai_prompt(part, selected, user_prompt, sample_df=sample, summary_md=summary)
        resp = interpret_with_local_ai(prompt, model="mistral")
        parts.append(resp)

    merge_prompt = f"""Masz częściowe analizy AI (poniżej). 
Scal je w jeden spójny raport, eliminując powtórki i podkreślając tezy wspólne oraz wyjątki.

Analizy cząstkowe:
------------------
{chr(10).join(f"### Część {i+1}\n{p}" for i,p in enumerate(parts))}

Zwróć: Sekcje (Wnioski kluczowe, Zależności, Anomalie, Rekomendacje). Zwięźle, po polsku.
"""
    if len(merge_prompt) > MAX_PROMPT_CHARS:
        merge_prompt = shorten(merge_prompt, width=MAX_PROMPT_CHARS, placeholder="\n\n...[ucięto dla limitu]")

    return interpret_with_local_ai(merge_prompt, model="mistral")


def interpretuj_ai_z_kategorii(checkboxes, user_prompt, frame_data, frame_ai):
    selected = [k for k, v in checkboxes.items() if v.get()]
    if not selected:
        tk.messagebox.showwarning("Uwaga", "Wybierz przynajmniej jedną kategorię.")
        return

    df = fetch_data_for_categories(selected)

    for widget in frame_data.winfo_children():
        widget.destroy()
    for widget in frame_ai.winfo_children():
        widget.destroy()

    # Górny panel – dane
    data_box = tk.Text(frame_data, bg="#121222", fg="white", font=("Consolas", 10), wrap="word", borderwidth=0)
    data_box.place(x=0, y=0, relwidth=1.0, relheight=1.0)

    # Dolny panel – analiza AI
    ai_box = tk.Text(frame_ai, bg="#121222", fg="white", font=("Consolas", 10), wrap="word", borderwidth=0)
    ai_box.place(x=0, y=0, relwidth=1.0, relheight=1.0)

    if df.empty:
        data_box.insert("end", "Brak danych dla wybranych kategorii.\n")
        return

    summary_md = summarize_dataframe(df)
    data_box.insert("end", "Podsumowanie danych (skrócone):\n")
    data_box.insert("end", summary_md + "\n\n")
    data_box.insert("end", "Wszystkie dane:\n")
    data_box.insert("end", df.to_markdown(index=False) + "\n\n")

    ai_box.insert("end", "Analiza AI (to może potrwać chwilę)...\n")
    ai_box.see("end")

    def run_ai():
        try:
            if ENABLE_MAP_REDUCE and len(df) > CHUNK_ROWS:
                response = map_reduce_analysis(df, selected, user_prompt)
            else:
                prompt = build_ai_prompt(df, selected, user_prompt, sample_df=df, summary_md=summary_md)
                response = interpret_with_local_ai(prompt, model="mistral")
        except Exception as e:
            response = f"[Błąd AI]: {e}"

        ai_box.after(0, lambda: wstaw_odpowiedz(response))

    def wstaw_odpowiedz(response):
        ai_box.delete("1.0", "end")
        ai_box.insert("end", response)
        ai_box.see("end")

    threading.Thread(target=run_ai, daemon=True).start()