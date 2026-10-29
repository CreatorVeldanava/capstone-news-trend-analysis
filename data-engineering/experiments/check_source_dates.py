import sqlite3
from collections import Counter, defaultdict
from datetime import timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "news.db"

def to_local_date(value):
    if not value:
        return None

    try:
        dt = parsedate_to_datetime(value)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # Konversi ke WIB (UTC+7).
        from datetime import timedelta
        dt = dt.astimezone(timezone(timedelta(hours=7)))

        return dt.date().isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


with sqlite3.connect(DB_PATH) as connection:
    rows = connection.execute("""
        SELECT source, published_at
        FROM articles
    """).fetchall()

source_totals = Counter()
source_dates = defaultdict(Counter)

for source, published_at in rows:
    date = to_local_date(published_at)

    if date is None:
        continue

    source_totals[source] += 1
    source_dates[source][date] += 1

print("=" * 60)
print("SEBARAN TANGGAL BERITA PER SUMBER (WIB)")
print("=" * 60)

for source in sorted(source_totals):
    print(f"\n{source}: {source_totals[source]} artikel")

    for date, count in sorted(source_dates[source].items()):
        print(f"  {date}: {count} artikel")

print("\nPemeriksaan selesai. Database tidak diubah.")
