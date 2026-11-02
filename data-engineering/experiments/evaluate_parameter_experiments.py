import csv
import json
import sqlite3
from pathlib import Path
from collections import defaultdict

from gensim.corpora import Dictionary
from gensim.models import CoherenceModel
from sklearn.feature_extraction.text import CountVectorizer

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "news.db"
OUTPUT_DIR = BASE_DIR / "outputs" / "parameter_experiments"

EXPERIMENTS = {
    "main_model": None,
    "experiment_A": OUTPUT_DIR / "experiment_A" / "assignments.csv",
    "experiment_B": OUTPUT_DIR / "experiment_B" / "assignments.csv",
    "experiment_C": OUTPUT_DIR / "experiment_C" / "assignments.csv",
}

TOP_N_WORDS = 10


def load_documents():
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute("""
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


def load_assignments(name, path):
    if name == "main_model":
        with sqlite3.connect(DB_PATH) as connection:
            rows = connection.execute("""
                SELECT id, topic_id
                FROM articles
                WHERE topic_id IS NOT NULL
                ORDER BY id
            """).fetchall()

        return {
            str(article_id): int(topic_id)
            for article_id, topic_id in rows
        }

    assignments = {}

    with path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        for row in csv.DictReader(file):
            assignments[str(row["id"])] = int(row["topic_id"])

    return assignments


def evaluate_model(name, assignments, documents, dictionary, matrix,
                   feature_names, id_to_index):
    grouped = defaultdict(list)

    for article_id, topic_id in assignments.items():
        if topic_id != -1 and article_id in documents:
            grouped[topic_id].append(article_id)

    topic_ids = sorted(grouped)

    topic_word_lists = []
    topic_counts = []
    topic_results = []

    for topic_id in topic_ids:
        article_ids = grouped[topic_id]
        indices = [
            id_to_index[article_id]
            for article_id in article_ids
        ]

        counts = matrix[indices].sum(axis=0).A1
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
        raise ValueError(f"Tidak ada topik valid pada {name}")

    coherence = CoherenceModel(
        topics=topic_word_lists,
        texts=list(documents.values()),
        dictionary=dictionary,
        coherence="c_v",
        processes=1,
    )

    scores = coherence.get_coherence_per_topic()
    overall = coherence.get_coherence()

    for result, score in zip(topic_results, scores):
        result["coherence_cv"] = round(float(score), 4)

    outliers = sum(
        1 for topic_id in assignments.values()
        if topic_id == -1
    )

    summary = {
        "model": name,
        "documents": len(assignments),
        "normal_topics": len(topic_ids),
        "outliers": outliers,
        "outlier_percentage": round(
            outliers / len(assignments) * 100, 2
        ),
        "overall_coherence_cv": round(float(overall), 4),
        "evaluated_topics": len(topic_results),
        "evaluated_articles": sum(topic_counts),
    }

    return summary, topic_results


def main():
    print("=" * 60)
    print("EVALUASI COHERENCE EKSPERIMEN PARAMETER")
    print("=" * 60)

    documents = load_documents()
    reference_ids = set(documents)

    print(f"Jumlah dokumen referensi: {len(documents)}")

    all_texts = list(documents.values())

    dictionary = Dictionary(all_texts)
    dictionary.filter_extremes(
        no_below=2,
        no_above=0.95,
        keep_n=10000,
    )

    vectorizer = CountVectorizer(
        tokenizer=str.split,
        token_pattern=None,
        lowercase=False,
        min_df=2,
        max_df=0.95,
        max_features=10000,
    )

    reference_texts = [
        " ".join(words) for words in all_texts
    ]

    matrix = vectorizer.fit_transform(reference_texts)
    feature_names = vectorizer.get_feature_names_out()

    id_to_index = {
        article_id: index
        for index, article_id in enumerate(documents)
    }

    summaries = []
    all_topic_results = []

    for name, path in EXPERIMENTS.items():
        print(f"\nMengevaluasi: {name}")

        assignments = load_assignments(name, path)

        assignment_ids = set(assignments)

        if assignment_ids != reference_ids:
            missing = reference_ids - assignment_ids
            extra = assignment_ids - reference_ids

            raise ValueError(
                f"ID artikel tidak cocok pada {name}. "
                f"Missing: {len(missing)}, Extra: {len(extra)}"
            )

        summary, topic_results = evaluate_model(
            name,
            assignments,
            documents,
            dictionary,
            matrix,
            feature_names,
            id_to_index,
        )

        summaries.append(summary)
        all_topic_results.extend(topic_results)

        print(f"Jumlah topik       : {summary['normal_topics']}")
        print(f"Jumlah outlier     : {summary['outliers']}")
        print(f"Persentase outlier : {summary['outlier_percentage']}%")
        print(f"Overall coherence : {summary['overall_coherence_cv']}")

    summary_path = OUTPUT_DIR / "parameter_coherence_summary.json"
    summary_path.write_text(
        json.dumps(summaries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    detail_path = OUTPUT_DIR / "parameter_coherence_topics.csv"

    with detail_path.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "model",
                "topic_id",
                "article_count",
                "coherence_cv",
                "keywords",
            ],
        )
        writer.writeheader()
        writer.writerows(all_topic_results)

    print("\n" + "=" * 60)
    print("PERBANDINGAN SELESAI")
    print("=" * 60)

    for result in summaries:
        print(
            f"{result['model']:15} | "
            f"Topik: {result['normal_topics']:2} | "
            f"Outlier: {result['outliers']:3} | "
            f"c_v: {result['overall_coherence_cv']:.4f}"
        )

    print(f"\nRingkasan: {summary_path}")
    print(f"Detail topik: {detail_path}")


if __name__ == "__main__":
    main()
