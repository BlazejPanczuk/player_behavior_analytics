from pathlib import Path
from database_connection import with_db_connection

# =========================================================
# STRUKTURA:
# Aplikacja/
# ├── code/test.py
# └── __inz_assets_f3a9c1e7b2/
#     ├── 1.jpg
#     ├── 2.png
#     ├── ...
#     └── default.png
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = BASE_DIR / "__inz_assets_f3a9c1e7b2"
DEFAULT_IMG = ASSETS_DIR / "default.png"


# =========================================================
# DIAGNOSTYKA (MOŻESZ USUNĄĆ PO TESTACH)
# =========================================================
print("BASE_DIR:", BASE_DIR)
print("ASSETS_DIR:", ASSETS_DIR)
print("ASSETS_DIR EXISTS:", ASSETS_DIR.exists())

if ASSETS_DIR.exists():
    print("FILES:")
    for f in ASSETS_DIR.iterdir():
        print(" -", f.name)
else:
    print("[ERROR] ASSETS_DIR NIE ISTNIEJE")


# =========================================================
# MAPOWANIE id_game → PLIK
# =========================================================
def resolve_image_path(id_game: int) -> str:
    for ext in ("jpg", "png"):
        candidate = ASSETS_DIR / f"{id_game}.{ext}"
        if candidate.is_file():
            return candidate.as_posix()

    return DEFAULT_IMG.as_posix()


# =========================================================
# UPDATE BAZY
# =========================================================
def update_image_paths():
    with with_db_connection(dictionary=True) as (conn, cursor):
        cursor.execute("SELECT id_game FROM game")
        games = cursor.fetchall()

        for g in games:
            gid = int(g["id_game"])
            img_path = resolve_image_path(gid)

            cursor.execute(
                "UPDATE game SET image_url = %s WHERE id_game = %s",
                (img_path, gid)
            )

            print(f"id_game={gid} -> {img_path}")

        conn.commit()


# =========================================================
# START
# =========================================================
if __name__ == "__main__":
    update_image_paths()
    print("Image paths updated")
