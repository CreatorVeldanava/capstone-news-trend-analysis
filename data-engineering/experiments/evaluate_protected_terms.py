import csv
import json
import sqlite3
from pathlib import Path

from gensim.corpora import Dictionary
from gensim.models import CoherenceModel
from sklearn.feature_extraction.text import CountVectorizer

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "news.db"

OUTPUT_DIR = (
    BASE_DIR / "outputs"
    / "preprocessing_experiments"
    / "protected_terms_model"
)

EXPERIMENTS = {
    "main_model": {
        "assignments": None,
        "text_source": "database",
    },
    "protected_terms": {
        "assignments": OUTPUT_DIR / "assignments.csv",
        "text_source": OUTPUT_DIR / "assignments.csv",
    },
}

TOP_N_WORDS = 10


def load_reference_documents():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT id, processed_text
            FROM articles
            WHERE processed_text IS NOT NULL
              AND TRIM(processed_text) != ''
            ORDER BY id
        """).fetchall()

    return {
        str(article_id): text.split()
        for article_id, text in rows
        if text and text.split()
    }


def load_main_assignments():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT id, topic_id
            FROM articles
            WHERE topic_id IS NOT NULL
            ORDER BY id
        """).fetchall()

    return {
        str(article_id): int(topic_id)
        for article_id, topic_id in rows
    }


def load_experiment(file_path):
    assignments = {}
    documents = {}

    with file_path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        for row in csv.DictReader(file):
            article_id = str(row["id"])
            assignments[article_id] = int(row["topic_id"])
            documents[article_id] = row["processed_text"].split()

    return assignments, documents


def evaluate_model(
    name,
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

    reference_texts = [
        " ".join(words)
        for words in reference_documents.values()
    ]

    matrix = vectorizer.fit_transform(reference_texts)
    feature_names = vectorizer.get_feature_names_out()

    reference_ids = list(reference_documents.keys())
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

    topic_word_lists = []
    topic_counts = []
    topic_results = []

    for topic_id in sorted(grouped):
        article_ids = grouped[topic_id]

        topic_texts = [
            " ".join(model_documents[article_id])
            for article_id in article_ids
        ]

        topic_matrix = vectorizer.transform(topic_texts)
        counts = topic_matrix.sum(axis=0).A1

        ranked_indices = counts.argsort()[::-1]

        words = [
            feature_names[index]
            for index in ranked_indices
            if counts[index] > 0
            and feature_names[index] in dictionary.token2id
        ][:TOP_N_WORDS]

        if not words:
            continue

        topic_word_lists.append(words)
        topic_counts.append(len(article_ids))

        topic_results.append({
            "model": name,
            "topic_id": topic_id,
            "article_count": len(article_ids),
            "keywords": ", ".join(words),
        })

    if not topic_word_lists:
        raise ValueError(f"Tidak ada topik valid: {name}")

    coherence = CoherenceModel(
        topics=topic_word_lists,
        texts=list(reference_documents.values()),
        dictionary=dictionary,
        coherence="c_v",
        processes=1,
    )

    scores = coherence.get_coherence_per_topic()
    overall = coherence.get_coherence()

    for result, score in zip(topic_results, scores):
        result["coherence_cv"] = round(float(score), 4)

    return {
        "model": name,
        "document_count": len(assignments),
        "topic_count": len(topic_word_lists),
        "outlier_count": sum(
            1 for topic_id in assignments.values()
            if topic_id == -1
        ),
        "evaluated_articles": sum(topic_counts),
        "overall_coherence_cv": round(float(overall), 4),
        "topic_results": topic_results,
    }


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)

    reference_documents = load_reference_documents()

    dictionary = Dictionary(
        list(reference_documents.values())
    )

    dictionary.filter_extremes(
        no_below=2,
        no_above=0.95,
        keep_n=10000,
    )

    if len(dictionary) == 0:
        raise ValueError("Dictionary referensi kosong.")

    results = []
    all_topics = []

    for name, config in EXPERIMENTS.items():
        print(f"\nMengevaluasi: {name}")

        if name == "main_model":
            assignments = load_main_assignments()
            model_documents = reference_documents
        else:
            file_path = config["assignments"]

            if not file_path.exists():
                raise FileNotFoundError(file_path)

            assignments, model_documents = load_experiment(
                file_path
            )

        if set(assignments) != set(reference_documents):
            raise ValueError(
                f"ID dokumen {name} tidak sama dengan "
                "korpus referensi."
            )

        result = evaluate_model(
            name,
            assignments,
            model_documents,
            reference_documents,
            dictionary,
        )

        results.append({
            key: value
            for key, value in result.items()
            if key != "topic_results"
        })

        all_topics.extend(result["topic_results"])

        print(f"Dokumen            : {result['document_count']}")
        print(f"Jumlah topik       : {result['topic_count']}")
        print(f"Jumlah outlier     : {result['outlier_count']}")
        print(
            "Overall coherence : "
            f"{result['overall_coherence_cv']:.4f}"
        )

    summary_path = OUTPUT_DIR / "protected_terms_comparison.json"
    topics_path = OUTPUT_DIR / "protected_terms_topic_details.csv"

    with summary_path.open("w", encoding="utf-8") as file:
        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False,
        )

    with topics_path.open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "model",
                "topic_id",
                "article_count",
                "keywords",
                "coherence_cv",
            ],
        )
        writer.writeheader()
        writer.writerows(all_topics)

    print("\n" + "=" * 60)
    print("PERBANDINGAN PROTECTED TERMS SELESAI")
    print("=" * 60)

    for item in results:
        print(
            f"{item['model']:20} | "
            f"Topik: {item['topic_count']:2} | "
            f"Outlier: {item['outlier_count']:3} | "
            f"C_v: {item['overall_coherence_cv']:.4f}"
        )

    print(f"\nRingkasan: {summary_path}")
    print(f"Detail topik: {topics_path}")
    print("\nDatabase dan model utama tidak diubah.")


if __name__ == "__main__":
    main()
