import mysql.connector
from contextlib import contextmanager
from typing import Optional, Tuple
@contextmanager
def with_db_connection(dictionary=False):
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='root',
        database='gamedb'
    )
    try:
        cursor = conn.cursor(dictionary=dictionary)
        yield conn, cursor
    finally:
        cursor.close()
        conn.close()

def upsert_rating(login: str, game_id: int, rating: int) -> None:
    """Zapisz lub zaktualizuj ocenę (1–10) dla gry posiadanej przez użytkownika."""
    if not (1 <= int(rating) <= 10):
        raise ValueError("Ocena musi być w zakresie 1–10")

    with with_db_connection(dictionary=True) as (conn, cur):
        # pobierz id użytkownika
        cur.execute("SELECT id_user FROM `user` WHERE login=%s", (login,))
        row = cur.fetchone()
        if not row:
            raise ValueError("Nie znaleziono użytkownika")
        uid = int(row["id_user"])

        cur.execute("""
            SELECT 1
            FROM library
            WHERE id_user=%s AND id_game=%s
            LIMIT 1
        """, (uid, game_id))
        if cur.fetchone() is None:
            raise PermissionError("Użytkownik nie posiada tej gry – nie może jej oceniać")

        cur.execute("""
            INSERT INTO rating (id_user, id_game, rating)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE rating=VALUES(rating), updated_at=CURRENT_TIMESTAMP
        """, (uid, game_id, int(rating)))
        conn.commit()


def fetch_user_game_rating(login: str, game_id: int) -> Optional[int]:
    """Pobierz ocenę użytkownika dla danej gry (lub None, jeśli nie oceniał)."""
    with with_db_connection(dictionary=True) as (conn, cur):
        cur.execute("""
            SELECT r.rating
            FROM rating r
            JOIN `user` u ON u.id_user = r.id_user
            WHERE u.login=%s AND r.id_game=%s
        """, (login, game_id))
        row = cur.fetchone()
        return int(row["rating"]) if row and row.get("rating") is not None else None


def fetch_game_rating_summary(game_id: int) -> Tuple[Optional[float], int]:
    """Zwraca (średnia_ocena, liczba_ocen)."""
    with with_db_connection(dictionary=True) as (conn, cur):
        cur.execute("""
            SELECT ROUND(AVG(r.rating),1) AS avg_rating, COUNT(*) AS cnt
            FROM rating r
            WHERE r.id_game = %s
        """, (game_id,))
        row = cur.fetchone() or {}
        avg = row.get("avg_rating")
        cnt = int(row.get("cnt") or 0)
        return (float(avg) if avg is not None else None, cnt)


def fetch_games_for_shop_with_ratings() -> list[dict]:
    """Zwraca wszystkie gry z ich średnią oceną i liczbą ocen."""
    with with_db_connection(dictionary=True) as (conn, cur):
        cur.execute("""
            SELECT g.*,
                   ROUND(AVG(r.rating),1) AS avg_rating,
                   COUNT(r.rating)        AS rating_count
            FROM game g
            LEFT JOIN rating r ON r.id_game = g.id_game
            GROUP BY g.id_game
            ORDER BY g.name
        """)
        return list(cur.fetchall())