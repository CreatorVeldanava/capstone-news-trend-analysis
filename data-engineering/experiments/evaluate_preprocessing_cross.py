import csv
import json
import sqlite3
from pathlib import Path

from gensim.corpora import Dictionary
from gensim.models import CoherenceModel
from sklearn.feature_extraction.text import CountVectorizer

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "news.db"

PROTECTED_DIR = (
    BASE_DIR / "outputs"
    / "preprocessing_experiments"
)

ASSIGNMENT_FILE = (
    PROTECTED_DIR / "protected_terms_model"
    / "assignments.csv"
)

OUTPUT_DIR = PROTECTED_DIR / "cross_evaluation"
TOP_N_WORDS = 10


def load_database():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT id, processed_text, topic_id
            FROM articles
            WHERE processed_text IS NOT NULL
              AND TRIM(processed_text) != ''
            ORDER BY id
        """).fetchall()

    documents = {}
    assignments = {}

    for article_id, text, topic_id in rows:
        article_id = str(article_id)
        words = text.split()

        if words:
            documents[article_id] = words

        if topic_id is not None:
            assignments[article_id] = int(topic_id)

    return documents, assignments


def load_protected():
    assignments = {}
    documents = {}

    with ASSIGNMENT_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        for row in csv.DictReader(file):
            article_id = str(row["id"])
            assignments[article_id] = int(row["topic_id"])
            documents[article_id] = row["processed_text"].split()

    return documents, assignments


def build_topic_words(
    assignments,
    model_documents,
    reference_documents,
    dictionary,
):
    vectorizer = CountVectorizer(
        tokenizer=str.split,
        token_pattern=None,
        lowercase=False,
        min_df=2,
        max_df=0.95,
        max_features=10000,
    )

    reference_ids = list(reference_documents.keys())
    reference_texts = [
        " ".join(reference_documents[key])
        for key in reference_ids
    ]

    matrix = vectorizer.fit_transform(reference_texts)
    feature_names = vectorizer.get_feature_names_out()

    id_to_index = {
        article_id: index
        for index, article_id in enumerate(reference_ids)
    }

    grouped = {}

    for article_id, topic_id in assignments.items():
        if topic_id == -1:
            continue

        if article_id not in model_documents:
            continue

        if article_id not in id_to_index:
            continue

        grouped.setdefault(topic_id, []).append(article_id)

    topic_ids = []
    topic_words = []
    topic_counts = []

    for topic_id in sorted(grouped):
        article_ids = grouped[topic_id]

        texts = [
            " ".join(model_documents[article_id])
            for article_id in article_ids
        ]

        indices = [
            id_to_index[article_id]
            for article_id in article_ids
        ]

        # Ambil kata kunci dari teks model yang sedang dievaluasi.
        # Matriks referensi hanya menyediakan kosakata bersama.
        model_vectorizer = CountVectorizer(
            tokenizer=str.split,
            token_pattern=None,
            lowercase=False,
            min_df=1,
        )

        model_matrix = model_vectorizer.fit_transform(texts)
        model_features = model_vectorizer.get_feature_names_out()
        model_counts = model_matrix.sum(axis=0).A1

        # Urutkan kata berdasarkan frekuensi dalam topik.
        ranked = model_counts.argsort()[::-1]

        words = [
            model_features[index]
            for index in ranked
            if model_counts[index] > 0
            and model_features[index] in dictionary.token2id
            and model_features[index] in feature_names
        ][:TOP_N_WORDS]

        if len(words) < 2:
            continue

        topic_ids.append(topic_id)
        topic_words.append(words)
        topic_counts.append(len(article_ids))

    return topic_ids, topic_words, topic_counts


def evaluate(
    model_name,
    assignments,
    model_documents,
    reference_name,
    reference_documents,
    dictionary,
):
    topic_ids, topic_words, topic_counts = build_topic_words(
        assignments,
        model_documents,
        reference_documents,
        dictionary,
    )

    if not topic_words:
        raise ValueError(
            f"Tidak ada kata kunci yang dapat dievaluasi: "
            f"{model_name} / {reference_name}"
        )

    coherence = CoherenceModel(
        topics=topic_words,
        texts=list(reference_documents.values()),
        dictionary=dictionary,
        coherence="c_v",
        processes=1,
    )

    scores = coherence.get_coherence_per_topic()

    details = []

    for topic_id, words, count, score in zip(
        topic_ids, topic_words, topic_counts, scores
    ):
        details.append({
            "model": model_name,
            "reference": reference_name,
            "topic_id": topic_id,
            "article_count": count,
            "keywords": ", ".join(words),
            "coherence_cv": round(float(score), 4),
        })

    return {
        "model": model_name,
        "reference": reference_name,
        "document_count": len(assignments),
        "topic_count": len(topic_words),
        "outlier_count": sum(
            1 for value in assignments.values() if value == -1
        ),
        "evaluated_articles": sum(topic_counts),
        "overall_coherence_cv": round(
            float(coherence.get_coherence()), 4
        ),
        "topic_results": details,
    }


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)

    if not ASSIGNMENT_FILE.exists():
        raise FileNotFoundError(ASSIGNMENT_FILE)

    old_documents, main_assignments = load_database()
    protected_documents, protected_assignments = load_protected()

    if set(old_documents) != set(protected_documents):
        raise ValueError(
            "ID dokumen pada kedua versi preprocessing berbeda."
        )

    if set(main_assignments) != set(old_documents):
        raise ValueError(
            "Assignment model utama tidak cocok dengan korpus."
        )

    if set(protected_assignments) != set(protected_documents):
        raise ValueError(
            "Assignment Protected Terms tidak cocok dengan korpus."
        )

    models = {
        "main_model": (main_assignments, old_documents),
        "protected_terms": (
            protected_assignments,
            protected_documents,
        ),
    }

    references = {
        "processed_text": old_documents,
        "protected_terms": protected_documents,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summaries = []
    all_details = []

    for reference_name, reference_documents in references.items():
        dictionary = Dictionary(
            list(reference_documents.values())
        )

        dictionary.filter_extremes(
            no_below=2,
            no_above=0.95,
            keep_n=10000,
        )

        if len(dictionary) == 0:
            raise ValueError(
                f"Dictionary kosong: {reference_name}"
            )

        print("\n" + "=" * 60)
        print(f"KORPUS REFERENSI: {reference_name}")
        print("=" * 60)

        for model_name, (assignments, model_documents) in models.items():
            print(f"\nMengevaluasi {model_name}...")

            result = evaluate(
                model_name,
                assignments,
                model_documents,
                reference_name,
                reference_documents,
                dictionary,
            )

            summaries.append({
                key: value
                for key, value in result.items()
                if key != "topic_results"
            })

            all_details.extend(result["topic_results"])

            print(
                f"Topik: {result['topic_count']} | "
                f"Outlier: {result['outlier_count']} | "
                f"Artikel dievaluasi: "
                f"{result['evaluated_articles']} | "
                f"C_v: {result['overall_coherence_cv']:.4f}"
            )

    summary_path = OUTPUT_DIR / "cross_evaluation_summary.json"
    details_path = OUTPUT_DIR / "cross_evaluation_topics.csv"

    with summary_path.open("w", encoding="utf-8") as file:
        json.dump(
            summaries,
            file,
            indent=2,
            ensure_ascii=False,
        )

    with details_path.open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "model",
                "reference",
                "topic_id",
                "article_count",
                "keywords",
                "coherence_cv",
            ],
        )
        writer.writeheader()
        writer.writerows(all_details)

    print("\n" + "=" * 60)
    print("EVALUASI SILANG SELESAI")
    print("=" * 60)

    for item in summaries:
        print(
            f"{item['model']:18} | "
            f"{item['reference']:15} | "
            f"C_v: {item['overall_coherence_cv']:.4f}"
        )

    print(f"\nRingkasan: {summary_path}")
    print(f"Detail: {details_path}")
    print("Database dan model utama tidak diubah.")


if __name__ == "__main__":
    main()
