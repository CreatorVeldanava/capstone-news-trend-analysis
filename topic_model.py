
import sqlite3
from pathlib import Path

from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "news.db"

# Model embedding multibahasa untuk teks berita Indonesia.
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


def column_exists(connection, table_name, column_name):
    columns = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return any(column["name"] == column_name for column in columns)


def main():
    if not DB_PATH.exists():
        print("Database tidak ditemukan.")
        return

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row

        articles = connection.execute("""
            SELECT id, title, processed_text
            FROM articles
            WHERE processed_text IS NOT NULL
              AND TRIM(processed_text) != ''
            ORDER BY id
        """).fetchall()

        if len(articles) < 5:
            print("Data belum cukup untuk pengujian model.")
            return

        ids = [article["id"] for article in articles]
        documents = [article["processed_text"] for article in articles]

        if not column_exists(connection, "articles", "topic_id"):
            connection.execute(
                "ALTER TABLE articles ADD COLUMN topic_id INTEGER"
            )

        if not column_exists(connection, "articles", "topic_name"):
            connection.execute(
                "ALTER TABLE articles ADD COLUMN topic_name TEXT"
            )

        connection.commit()

    print("=" * 60)
    print("PEMODELAN TOPIK BERITA DENGAN BERTOPIC")
    print("=" * 60)
    print(f"Jumlah dokumen: {len(documents)}")
    print(f"Model embedding: {EMBEDDING_MODEL}")
    print("\nMemuat model embedding...")
    print("Penggunaan pertama dapat memerlukan unduhan model.")

    embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    print("\nMenghitung representasi teks...")
    embeddings = embedding_model.encode(
        documents,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    topic_model = BERTopic(
        language="multilingual",
        min_topic_size=5,
        calculate_probabilities=False,
        verbose=True
    )

    print("\nMelatih model dan mengelompokkan berita...")
    topics, probabilities = topic_model.fit_transform(
        documents,
        embeddings
    )

    # Mengambil nama topik berdasarkan kata-kata representatif.
    topic_info = topic_model.get_topic_info()
    topic_names = {}

    for _, row in topic_info.iterrows():
        topic_id = int(row["Topic"])

        if topic_id == -1:
            topic_names[topic_id] = "Outlier / belum terkelompok"
        else:
            keywords = topic_model.get_topic(topic_id) or []
            keyword_text = ", ".join(word for word, _ in keywords[:4])
            topic_names[topic_id] = keyword_text or "Topik belum bernama"

    with sqlite3.connect(DB_PATH) as connection:
        for article_id, topic_id in zip(ids, topics):
            topic_id = int(topic_id)
            topic_name = topic_names.get(
                topic_id,
                "Topik belum bernama"
            )

            connection.execute("""
                UPDATE articles
                SET topic_id = ?, topic_name = ?
                WHERE id = ?
            """, (topic_id, topic_name, article_id))

        connection.commit()

    # Menyimpan model agar bisa digunakan kembali.
    model_dir = BASE_DIR / "models" / "bertopic"
    model_dir.mkdir(parents=True, exist_ok=True)
    topic_model.save(
        str(model_dir),
        serialization="safetensors",
        save_ctfidf=True,
        save_embedding_model=EMBEDDING_MODEL
    )

    print("\n" + "=" * 60)
    print("HASIL PEMODELAN TOPIK")
    print("=" * 60)

    display_columns = [
        column for column in ["Topic", "Count", "Name"]
        if column in topic_info.columns
    ]

    print(topic_info[display_columns].to_string(index=False))
    print(f"\nTotal dokumen dianalisis: {len(documents)}")
    print(f"Jumlah topik termasuk outlier: {len(topic_info)}")
    print(f"Model disimpan di: {model_dir}")
    print("Hasil topik disimpan ke database.")


if __name__ == "__main__":
    main()
