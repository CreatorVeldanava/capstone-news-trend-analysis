import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT / "outputs" / "preprocessing_experiments"
    / "new_articles_protected" / "topic_audit.csv"
)

PREFIX_PATTERN = re.compile(
    r"^\s*(?:VIDEO|FOTO|INFOGRAFIS|GRAFIS|"
    r"ANALISIS|LIVE REPORT)\s*:\s*",
    re.IGNORECASE,
)

def main():
    topics = defaultdict(list)
    prefix_counts = Counter()
    total = 0

    with INPUT.open(
        encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            total += 1
            title = row["title"].strip()

            match = PREFIX_PATTERN.match(title)

            if match:
                prefix = match.group(0).strip().rstrip(":").upper()
                prefix_counts[prefix] += 1
                cleaned_title = PREFIX_PATTERN.sub("", title)
            else:
                prefix = "TANPA PREFIX"
                cleaned_title = title

            topics[int(row["topic_id"])].append(
                (prefix, title, cleaned_title)
            )

    print("=" * 65)
    print("AUDIT PREFIX JUDUL BERITA")
    print("=" * 65)
    print("Total artikel:", total)

    print("\nDistribusi prefix:")
    for prefix, count in prefix_counts.most_common():
        print(f"{prefix:20} {count:4} artikel")

    print("\nPemeriksaan lima topik prioritas:")

    for topic_id in [0, 1, 5, 9, 15]:
        articles = topics.get(topic_id, [])
        counts = Counter(item[0] for item in articles)

        print(f"\nTopic {topic_id} — {len(articles)} artikel")
        for prefix, count in counts.most_common():
            print(f"  {prefix}: {count}")

        print("Contoh judul setelah prefix dihapus:")
        for _, original, cleaned in articles[:5]:
            if original != cleaned:
                print(f"  Sebelum : {original}")
                print(f"  Sesudah : {cleaned}")

    print("\nAudit selesai. Database dan model tidak diubah.")


if __name__ == "__main__":
    main()
