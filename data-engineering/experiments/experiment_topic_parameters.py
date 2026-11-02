import csv
import json
import sqlite3
from collections import Counter
from pathlib import Path

from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "news.db"
OUTPUT_DIR = BASE_DIR / "outputs" / "parameter_experiments"

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

EXPERIMENTS = [
    {"name": "experiment_A", "min_topic_size": 10, "min_samples": 5},
    {"name": "experiment_B", "min_topic_size": 15, "min_samples": 5},
    {"name": "experiment_C", "min_topic_size": 20, "min_samples": 5},
]


def load_documents():
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute("""
            SELECT id, processed_text
            FROM articles
            WHERE processed_text IS NOT NULL
              AND TRIM(processed_text) != ''
            ORDER BY id
        """).fetchall()

    ids = [row[0] for row in rows]
    documents = [row[1].strip() for row in rows]

    return ids, documents


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ids, documents = load_documents()

    print("=" * 60)
    print("EKSPERIMEN PARAMETER BERTOPIC")
    print("=" * 60)
    print(f"Jumlah dokumen: {len(documents)}")

    print("\nMemuat embedding model...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    print("\nMenghitung embeddings...")
    embeddings = embedding_model.encode(
        documents,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    summaries = []

    for config in EXPERIMENTS:
        name = config["name"]
        min_topic_size = config["min_topic_size"]
        min_samples = config["min_samples"]

        print("\n" + "=" * 60)
        print(f"Menjalankan {name}")
        print(f"min_topic_size: {min_topic_size}")
        print(f"min_samples   : {min_samples}")
        print("=" * 60)

        topic_model = BERTopic(
            language="multilingual",
            min_topic_size=min_topic_size,
            hdbscan_model=None,
            calculate_probabilities=False,
            verbose=True,
        )

        # Atur min_samples secara eksplisit pada HDBSCAN.
        from hdbscan import HDBSCAN

        topic_model.hdbscan_model = HDBSCAN(
            min_cluster_size=min_topic_size,
            min_samples=min_samples,
            metric="euclidean",
            cluster_selection_method="eom",
            prediction_data=True,
        )

        topics, _ = topic_model.fit_transform(
            documents,
            embeddings,
        )

        counts = Counter(int(topic) for topic in topics)
        outliers = counts.get(-1, 0)
        normal_topics = len([
            topic for topic in counts if topic != -1
        ])

        experiment_dir = OUTPUT_DIR / name
        experiment_dir.mkdir(parents=True, exist_ok=True)

        assignments_path = experiment_dir / "assignments.csv"

        with assignments_path.open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.writer(file)
            writer.writerow(["id", "topic_id"])

            for article_id, topic_id in zip(ids, topics):
                writer.writerow([article_id, int(topic_id)])

        summary = {
            "experiment": name,
            "min_topic_size": min_topic_size,
            "min_samples": min_samples,
            "embedding_model": EMBEDDING_MODEL,
            "documents": len(documents),
            "normal_topics": normal_topics,
            "outliers": outliers,
            "outlier_percentage": round(
                outliers / len(documents) * 100, 2
            ),
            "topic_distribution": [
                {
                    "topic_id": int(topic_id),
                    "article_count": int(count),
                }
                for topic_id, count in sorted(counts.items())
            ],
        }

        summary_path = experiment_dir / "summary.json"
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Simpan model masing-masing eksperimen secara terpisah.
        topic_model.save(
            str(experiment_dir / "model"),
            serialization="safetensors",
            save_ctfidf=True,
            save_embedding_model=EMBEDDING_MODEL,
        )

        summaries.append(summary)

        print(f"\nJumlah topik : {normal_topics}")
        print(f"Outlier      : {outliers}")
        print(
            f"Persentase   : {summary['outlier_percentage']}%"
        )
        print(f"Hasil        : {experiment_dir}")

    comparison_path = OUTPUT_DIR / "parameter_comparison.json"
    comparison_path.write_text(
        json.dumps(summaries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n" + "=" * 60)
    print("SEMUA EKSPERIMEN SELESAI")
    print("=" * 60)

    for summary in summaries:
        print(
            f"{summary['experiment']} | "
            f"Topik: {summary['normal_topics']} | "
            f"Outlier: {summary['outliers']} | "
            f"Outlier: {summary['outlier_percentage']}%"
        )

    print(f"\nRingkasan: {comparison_path}")


if __name__ == "__main__":
    main()
