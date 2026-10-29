import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "news.db"


def get_connection():
    """Membuka koneksi ke database berita."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    """Membuat tabel berita jika belum tersedia."""
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                published_at TEXT,
                summary TEXT,
                fetched_at TEXT NOT NULL
            )
        """)

    print("Database berhasil disiapkan.")
    print(f"Lokasi database: {DB_PATH}")


if __name__ == "__main__":
    initialize_database()
