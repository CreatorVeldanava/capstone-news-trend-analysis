
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "news.db"


def main():
    if not DB_PATH.exists():
        print("Database tidak ditemukan.")
        return

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row

        total = connection.execute(
            "SELECT COUNT(*) AS total FROM articles"
        ).fetchone()["total"]

        print("=" * 65)
        print("PEMERIKSAAN DATABASE BERITA")
        print("=" * 65)
        print(f"Total artikel: {total}")

        print("\nJumlah artikel per sumber:")
        rows = connection.execute("""
            SELECT source, COUNT(*) AS jumlah
            FROM articles
            GROUP BY source
            ORDER BY source
        """).fetchall()

        for row in rows:
            print(f"- {row['source']}: {row['jumlah']} artikel")

        print("\nPemeriksaan data kosong:")
        missing = connection.execute("""
            SELECT
                SUM(CASE WHEN title IS NULL OR TRIM(title) = ''
                    THEN 1 ELSE 0 END) AS judul_kosong,
                SUM(CASE WHEN url IS NULL OR TRIM(url) = ''
                    THEN 1 ELSE 0 END) AS url_kosong,
                SUM(CASE WHEN published_at IS NULL
                    OR TRIM(published_at) = ''
                    THEN 1 ELSE 0 END) AS tanggal_kosong,
                SUM(CASE WHEN summary IS NULL OR TRIM(summary) = ''
                    THEN 1 ELSE 0 END) AS ringkasan_kosong
            FROM articles
        """).fetchone()

        print(f"- Judul kosong: {missing['judul_kosong']}")
        print(f"- URL kosong: {missing['url_kosong']}")
        print(f"- Tanggal publikasi kosong: {missing['tanggal_kosong']}")
        print(f"- Ringkasan kosong: {missing['ringkasan_kosong']}")

        print("\n10 artikel terbaru yang diambil:")
        latest = connection.execute("""
            SELECT source, title, published_at
            FROM articles
            ORDER BY id DESC
            LIMIT 10
        """).fetchall()

        for index, article in enumerate(latest, start=1):
            print(f"\n{index}. [{article['source']}] {article['title']}")
            print(f"   Tanggal publikasi: {article['published_at'] or 'Tidak tersedia'}")


if __name__ == "__main__":
    main()
