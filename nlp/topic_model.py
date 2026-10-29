import json
import sqlite3
from collections import Counter
from pathlib import Path

from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "news.db"
MODEL_DIR = BASE_DIR / "models" / "bertopic"

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
MIN_DOCUMENTS = 5


def column_exists(connection, table_name, column_name):
    columns = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()
    return any(row["name"] == column_name for row in columns)


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database tidak ditemukan: {DB_PATH}")

    # Membaca data dan memastikan kolom hasil tersedia.
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row

        articles = connection.execute("""
            SELECT id, title, processed_text
            FROM articles
            WHERE processed_text IS NOT NULL
              AND TRIM(processed_text) != ''
            ORDER BY id
        """).fetchall()

        if len(articles) < MIN_DOCUMENTS:
            raise ValueError(
                f"Dokumen tidak cukup: {len(articles)}"
            )

        for column, sql_type in [
            ("topic_id", "INTEGER"),
            ("topic_name", "TEXT"),
        ]:
            if not column_exists(connection, "articles", column):
                connection.execute(
                    f"ALTER TABLE articles ADD COLUMN {column} {sql_type}"
                )

        connection.commit()

    ids = [row["id"] for row in articles]
    documents = [row["processed_text"].strip() for row in articles]

    print("=" * 60)
    print("PEMODELAN TOPIK BERITA DENGAN BERTOPIC")
    print("=" * 60)
    print(f"Jumlah dokumen: {len(documents)}")
    print(f"Model embedding: {EMBEDDING_MODEL}")

    print("\nMemuat model embedding...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    print("\nMenghitung representasi teks...")
    embeddings = embedding_model.encode(
        documents,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    topic_model = BERTopic(
        language="multilingual",
        min_topic_size=5,
        calculate_probabilities=False,
        verbose=True,
    )

    print("\nMelatih model dan mengelompokkan berita...")
    topics, _ = topic_model.fit_transform(documents, embeddings)

    if len(topics) != len(ids):
        raise RuntimeError(
            "Jumlah hasil topik tidak sama dengan jumlah dokumen."
        )

    topic_info = topic_model.get_topic_info()
    topic_names = {}

    for _, row in topic_info.iterrows():
        topic_id = int(row["Topic"])

        if topic_id == -1:
            topic_names[topic_id] = "Outlier / belum terkelompok"
        else:
            keywords = topic_model.get_topic(topic_id) or []
            topic_names[topic_id] = ", ".join(
                word for word, _ in keywords[:4]
            ) or "Topik belum bernama"

    # Simpan model sebelum menulis penetapan topik ke database.
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    print("\nMenyimpan model BERTopic...")

    topic_model.save(
        str(MODEL_DIR),
        serialization="safetensors",
        save_ctfidf=True,
        save_embedding_model=EMBEDDING_MODEL,
    )

    # Perbarui hasil dalam satu transaksi database.
    assignments = [
        (
            int(topic_id),
            topic_names.get(int(topic_id), "Topik belum bernama"),
            article_id,
        )
        for article_id, topic_id in zip(ids, topics)
    ]

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("BEGIN")

        connection.executemany("""
            UPDATE articles
            SET topic_id = ?, topic_name = ?
            WHERE id = ?
        """, assignments)

        connection.commit()

        verification = connection.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN topic_id IS NOT NULL
                         THEN 1 ELSE 0 END) AS assigned
            FROM articles
            WHERE processed_text IS NOT NULL
              AND TRIM(processed_text) != ''
        """).fetchone()

        topic_counts = connection.execute("""
            SELECT topic_id, topic_name, COUNT(*)
            FROM articles
            WHERE processed_text IS NOT NULL
              AND TRIM(processed_text) != ''
              AND topic_id IS NOT NULL
            GROUP BY topic_id, topic_name
            ORDER BY COUNT(*) DESC
        """).fetchall()

    counts = Counter(int(topic_id) for topic_id in topics)
    outliers = counts.get(-1, 0)
    normal_topics = len([topic_id for topic_id in counts if topic_id != -1])

    print("\n" + "=" * 60)
    print("HASIL PEMODELAN TOPIK")
    print("=" * 60)
    print(f"Dokumen dianalisis       : {len(documents)}")
    print(f"Dokumen bertopik di model: {len(topics)}")
    print(f"Topik selain outlier     : {normal_topics}")
    print(f"Jumlah dokumen outlier   : {outliers}")
    print(f"Total hasil di database  : {verification[1]} / {verification[0]}")
    print(f"Model disimpan di        : {MODEL_DIR}")

    print("\nDistribusi topik di database:")
    for topic_id, topic_name, count in topic_counts:
        print(f"[{topic_id}] {topic_name}: {count} artikel")

    # Simpan ringkasan hasil untuk evaluasi berikutnya.
    report_path = BASE_DIR / "outputs" / "topic_model_summary.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "embedding_model": EMBEDDING_MODEL,
        "documents_analyzed": len(documents),
        "model_topic_count_excluding_outlier": normal_topics,
        "outlier_count": outliers,
        "database_assigned": verification[1],
        "database_total": verification[0],
        "topic_distribution": [
            {
                "topic_id": int(topic_id),
                "topic_name": topic_name,
                "article_count": count,
            }
            for topic_id, topic_name, count in topic_counts
        ],
    }

    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nRingkasan disimpan di: {report_path}")

    if verification[0] != len(documents) or verification[1] != len(documents):
        print(
            "\nPERINGATAN: jumlah artikel bertopik di database "
            "belum sesuai dengan jumlah dokumen yang diproses."
        )
    else:
        print("\nVALIDASI: semua dokumen yang diproses memiliki hasil topik.")


if __name__ == "__main__":
    main()
