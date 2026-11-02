import re
import csv
import sqlite3
from pathlib import Path

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "news.db"
OUTPUT_DIR = BASE_DIR / "outputs" / "preprocessing_experiments"
OUTPUT_FILE = OUTPUT_DIR / "protected_terms.csv"

stemmer = StemmerFactory().create_stemmer()
stopwords = set(StopWordRemoverFactory().get_stop_words())

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


def preprocess(text):
    if not text:
        return ""

    text = text.lower()
    words = re.findall(r"[a-z]+", text)

    words = [
        word for word in words
        if word not in stopwords
    ]

    result = []

    for word in words:
        if word in PROTECTED_WORDS:
            result.append(word)
        else:
            result.append(stemmer.stem(word))

    result = [
        word for word in result
        if word not in stopwords
    ]

    return " ".join(result)


def main():
    if not DB_PATH.exists():
        print(f"Database tidak ditemukan: {DB_PATH}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT id, title, cleaned_text
            FROM articles
            WHERE cleaned_text IS NOT NULL
              AND TRIM(cleaned_text) != ''
            ORDER BY id
        """).fetchall()

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "title", "processed_text"])

        for article_id, title, cleaned_text in rows:
            processed = preprocess(cleaned_text)
            writer.writerow([article_id, title, processed])

    print("=" * 60)
    print("EKSPERIMEN PREPROCESSING: PROTECTED TERMS")
    print("=" * 60)
    print("Jumlah artikel :", len(rows))
    print("Protected words:", ", ".join(sorted(PROTECTED_WORDS)))
    print("File hasil     :", OUTPUT_FILE)


if __name__ == "__main__":
    main()
