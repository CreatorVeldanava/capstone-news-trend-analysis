import csv
import json
import re
from collections import Counter
from pathlib import Path

from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    BASE_DIR
    / "outputs"
    / "preprocessing_experiments"
    / "protected_terms.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "outputs"
    / "preprocessing_experiments"
    / "protected_terms_no_prefix_model"
)

MODEL_DIR = OUTPUT_DIR / "model"

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
MIN_TOPIC_SIZE = 5

# Menghapus awalan format jika muncul di awal teks.
PREFIX_PATTERN = re.compile(
    r"^\s*(?:VIDEO|FOTO|INFOGRAFIS|GRAFIS)\s*:\s*",
    re.IGNORECASE,
)


def load_documents():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"File tidak ditemukan: {INPUT_FILE}"
        )

    with INPUT_FILE.open(
        "r", newline="", encoding="utf-8-sig"
    ) as file:
        rows = list(csv.DictReader(file))

    ids = [int(row["id"]) for row in rows]
    titles = [row["title"] or "" for row in rows]

    documents = []
    removed_prefix_count = 0

    for row in rows:
        text = (row["processed_text"] or "").strip()

        # Hilangkan prefix hanya jika benar-benar ada.
        cleaned_text, count = PREFIX_PATTERN.subn("", text, count=1)

        if count:
            removed_prefix_count += 1

        cleaned_text = cleaned_text.strip()

        if not cleaned_text:
            raise ValueError(
                f"Teks kosong setelah penghapusan prefix. ID: {row['id']}"
            )

        documents.append(cleaned_text)

    if len(ids) != len(set(ids)):
        raise ValueError("Ditemukan ID artikel duplikat.")

    if not documents:
        raise ValueError("Tidak ada dokumen untuk diproses.")

    return ids, titles, documents, removed_prefix_count


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ids, titles, documents, removed_count = load_documents()

    print("=" * 65)
    print("EKSPERIMEN BERTOPIC: PROTECTED TERMS TANPA PREFIX")
    print("=" * 65)
    print(f"Jumlah dokumen       : {len(documents)}")
    print(f"Prefix yang dihapus  : {removed_count}")
    print(f"Embedding            : {EMBEDDING_MODEL}")
    print(f"Min topic size       : {MIN_TOPIC_SIZE}")
    print("Database             : Tidak digunakan")
    print("Model utama          : Tidak diubah")

    print("\nMemuat model embedding...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    print("\nMenghitung embeddings...")
    embeddings = embedding_model.encode(
        documents,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    topic_model = BERTopic(
        language="multilingual",
        min_topic_size=MIN_TOPIC_SIZE,
        calculate_probabilities=False,
        verbose=True,
    )

    print("\nMelatih BERTopic...")
    topics, _ = topic_model.fit_transform(
        documents,
        embeddings,
    )

    if len(topics) != len(ids):
        raise RuntimeError(
            "Jumlah prediksi tidak sama dengan jumlah dokumen."
        )

    counts = Counter(int(topic) for topic in topics)

    topic_names = {}
    for _, row in topic_model.get_topic_info().iterrows():
        topic_id = int(row["Topic"])

        if topic_id == -1:
            topic_names[topic_id] = "Outlier"
        else:
            keywords = topic_model.get_topic(topic_id) or []
            topic_names[topic_id] = ", ".join(
                word for word, _ in keywords[:5]
            )

    assignments_path = OUTPUT_DIR / "assignments.csv"

    with assignments_path.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.writer(file)
        writer.writerow([
            "id",
            "title",
            "topic_id",
            "topic_name",
            "processed_text_without_prefix",
        ])

        for article_id, title, topic_id, document in zip(
            ids, titles, topics, documents
        ):
            topic_id = int(topic_id)
            writer.writerow([
                article_id,
                title,
                topic_id,
                topic_names.get(topic_id, "Topik belum bernama"),
                document,
            ])

    print("\nMenyimpan model eksperimen...")
    topic_model.save(
        str(MODEL_DIR),
        serialization="safetensors",
        save_ctfidf=True,
        save_embedding_model=EMBEDDING_MODEL,
    )

    outliers = counts.get(-1, 0)
    normal_topics = sum(
        1 for topic_id in counts if topic_id != -1
    )

    summary = {
        "experiment": "protected_terms_no_prefix",
        "preprocessing": "protected_terms_without_video_foto_prefix",
        "embedding_model": EMBEDDING_MODEL,
        "min_topic_size": MIN_TOPIC_SIZE,
        "documents": len(documents),
        "removed_prefix_count": removed_count,
        "normal_topics": normal_topics,
        "outliers": outliers,
        "outlier_percentage": round(
            outliers / len(documents) * 100, 2
        ),
        "topic_distribution": [
            {
                "topic_id": int(topic_id),
                "article_count": int(count),
                "topic_name": topic_names.get(
                    int(topic_id), "Topik belum bernama"
                ),
            }
            for topic_id, count in sorted(counts.items())
        ],
    }

    summary_path = OUTPUT_DIR / "summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n" + "=" * 65)
    print("HASIL EKSPERIMEN")
    print("=" * 65)
    print(f"Dokumen              : {len(documents)}")
    print(f"Prefix dihapus       : {removed_count}")
    print(f"Jumlah topik         : {normal_topics}")
    print(f"Jumlah outlier       : {outliers}")
    print(f"Persentase outlier   : {summary['outlier_percentage']}%")
    print(f"Assignments          : {assignments_path}")
    print(f"Model                 : {MODEL_DIR}")
    print(f"Ringkasan             : {summary_path}")
    print("\nDatabase dan model utama tidak diubah.")


if __name__ == "__main__":
    main()
