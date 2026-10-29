import csv
import sqlite3
from collections import Counter
from datetime import timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "news.db"
OUTPUT_DIR = BASE_DIR / "outputs"

DAILY_FILE = OUTPUT_DIR / "trend_daily.csv"
TOPIC_FILE = OUTPUT_DIR / "trend_topic_summary.csv"

# Zona waktu Indonesia bagian barat.
WIB = timezone(timedelta(hours=7))


def parse_published_date(value):
    """Mengubah tanggal RSS menjadi tanggal lokal Indonesia (WIB)."""
    if not value:
        return None

    try:
        dt = parsedate_to_datetime(value)

        if dt.tzinfo is None:
            return None

        return dt.astimezone(WIB).date().isoformat()

    except (TypeError, ValueError, OverflowError):
        return None


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database tidak ditemukan: {DB_PATH}"
        )

    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute("""
            SELECT source, title, published_at, topic_id, topic_name
            FROM articles
            WHERE topic_id IS NOT NULL
            ORDER BY id
        """).fetchall()

    if not rows:
        raise ValueError(
            "Belum ada artikel yang memiliki hasil pemodelan topik."
        )

    daily_counts = Counter()
    topic_counts = Counter()
    topic_names = {}
    source_counts = Counter()
    invalid_dates = 0
    outlier_counts = Counter()

    for source, title, published_at, topic_id, topic_name in rows:
        article_date = parse_published_date(published_at)

        if article_date is None:
            invalid_dates += 1
            continue

        topic_id = int(topic_id)
        name = topic_name or "Topik belum bernama"

        daily_counts[(article_date, topic_id, name)] += 1
        topic_counts[(topic_id, name)] += 1
        topic_names[topic_id] = name
        source_counts[source] += 1

        if topic_id == -1:
            outlier_counts[article_date] += 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # File 1: jumlah artikel per tanggal dan topik.
    with open(
        DAILY_FILE, "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.writer(file)
        writer.writerow([
            "tanggal",
            "topic_id",
            "topic_name",
            "jumlah_artikel",
        ])

        for (date, topic_id, name), count in sorted(
            daily_counts.items()
        ):
            writer.writerow([date, topic_id, name, count])

    # File 2: ringkasan jumlah artikel per topik.
    with open(
        TOPIC_FILE, "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.writer(file)
        writer.writerow([
            "topic_id",
            "topic_name",
            "total_artikel",
            "persentase_dari_data_valid",
        ])

        valid_total = sum(topic_counts.values())

        for (topic_id, name), count in sorted(
            topic_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            percentage = (
                round(count / valid_total * 100, 2)
                if valid_total else 0
            )
            writer.writerow([
                topic_id, name, count, percentage
            ])

    daily_totals = Counter()

    for (date, topic_id, name), count in daily_counts.items():
        daily_totals[date] += count

    print("=" * 60)
    print("ANALISIS TREN BERITA HARIAN")
    print("=" * 60)
    print(f"Artikel dengan hasil topik : {len(rows)}")
    print(f"Tanggal valid              : {len(rows) - invalid_dates}")
    print(f"Tanggal tidak valid        : {invalid_dates}")
    print(f"Jumlah hari berbeda        : {len(daily_totals)}")

    if daily_totals:
        dates = sorted(daily_totals)
        print(f"Tanggal paling awal        : {dates[0]}")
        print(f"Tanggal paling akhir       : {dates[-1]}")

    print("\nJumlah artikel per hari:")
    for date, count in sorted(daily_totals.items()):
        print(f"{date}: {count} artikel")

    print("\nTopik dengan artikel terbanyak:")
    for (topic_id, name), count in topic_counts.most_common(10):
        print(f"[{topic_id}] {name}: {count} artikel")

    print("\nFile hasil:")
    print(DAILY_FILE)
    print(TOPIC_FILE)


if __name__ == "__main__":
    main()
