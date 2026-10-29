import csv
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
CSV_PATH = (
    BASE_DIR
    / "outputs"
    / "topic_experiment"
    / "experimental_assignments.csv"
)

if not CSV_PATH.exists():
    raise FileNotFoundError(f"File hasil tidak ditemukan: {CSV_PATH}")

topics = defaultdict(list)

with CSV_PATH.open(
    "r", newline="", encoding="utf-8-sig"
) as file:
    reader = csv.DictReader(file)

    for row in reader:
        topics[row["topic_id"]].append(row)

print("=" * 75)
print("PEMERIKSAAN ISI TOPIK EKSPERIMEN")
print("=" * 75)

for topic_id, articles in sorted(
    topics.items(),
    key=lambda item: (
        item[0] == "-1",
        -len(item[1]),
    ),
):
    name = articles[0]["topic_name"]
    print(f"\nTopik {topic_id} | {name}")
    print(f"Jumlah artikel: {len(articles)}")

    for article in articles[:5]:
        title = article["title"].strip()
        print(f"  - {title}")
