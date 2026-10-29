import csv
import json
import sqlite3
from hdbscan import HDBSCAN
from collections import Counter
from pathlib import Path

from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "news.db"
OUTPUT_DIR = BASE_DIR / "outputs" / "topic_experiment"
MODEL_DIR = BASE_DIR / "models" / "bertopic_experiment"

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
MIN_DOCUMENTS = 5

# Menghapus kata yang menunjukkan format berita, bukan tema.
EXTRA_STOPWORDS = {
    "video", "viral", "simak", "berikut", "foto",
    "baca", "selengkapnya", "detik", "antaranews"
}


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database tidak ditemukan: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("""
            SELECT id, source, title, published_at, processed_text
            FROM articles
            WHERE processed_text IS NOT NULL
              AND TRIM(processed_text) != ''
            ORDER BY id
        """).fetchall()

    if len(rows) < MIN_DOCUMENTS:
        raise ValueError(f"Dokumen tidak cukup: {len(rows)}")

    ids = [row["id"] for row in rows]

    # Untuk eksperimen awal, gunakan teks yang sudah tersedia.
    # Stopwords tambahan hanya diterapkan pada representasi topik,
    # bukan mengubah teks di database.
    documents = [row["processed_text"].strip() for row in rows]

    print("=" * 60)
    print("EKSPERIMEN BERTOPIC - TERPISAH DARI MODEL UTAMA")
    print("=" * 60)
    print(f"Dokumen: {len(documents)}")
    print(f"Embedding: {EMBEDDING_MODEL}")
    print("Konfigurasi: min_topic_size=10, min_samples=5")

    embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    embeddings = embedding_model.encode(
        documents,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    # Konfigurasi eksperimen: topik minimum lebih besar.
    # Stopwords tambahan membantu membersihkan kata format pada
    # representasi topik, tanpa mengubah isi database utama.
    from sklearn.feature_extraction.text import CountVectorizer

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
        calculate_probabilities=False,
        vectorizer_model=vectorizer_model,
        verbose=True,
    )

    topics, _ = topic_model.fit_transform(documents, embeddings)

    if len(topics) != len(ids):
        raise RuntimeError("Jumlah penetapan topik tidak sesuai.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.parent.mkdir(parents=True, exist_ok=True)

    # Simpan model eksperimen di direktori berbeda.
    topic_model.save(
        str(MODEL_DIR),
        serialization="safetensors",
        save_ctfidf=True,
        save_embedding_model=EMBEDDING_MODEL,
    )

    topic_info = topic_model.get_topic_info()
    topic_names = {}

    for _, row in topic_info.iterrows():
        topic_id = int(row["Topic"])

        if topic_id == -1:
            topic_names[topic_id] = "Outlier / belum terkelompok"
        else:
            words = topic_model.get_topic(topic_id) or []
            topic_names[topic_id] = ", ".join(
                word for word, _ in words[:5]
            )

    # Simpan penetapan hasil eksperimen sebagai CSV terpisah.
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
        "experiment": "BERTopic min_topic_size=10",
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

    print("\n" + "=" * 60)
    print("HASIL EKSPERIMEN")
    print("=" * 60)
    print(f"Dokumen dianalisis : {len(documents)}")
    print(f"Topik non-outlier  : {normal_topics}")
    print(f"Jumlah outlier     : {outliers}")
    print(f"Persentase outlier : {summary['outlier_percentage']}%")
    print(f"CSV hasil          : {assignment_path}")
    print(f"Ringkasan          : {summary_path}")
    print(f"Model eksperimen   : {MODEL_DIR}")
    print("\nDatabase dan model utama tidak diubah.")


if __name__ == "__main__":
    main()
