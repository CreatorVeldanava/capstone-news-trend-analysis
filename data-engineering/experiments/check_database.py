import sqlite3
from email.utils import parsedate_to_datetime
from pathlib import Path
from datetime import datetime
from collections import Counter

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "news.db"


def parse_date(value):
    """Mengubah berbagai format tanggal menjadi tanggal kalender."""
    if not value:
        return None

    value = value.strip()

    try:
        return parsedate_to_datetime(value).date()
    except (TypeError, ValueError, OverflowError):
        pass

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).date()
    except (TypeError, ValueError, OverflowError):
        return None

def main():
    if not DB_PATH.exists():
        print("Database tidak ditemukan:", DB_PATH)
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

        print(f"- Judul kosong: {missing['judul_kosong'] or 0}")
        print(f"- URL kosong: {missing['url_kosong'] or 0}")
        print(f"- Tanggal publikasi kosong: {missing['tanggal_kosong'] or 0}")
        print(f"- Ringkasan kosong: {missing['ringkasan_kosong'] or 0}")

        # Pemeriksaan distribusi tanggal publikasi.
        print("\n" + "=" * 65)
        print("ANALISIS DISTRIBUSI TANGGAL")
        print("=" * 65)

        date_rows = connection.execute("""
            SELECT published_at
            FROM articles
            WHERE published_at IS NOT NULL
              AND TRIM(published_at) != ''
        """).fetchall()

        daily_counts = Counter()
        invalid_dates = 0

        for row in date_rows:
            parsed = parse_date(row["published_at"])

            if parsed is None:
                invalid_dates += 1
            else:
                daily_counts[parsed] += 1

        print(f"Artikel dengan tanggal yang diperiksa: {len(date_rows)}")
        print(f"Tanggal yang tidak dapat dibaca: {invalid_dates}")

        if daily_counts:
            first_date = min(daily_counts)
            last_date = max(daily_counts)
            total_days = len(daily_counts)
            total_dated_articles = sum(daily_counts.values())

            print(f"Tanggal paling awal: {first_date}")
            print(f"Tanggal paling akhir: {last_date}")
            print(f"Jumlah hari dengan berita: {total_days}")
            print(f"Total artikel bertanggal valid: {total_dated_articles}")

            print("\nJumlah artikel per hari:")
            for date in sorted(daily_counts):
                print(f"- {date}: {daily_counts[date]} artikel")

            print("\n5 tanggal dengan artikel terbanyak:")
            for date, count in sorted(
                daily_counts.items(),
                key=lambda item: (-item[1], item[0])
            )[:5]:
                print(f"- {date}: {count} artikel")

            print("\n5 tanggal dengan artikel tersedikit:")
            for date, count in sorted(
                daily_counts.items(),
                key=lambda item: (item[1], item[0])
            )[:5]:
                print(f"- {date}: {count} artikel")
        else:
            print("Tidak ada tanggal publikasi valid untuk dianalisis.")

        print("\n10 artikel terbaru berdasarkan ID:")
        latest = connection.execute("""
            SELECT source, title, published_at
            FROM articles
            ORDER BY id DESC
            LIMIT 10
        """).fetchall()

        for index, article in enumerate(latest, start=1):
            print(f"\n{index}. [{article['source']}] {article['title']}")
            print(
                "   Tanggal publikasi: "
                f"{article['published_at'] or 'Tidak tersedia'}"
            )


if __name__ == "__main__":
    main()
