import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    BASE_DIR / "outputs" / "preprocessing_experiments"
    / "new_articles_protected" / "topic_predictions.csv"
)

OUTPUT_DIR = (
    BASE_DIR / "outputs" / "preprocessing_experiments"
    / "new_articles_protected"
)

OUTPUT_FILE = OUTPUT_DIR / "topic_audit.csv"


def main():
    with INPUT_FILE.open(
        encoding="utf-8-sig",
        newline=""
    ) as file:
        predictions = list(csv.DictReader(file))

    groups = defaultdict(list)

    for article in predictions:
        topic_id = int(article["topic_id"])

        if topic_id != -1:
            groups[topic_id].append(article)

    results = []

    for topic_id, articles in sorted(groups.items()):
        for article in articles:
            results.append({
                "topic_id": topic_id,
                "topic_name": article["topic_name"],
                "article_count_in_topic": len(articles),
                "article_id": article["id"],
                "title": article["title"],
                "source": article["source"],
                "published_at": article["published_at"],
                "url": article["url"],
            })

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(results[0].keys())
        )
        writer.writeheader()
        writer.writerows(results)

    print("=" * 60)
    print("AUDIT KUALITAS PREDIKSI TOPIK")
    print("=" * 60)
    print("Jumlah topik diperiksa :", len(groups))
    print("Jumlah artikel diperiksa:", len(results))
    print("File hasil:", OUTPUT_FILE)

    print("\nDISTRIBUSI TOPIK:")
    for topic_id, articles in sorted(
        groups.items(),
        key=lambda item: -len(item[1])
    ):
        print(
            f"Topic {topic_id:>2} | "
            f"{len(articles):>3} artikel | "
            f"{articles[0]['topic_name']}"
        )


if __name__ == "__main__":
    main()