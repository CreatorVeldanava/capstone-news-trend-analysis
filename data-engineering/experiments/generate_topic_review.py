import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT / "outputs" / "preprocessing_experiments"
    / "new_articles_protected" / "topic_audit.csv"
)

OUTPUT = (
    ROOT / "outputs" / "preprocessing_experiments"
    / "new_articles_protected" / "topic_review_report.md"
)


def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {INPUT}")

    topics = defaultdict(list)

    with INPUT.open(
        encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            topics[int(row["topic_id"])].append(row)

    lines = [
        "# LAPORAN PEMERIKSAAN TOPIK BERTopic",
        "",
        f"Jumlah topik: {len(topics)}",
        f"Jumlah artikel: {sum(len(v) for v in topics.values())}",
        "",
        "Catatan: pemeriksaan berdasarkan judul, bukan isi lengkap artikel.",
        "",
    ]

    for topic_id in sorted(topics):
        articles = topics[topic_id]
        topic_name = articles[0]["topic_name"]

        lines.extend([
            f"## Topic {topic_id} — {len(articles)} artikel",
            f"Nama model: {topic_name}",
            "",
        ])

        for number, article in enumerate(articles, start=1):
            lines.append(
                f"{number}. {article['title']} "
                f"({article['source']}, {article['published_at']})"
            )

        lines.append("")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")

    print("Laporan berhasil dibuat.")
    print(f"Jumlah topik : {len(topics)}")
    print(f"Jumlah artikel: {sum(len(v) for v in topics.values())}")
    print(f"Lokasi: {OUTPUT}")


if __name__ == "__main__":
    main()
