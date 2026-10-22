
import csv
import sqlite3
from collections import Counter, defaultdict
from datetime import timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "news.db"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_FILE = OUTPUT_DIR / "trend_daily.csv"


def parse_published_date(value):
    """Mengubah tanggal RSS menjadi tanggal YYYY-MM-DD."""
    if not value:
        return None

    try:
        dt = parsedate_to_datetime(value)

        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc)

        return dt.date().isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def main():
    if not DB_PATH.exists():
        print("Database tidak ditemukan:", DB_PATH)
        return

    with sqlite3.connect(DB_PATH) as connection:
        articles = connection.execute("""
            SELECT id, title, published_at, topic_id, topic_name
            FROM articles
            WHERE topic_id IS NOT NULL
            ORDER BY id
        """).fetchall()

    daily_counts = Counter()
    topic_names = {}
    invalid_dates = 0
    valid_dates = 0

    for article_id, title, published_at, topic_id, topic_name in articles:
        article_date = parse_published_date(published_at)

        if article_date is None:
            invalid_dates += 1
            continue

        valid_dates += 1
        topic_id = int(topic_id)
        topic_names[topic_id] = topic_name or "Tidak diketahui"
        daily_counts[(article_date, topic_id)] += 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow([
            "tanggal",
            "topic_id",
            "topic_name",
            "jumlah_artikel",
        ])

        for (article_date, topic_id), count in sorted(daily_counts.items()):
            writer.writerow([
                article_date,
                topic_id,
                topic_names.get(topic_id, "Tidak diketahui"),
                count,
            ])

    dates = sorted({date for date, _ in daily_counts})

    print("=" * 60)
    print("ANALISIS TREN BERITA HARIAN")
    print("=" * 60)
    print(f"Artikel dengan hasil topik : {len(articles)}")
    print(f"Tanggal berhasil dibaca    : {valid_dates}")
    print(f"Tanggal tidak valid        : {invalid_dates}")
    print(f"Jumlah hari berbeda        : {len(dates)}")

    if dates:
        print(f"Tanggal paling awal        : {dates[0]}")
        print(f"Tanggal paling akhir       : {dates[-1]}")

    print("\nJumlah artikel per hari:")
    daily_totals = Counter()

    for (article_date, topic_id), count in daily_counts.items():
        daily_totals[article_date] += count

    for article_date in sorted(daily_totals):
        print(f"{article_date}: {daily_totals[article_date]} artikel")

    print("\nFile hasil disimpan di:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()
