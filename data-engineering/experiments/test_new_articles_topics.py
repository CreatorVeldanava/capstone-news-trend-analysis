import csv
from pathlib import Path
from collections import Counter

from bertopic import BERTopic

BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    BASE_DIR / "outputs" / "preprocessing_experiments"
    / "protected_terms_model" / "model"
)

INPUT_FILE = (
    BASE_DIR / "outputs" / "preprocessing_experiments"
    / "new_articles_protected" / "new_articles.csv"
)

OUTPUT_DIR = (
    BASE_DIR / "outputs" / "preprocessing_experiments"
    / "new_articles_protected"
)

OUTPUT_FILE = OUTPUT_DIR / "topic_predictions.csv"
SUMMARY_FILE = OUTPUT_DIR / "topic_predictions_summary.txt"


def main():
    print("=" * 65)
    print("PENGUJIAN TOPIC PREDICTION - 270 ARTIKEL BARU")
    print("=" * 65)

    # Membaca artikel hasil preprocessing
    with INPUT_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        articles = list(csv.DictReader(file))

    articles = [
        article for article in articles
        if article["processed_text"].strip()
    ]

    if not articles:
        raise ValueError("Tidak ada artikel dengan processed_text.")

    documents = [
        article["processed_text"]
        for article in articles
    ]

    print(f"Artikel yang diuji: {len(documents)}")

    # Memuat model Protected Terms
    print("\nMemuat model BERTopic...")

    topic_model = BERTopic.load(
        str(MODEL_PATH),
        embedding_model=(
            "sentence-transformers/"
            "paraphrase-multilingual-MiniLM-L12-v2"
        ),
    )

    print("Model berhasil dimuat.")

    # Melakukan prediksi tanpa melatih ulang model
    print("\nMelakukan prediksi topik...")

    predicted_topics, probabilities = topic_model.transform(
        documents
    )

    # Mengambil nama dan representasi topik
    topic_info = topic_model.get_topic_info()

    topic_names = {
        int(row["Topic"]): row["Name"]
        for _, row in topic_info.iterrows()
    }

    # Menyiapkan hasil prediksi
    results = []

    for index, article in enumerate(articles):
        topic_id = int(predicted_topics[index])

        results.append({
            "id": article["id"],
            "source": article["source"],
            "title": article["title"],
            "published_at": article["published_at"],
            "topic_id": topic_id,
            "topic_name": topic_names.get(
                topic_id, "Unknown"
            ),
            "url": article["url"],
        })

    # Menyimpan hasil prediksi ke CSV
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(results[0].keys()),
        )
        writer.writeheader()
        writer.writerows(results)

    # Menghitung distribusi topik
    distribution = Counter(
        result["topic_id"] for result in results
    )

    outliers = distribution.get(-1, 0)
    assigned = len(results) - outliers

    summary = [
        "=" * 65,
        "RINGKASAN PREDIKSI TOPIK ARTIKEL BARU",
        "=" * 65,
        f"Jumlah artikel diuji : {len(results)}",
        f"Berhasil masuk topik : {assigned}",
        f"Outlier (-1)         : {outliers}",
        f"Persentase outlier   : {outliers / len(results) * 100:.2f}%",
        "",
        "DISTRIBUSI ARTIKEL PER TOPIK",
        "-" * 65,
    ]

    for topic_id, count in sorted(
        distribution.items(),
        key=lambda item: (-item[1], item[0])
    ):
        name = topic_names.get(topic_id, "Unknown")
        summary.append(
            f"Topic {topic_id:>3} | {count:>3} artikel | {name}"
        )

    summary.extend([
        "",
        f"File prediksi : {OUTPUT_FILE}",
        f"File ringkasan: {SUMMARY_FILE}",
        "",
        "Database tidak diubah.",
        "Model tidak dilatih ulang.",
    ])

    SUMMARY_FILE.write_text(
        "\n".join(summary),
        encoding="utf-8",
    )

    print("\n".join(summary))


if __name__ == "__main__":
    main()