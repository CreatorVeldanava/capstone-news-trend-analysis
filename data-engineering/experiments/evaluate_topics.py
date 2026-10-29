import sqlite3
from pathlib import Path

from gensim.corpora import Dictionary
from gensim.models import CoherenceModel
from sklearn.feature_extraction.text import CountVectorizer

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "news.db"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_FILE = OUTPUT_DIR / "topic_coherence.csv"

TOP_N_WORDS = 10


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database tidak ditemukan: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT topic_id, processed_text
            FROM articles
            WHERE topic_id IS NOT NULL
              AND topic_id != -1
              AND processed_text IS NOT NULL
              AND TRIM(processed_text) != ''
            ORDER BY id
        """).fetchall()

    if not rows:
        raise ValueError("Tidak ada teks bertopik untuk dievaluasi.")

    topic_documents = {}
    all_texts = []

    for topic_id, text in rows:
        words = text.split()
        if not words:
            continue

        topic_documents.setdefault(int(topic_id), []).append(words)
        all_texts.append(words)

    if not all_texts:
        raise ValueError("Semua teks kosong setelah tokenisasi.")

    # Bentuk dictionary dan corpus dari teks yang sudah diproses.
    dictionary = Dictionary(all_texts)
    dictionary.filter_extremes(
        no_below=2,
        no_above=0.95,
        keep_n=10000,
    )

    if len(dictionary) == 0:
        raise ValueError("Kosakata terlalu sedikit untuk evaluasi.")

    # Ekstrak kata kunci topik menggunakan CountVectorizer.
    vectorizer = CountVectorizer(
        tokenizer=str.split,
        token_pattern=None,
        lowercase=False,
        min_df=2,
        max_df=0.95,
        max_features=10000,
    )
    vectorizer.fit([" ".join(words) for words in all_texts])
    feature_names = vectorizer.get_feature_names_out()
    matrix = vectorizer.transform([" ".join(words) for words in all_texts])

    topic_ids = sorted(topic_documents)
    topic_word_lists = []

    for topic_id in topic_ids:
        indices = [
            i for i, (row_topic, _) in enumerate(rows)
            if int(row_topic) == topic_id
        ]

        # Hitung frekuensi kata pada dokumen milik topik ini.
        counts = matrix[indices].sum(axis=0).A1
        ranked_indices = counts.argsort()[::-1]

        words = [
            feature_names[i]
            for i in ranked_indices
            if counts[i] > 0 and feature_names[i] in dictionary.token2id
        ][:TOP_N_WORDS]

        topic_word_lists.append(words)

    # Hitung c_v coherence untuk seluruh topik.
    coherence_model = CoherenceModel(
        topics=topic_word_lists,
        texts=all_texts,
        dictionary=dictionary,
        coherence="c_v",
        processes=1,
    )
    overall_coherence = coherence_model.get_coherence()
    per_topic = coherence_model.get_coherence_per_topic()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    import csv

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "topic_id",
            "jumlah_artikel",
            "kata_kunci_evaluasi",
            "coherence_cv",
        ])

        for topic_id, words, score in zip(
            topic_ids, topic_word_lists, per_topic
        ):
            writer.writerow([
                topic_id,
                len(topic_documents[topic_id]),
                ", ".join(words),
                round(float(score), 4),
            ])

    print("=" * 60)
    print("EVALUASI KOHERENSI TOPIK")
    print("=" * 60)
    print(f"Artikel dievaluasi : {sum(map(len, topic_documents.values()))}")
    print(f"Topik dievaluasi   : {len(topic_ids)}")
    print(f"Skor c_v keseluruhan: {overall_coherence:.4f}")
    print("\nSkor per topik:")

    for topic_id, words, score in zip(
        topic_ids, topic_word_lists, per_topic
    ):
        print(
            f"Topik {topic_id:>2} | c_v={score:.4f} | "
            f"{', '.join(words)}"
        )

    print(f"\nFile hasil: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
