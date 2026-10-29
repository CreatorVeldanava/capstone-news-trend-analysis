import csv
import json
import sqlite3
from collections import Counter
from pathlib import Path

from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from hdbscan import HDBSCAN

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "news.db"

OUTPUT_DIR = BASE_DIR / "outputs" / "topic_experiment_cleaned"
MODEL_DIR = BASE_DIR / "models" / "bertopic_cleaned_experiment"

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
MIN_DOCUMENTS = 5

EXTRA_STOPWORDS = {
    "video", "viral", "simak", "berikut", "foto",
    "baca", "selengkapnya", "detik", "antaranews"
}


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database tidak ditemukan: {DB_PATH}")

    # Hanya membaca data; tidak mengubah database utama.
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute("""
            SELECT id, source, title, published_at, cleaned_text
            FROM articles
            WHERE cleaned_text IS NOT NULL
              AND TRIM(cleaned_text) != ''
            ORDER BY id
        """).fetchall()

    if len(rows) < MIN_DOCUMENTS:
        raise ValueError(f"Dokumen tidak cukup: {len(rows)}")

    ids = [row["id"] for row in rows]
    documents = [row["cleaned_text"].strip() for row in rows]

    print("=" * 65)
    print("EKSPERIMEN BERTopic DENGAN CLEANED_TEXT")
    print("=" * 65)
    print(f"Jumlah dokumen: {len(documents)}")
    print(f"Model embedding: {EMBEDDING_MODEL}")
    print("HDBSCAN: min_cluster_size=10, min_samples=5")

    print("\nMemuat model embedding...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    print("\nMenghitung embedding teks...")
    embeddings = embedding_model.encode(
        documents,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    vectorizer_model = CountVectorizer(
        stop_words=list(EXTRA_STOPWORDS),
        ngram_range=(1, 2),
        min_df=2,
    )

    hdbscan_model = HDBSCAN(
        min_cluster_size=10,
        min_samples=5,
        metric="euclidean",
        cluster_selection_method="eom",
        prediction_data=True,
    )

    topic_model = BERTopic(
        language="multilingual",
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        calculate_probabilities=False,
        verbose=True,
    )

    print("\nMelatih model eksperimen...")
    topics, _ = topic_model.fit_transform(documents, embeddings)

    if len(topics) != len(ids):
        raise RuntimeError("Jumlah hasil topik tidak sesuai.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.parent.mkdir(parents=True, exist_ok=True)

    print("\nMenyimpan model eksperimen...")
    topic_model.save(
        str(MODEL_DIR),
        serialization="safetensors",
        save_ctfidf=True,
        save_embedding_model=EMBEDDING_MODEL,
    )

    topic_names = {}

    for _, row in topic_model.get_topic_info().iterrows():
        topic_id = int(row["Topic"])

        if topic_id == -1:
            topic_names[topic_id] = "Outlier / belum terkelompok"
        else:
            keywords = topic_model.get_topic(topic_id) or []
            topic_names[topic_id] = ", ".join(
                word for word, _ in keywords[:5]
            ) or "Topik belum bernama"

    assignment_path = OUTPUT_DIR / "experimental_assignments.csv"

    with assignment_path.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.writer(file)
        writer.writerow([
            "id", "source", "title", "published_at",
            "topic_id", "topic_name"
        ])

        for row, topic_id in zip(rows, topics):
            topic_id = int(topic_id)
            writer.writerow([
                row["id"],
                row["source"],
                row["title"],
                row["published_at"],
                topic_id,
                topic_names.get(topic_id, "Topik belum bernama"),
            ])

    counts = Counter(int(topic_id) for topic_id in topics)
    outliers = counts.get(-1, 0)
    normal_topics = sum(1 for topic_id in counts if topic_id != -1)

    summary = {
        "experiment": "cleaned_text, min_cluster_size=10, min_samples=5",
        "embedding_model": EMBEDDING_MODEL,
        "documents_analyzed": len(documents),
        "normal_topic_count": normal_topics,
        "outlier_count": outliers,
        "outlier_percentage": round(
            outliers / len(documents) * 100, 2
        ),
        "topic_distribution": [
            {
                "topic_id": int(topic_id),
                "topic_name": topic_names.get(
                    int(topic_id), "Topik belum bernama"
                ),
                "article_count": count,
            }
            for topic_id, count in sorted(
                counts.items(), key=lambda item: item[1], reverse=True
            )
        ],
    }

    summary_path = OUTPUT_DIR / "experimental_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n" + "=" * 65)
    print("HASIL EKSPERIMEN CLEANED_TEXT")
    print("=" * 65)
    print(f"Dokumen dianalisis : {len(documents)}")
    print(f"Topik non-outlier  : {normal_topics}")
    print(f"Jumlah outlier     : {outliers}")
    print(f"Persentase outlier : {summary['outlier_percentage']}%")
    print(f"CSV hasil          : {assignment_path}")
    print(f"Ringkasan          : {summary_path}")
    print(f"Model eksperimen   : {MODEL_DIR}")
    print("\nDatabase utama dan model awal tidak diubah.")


if __name__ == "__main__":
    main()
