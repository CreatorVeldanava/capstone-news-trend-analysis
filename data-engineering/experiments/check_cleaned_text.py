
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
db_path = BASE_DIR / "data" / "news.db"

with sqlite3.connect(db_path) as connection:
    columns = connection.execute(
        "PRAGMA table_info(articles)"
    ).fetchall()

    column_names = [column[1] for column in columns]
    print("Kolom tersedia:", column_names)

    if "cleaned_text" not in column_names:
        print("Kolom cleaned_text tidak ditemukan.")
    else:
        rows = connection.execute("""
            SELECT id, title, cleaned_text
            FROM articles
            WHERE cleaned_text IS NOT NULL
              AND TRIM(cleaned_text) != ''
            LIMIT 5
        """).fetchall()

        print("\nJumlah contoh:", len(rows))

        for article_id, title, cleaned_text in rows:
            print(f"\nID: {article_id}")
            print(f"Judul: {title}")
            print(f"Teks: {cleaned_text}")
