import tkinter as tk
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import threading
import pandas as pd

from ai_local_integration import interpret_with_local_ai

def _resolve_text_widget(widget):
    if isinstance(widget, tk.Text):
        return widget
    if isinstance(widget, tk.Frame):
        for child in widget.winfo_children():
            if isinstance(child, tk.Text):
                return child
        txt = tk.Text(widget, wrap="word", bg="#121222", fg="white",
                      font=("Consolas", 10), borderwidth=0)
        txt.pack(fill="both", expand=True)
        return txt
    return widget

def append_log(widget, text: str) -> None:
    target = _resolve_text_widget(widget)
    def do_insert():
        try:
            target.insert("end", text + "\n")
            target.see("end")
        except Exception:
            try:
                prev = target.cget("text")
                target.config(text=(prev + ("\n" if prev else "") + text))
            except Exception:
                pass
    try:
        target.after(0, do_insert)
    except Exception:
        do_insert()

@dataclass
class ChartSnapshot:
    chart_type: str 
    title: str
    df: pd.DataFrame
    x_col: Optional[str] = None
    y_col: Optional[str] = None
    series_col: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

_latest_snapshot: Optional[ChartSnapshot] = None

def register_chart_snapshot(snapshot: ChartSnapshot) -> None:
    global _latest_snapshot
    _latest_snapshot = snapshot

def _short_df_preview(df: pd.DataFrame, max_rows: int = 20, max_cols: int = 6) -> str:
    df2 = df.copy()
    if df2.shape[1] > max_cols:
        df2 = df2.iloc[:, :max_cols]
    return df2.head(max_rows).to_markdown(index=False)

def _build_chart_prompt(s: ChartSnapshot, user_hint: str = "") -> str:
    rows, cols = s.df.shape
    meta_lines: List[str] = []
    if s.meta:
        for k, v in s.meta.items():
            meta_lines.append(f"- {k}: {v}")
    meta_block = "\n".join(meta_lines) if meta_lines else "- brak"

    schema_desc = "\n".join([f"- {c}: {str(s.df[c].dtype)}" for c in s.df.columns])

    prompt = f"""
Jesteś analitykiem danych gier. Dostajesz dane stojące za wykresem.

Informacje o wykresie:
- typ: {s.chart_type}
- tytuł: {s.title}
- oś X: {s.x_col or "-"}
- oś Y: {s.y_col or "-"}
- seria/kategoria: {s.series_col or "-"}

Metadane:
{meta_block}

Kształt danych: {rows} wierszy × {cols} kolumn.
Schemat kolumn:
{schema_desc}

Podgląd danych:
{_short_df_preview(s.df)}

Zadanie:
1) Opisz trend/zależności/rozrzut.
2) Wypunktuj 2–4 najważniejsze spostrzeżenia (z rzędami wielkości).
3) Wskaż możliwe anomalie/artefakty.
4) Zaproponuj 2–3 hipotezy i jak je zweryfikować.

Nie generuj kodu. Pisz po polsku, zwięźle, w punktach.
"""
    if user_hint:
        prompt += f"\nUwaga użytkownika: {user_hint}\n"
    return prompt

def analyze_latest_chart_async(info_widget: tk.Text | tk.Frame, user_hint: str = "", model: str = "mistral") -> None:
    snap = _latest_snapshot
    if snap is None:
        append_log(info_widget, "Brak zarejestrowanego wykresu do analizy.")
        return

    append_log(info_widget, "AI analizuje bieżący wykres...")

    def _job():
        try:
            prompt = _build_chart_prompt(snap, user_hint=user_hint)
            response = interpret_with_local_ai(prompt, model=model)
        except Exception as e:
            response = f"[Błąd AI]: {e}"
        target = _resolve_text_widget(info_widget)
        def _replace():
            try:
                target.delete("1.0", "end")
            except Exception:
                pass
            append_log(target, response)
        try:
            target.after(0, _replace)
        except Exception:
            _replace()
    threading.Thread(target=_job, daemon=True).start()
