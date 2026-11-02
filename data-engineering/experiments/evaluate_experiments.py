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
OUTPUT_DIR = BASE_DIR / "outputs" / "comparison"

EXPERIMENTS = {
    "main_model": None,
    "processed_text": (
        BASE_DIR / "outputs" / "topic_experiment"
        / "experimental_assignments.csv"
    ),
    "cleaned_text": (
        BASE_DIR / "outputs" / "topic_experiment_cleaned"
        / "experimental_assignments.csv"
    ),
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

    documents = {}
    for article_id, text in rows:
        words = text.split()
        if words:
            documents[str(article_id)] = words

    return documents


def load_assignments(experiment_name, assignment_file):
    if experiment_name == "main_model":
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute("""
                SELECT id, topic_id
                FROM articles
                WHERE topic_id IS NOT NULL
                ORDER BY id
            """).fetchall()
        return {str(article_id): int(topic_id)
                for article_id, topic_id in rows}

    assignments = {}
    with assignment_file.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        for row in csv.DictReader(file):
            assignments[str(row["id"])] = int(row["topic_id"])

    return assignments


def evaluate_model(name, assignments, documents, dictionary):
    grouped = defaultdict(list)

    for article_id, topic_id in assignments.items():
        if topic_id != -1 and article_id in documents:
            grouped[topic_id].append(documents[article_id])

    topic_ids = sorted(grouped)

    if not topic_ids:
        raise ValueError(f"Tidak ada topik valid pada {name}")

    vectorizer = CountVectorizer(
        tokenizer=str.split,
        token_pattern=None,
        lowercase=False,
        min_df=2,
        max_df=0.95,
        max_features=10000,
    )

    reference_texts = [" ".join(words) for words in documents.values()]
    matrix = vectorizer.fit_transform(reference_texts)
    feature_names = vectorizer.get_feature_names_out()
    reference_ids = list(documents.keys())
    id_to_index = {
        article_id: index
        for index, article_id in enumerate(reference_ids)
    }

    topic_word_lists = []
    topic_counts = []

    for topic_id in topic_ids:
        article_ids = [
            article_id
            for article_id, assigned_topic in assignments.items()
            if assigned_topic == topic_id
            and article_id in id_to_index
        ]

        indices = [id_to_index[article_id] for article_id in article_ids]
        counts = matrix[indices].sum(axis=0).A1
        ranked_indices = counts.argsort()[::-1]

        words = [
            feature_names[index]
            for index in ranked_indices
            if counts[index] > 0
            and feature_names[index] in dictionary.token2id
        ][:TOP_N_WORDS]

        topic_word_lists.append(words)
        topic_counts.append(len(article_ids))

    coherence = CoherenceModel(
        topics=topic_word_lists,
        texts=list(documents.values()),
        dictionary=dictionary,
        coherence="c_v",
        processes=1,
    )

    scores = coherence.get_coherence_per_topic()
    overall = coherence.get_coherence()

    results = []
    for topic_id, words, count, score in zip(
        topic_ids, topic_word_lists, topic_counts, scores
    ):
        results.append({
            "model": name,
            "topic_id": topic_id,
            "article_count": count,
            "keywords": ", ".join(words),
            "coherence_cv": round(float(score), 4),
        })

    return {
        "model": name,
        "document_count": len(assignments),
        "topic_count": len(topic_ids),
        "outlier_count": sum(
            1 for topic_id in assignments.values()
            if topic_id == -1
        ),
        "evaluated_articles": sum(topic_counts),
        "overall_coherence_cv": round(float(overall), 4),
        "topic_results": results,
    }


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)

    documents = load_reference_documents()
    if not documents:
        raise ValueError("Tidak ada processed_text untuk evaluasi.")

    dictionary = Dictionary(list(documents.values()))
    dictionary.filter_extremes(
        no_below=2,
        no_above=0.95,
        keep_n=10000,
    )

    if len(dictionary) == 0:
        raise ValueError("Kosakata referensi kosong.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summaries = []
    all_topic_results = []

    for name, assignment_file in EXPERIMENTS.items():
        print(f"\nMengevaluasi: {name}")

        if assignment_file is not None and not assignment_file.exists():
            raise FileNotFoundError(assignment_file)

        assignments = load_assignments(name, assignment_file)

        if len(assignments) != len(documents):
            raise ValueError(
                f"Jumlah assignment {name} ({len(assignments)}) "
                f"tidak sama dengan dokumen referensi ({len(documents)})."
            )

        result = evaluate_model(
            name, assignments, documents, dictionary
        )

        summaries.append({
            key: value
            for key, value in result.items()
            if key != "topic_results"
        })
        all_topic_results.extend(result["topic_results"])

        print(f"Jumlah topik       : {result['topic_count']}")
        print(f"Jumlah outlier     : {result['outlier_count']}")
        print(
            "Overall coherence : "
            f"{result['overall_coherence_cv']:.4f}"
        )

    summary_file = OUTPUT_DIR / "model_comparison_summary.json"
    topic_file = OUTPUT_DIR / "model_comparison_topics.csv"

    with summary_file.open("w", encoding="utf-8") as file:
        json.dump(summaries, file, indent=2, ensure_ascii=False)

    with topic_file.open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "model", "topic_id", "article_count",
                "keywords", "coherence_cv"
            ],
        )
        writer.writeheader()
        writer.writerows(all_topic_results)

    print("\n" + "=" * 60)
    print("PERBANDINGAN SELESAI")
    print("=" * 60)
    for item in summaries:
        print(
            f"{item['model']:15} | "
            f"Topik: {item['topic_count']:2} | "
            f"Outlier: {item['outlier_count']:3} | "
            f"c_v: {item['overall_coherence_cv']:.4f}"
        )

    print(f"\nRingkasan: {summary_file}")
    print(f"Detail topik: {topic_file}")


if __name__ == "__main__":
    main()
