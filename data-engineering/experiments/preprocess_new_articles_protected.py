import re
import csv
import html
import sqlite3
from pathlib import Path

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import (
    StopWordRemoverFactory,
)

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "news.db"

OUTPUT_DIR = (
    BASE_DIR / "outputs"
    / "preprocessing_experiments"
    / "new_articles_protected"
)

OUTPUT_FILE = OUTPUT_DIR / "new_articles.csv"

stemmer = StemmerFactory().create_stemmer()
stopwords = set(
    StopWordRemoverFactory().get_stop_words()
)

stopwords.update({
    "terkait", "tersebut", "menurut", "melalui",
    "terhadap", "dalam", "antara", "hingga",
    "sejumlah", "orang", "tahun", "kini",
})

PROTECTED_WORDS = {
    "pemerintah",
    "asian",
    "tersangka",
    "pelaku",
}


def clean_text(text):
    if not text:
        return ""

    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def process_text(text):
    text = clean_text(text).lower()
    words = re.findall(r"[a-z]+", text)

    words = [
        word for word in words
        if word not in stopwords
    ]

    processed_words = []

    for word in words:
        if word in PROTECTED_WORDS:
            processed_words.append(word)
        else:
            processed_words.append(stemmer.stem(word))

    processed_words = [
        word for word in processed_words
        if word not in stopwords
    ]

    return " ".join(processed_words)


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT id, source, title, url,
                   published_at, summary
            FROM articles
            WHERE (
                cleaned_text IS NULL
                OR TRIM(cleaned_text) = ''
            )
            AND (
                processed_text IS NULL
                OR TRIM(processed_text) = ''
            )
            ORDER BY id
        """).fetchall()

    results = []

    for article_id, source, title, url, published_at, summary in rows:
        cleaned_title = clean_text(title)
        cleaned_summary = clean_text(summary)

        cleaned = f"{cleaned_title} {cleaned_summary}".strip()
        processed = process_text(cleaned)

        results.append({
            "id": article_id,
            "source": source,
            "title": title,
            "url": url,
            "published_at": published_at,
            "cleaned_text": cleaned,
            "processed_text": processed,
        })

    fieldnames = [
        "id",
        "source",
        "title",
        "url",
        "published_at",
        "cleaned_text",
        "processed_text",
    ]

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(results)

    print("=" * 60)
    print("PREPROCESSING ARTIKEL BARU - PROTECTED TERMS")
    print("=" * 60)
    print(f"Artikel ditemukan : {len(rows)}")
    print(f"Artikel diproses  : {sum(bool(r['processed_text']) for r in results)}")
    print(f"Teks kosong       : {sum(not r['processed_text'] for r in results)}")
    print(f"Protected words   : {', '.join(sorted(PROTECTED_WORDS))}")
    print(f"File hasil        : {OUTPUT_FILE}")
    print("\nDatabase tidak diubah.")


if __name__ == "__main__":
    main()
