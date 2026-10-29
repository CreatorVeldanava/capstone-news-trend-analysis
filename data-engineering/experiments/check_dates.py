import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "news.db"

with sqlite3.connect(DB_PATH) as connection:
    total = connection.execute(
        "SELECT COUNT(*) FROM articles"
    ).fetchone()[0]

    empty_dates = connection.execute("""
        SELECT COUNT(*)
        FROM articles
        WHERE published_at IS NULL
           OR TRIM(published_at) = ''
    """).fetchone()[0]

    oldest = connection.execute("""
        SELECT MIN(published_at)
        FROM articles
        WHERE published_at IS NOT NULL
          AND TRIM(published_at) != ''
    """).fetchone()[0]

    newest = connection.execute("""
        SELECT MAX(published_at)
        FROM articles
        WHERE published_at IS NOT NULL
          AND TRIM(published_at) != ''
    """).fetchone()[0]

    samples = connection.execute("""
        SELECT DISTINCT published_at
        FROM articles
        WHERE published_at IS NOT NULL
          AND TRIM(published_at) != ''
        LIMIT 10
    """).fetchall()

print("=" * 50)
print("PEMERIKSAAN TANGGAL PUBLIKASI")
print("=" * 50)
print(f"Total artikel    : {total}")
print(f"Tanggal kosong   : {empty_dates}")
print(f"Tanggal terlama  : {oldest}")
print(f"Tanggal terbaru  : {newest}")
print("\nContoh format tanggal:")

for row in samples:
    print("-", row[0])
