import csv
import sqlite3
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "news.db"

ASSIGNMENT_PATH = (
    BASE_DIR / "outputs"
    / "parameter_experiments"
    / "experiment_B"
    / "assignments.csv"
)

OUTPUT_PATH = (
    BASE_DIR / "outputs"
    / "parameter_experiments"
    / "experiment_B"
    / "topic_inspection.txt"
)


def main():
    grouped = defaultdict(list)

    with ASSIGNMENT_PATH.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            topic_id = int(row["topic_id"])

            if topic_id != -1:
                grouped[topic_id].append(str(row["id"]))

    results = []

    with sqlite3.connect(DB_PATH) as connection:
        for topic_id in sorted(grouped):
            article_ids = grouped[topic_id]

            placeholders = ",".join(
                "?" for _ in article_ids
            )

            rows = connection.execute(
                f"""
                SELECT title, source
                FROM articles
                WHERE id IN ({placeholders})
                ORDER BY published_at DESC
                LIMIT 10
                """,
                article_ids,
            ).fetchall()

            results.append(
                f"\n{'=' * 65}\n"
                f"TOPIK {topic_id} "
                f"({len(article_ids)} artikel)\n"
                f"{'=' * 65}\n"
            )

            for index, (title, source) in enumerate(rows, 1):
                results.append(
                    f"{index}. [{source}] {title}\n"
                )

    OUTPUT_PATH.write_text(
        "".join(results),
        encoding="utf-8",
    )

    print("Pemeriksaan topik selesai.")
    print(f"Jumlah topik: {len(grouped)}")
    print(f"Hasil disimpan di: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
