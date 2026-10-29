import re
import sqlite3
import html
from pathlib import Path

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import (
    StopWordRemoverFactory,
)

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "news.db"

stemmer = StemmerFactory().create_stemmer()
stopword_factory = StopWordRemoverFactory()
stopwords = set(stopword_factory.get_stop_words())

stopwords.update({
    "terkait", "tersebut", "menurut", "melalui",
    "terhadap", "dalam", "antara", "hingga",
    "sejumlah", "orang", "tahun", "kini",
})


def clean_text(text):
    """Membersihkan teks HTML, entitas HTML, dan spasi."""
    if not text:
        return ""

    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def process_text(text):
    """Membersihkan, menghapus stopword, dan melakukan stemming."""
    text = clean_text(text).lower()
    words = re.findall(r"[a-z]+", text)

    words = [word for word in words if word not in stopwords]
    if not words:
        return ""

    text = stemmer.stem(" ".join(words))
    words = [word for word in text.split() if word not in stopwords]

    return " ".join(words)


def ensure_column(connection, column_name):
    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(articles)")
    }

    if column_name not in columns:
        connection.execute(
            f"ALTER TABLE articles ADD COLUMN {column_name} TEXT"
        )


def main():
    if not DB_PATH.exists():
        print(f"Database tidak ditemukan: {DB_PATH}")
        return

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row

        ensure_column(connection, "cleaned_text")
        ensure_column(connection, "processed_text")

        # Hanya memproses ulang artikel yang belum memiliki teks.
        articles = connection.execute("""
            SELECT id, title, summary
            FROM articles
            WHERE cleaned_text IS NULL OR TRIM(cleaned_text) = ''
               OR processed_text IS NULL OR TRIM(processed_text) = ''
            ORDER BY id
        """).fetchall()

        updated = 0
        empty = 0

        for article in articles:
            title = clean_text(article["title"] or "")
            summary = clean_text(article["summary"] or "")
            original_text = f"{title} {summary}".strip()

            cleaned = re.sub(r"\s+", " ", original_text).strip()
            processed = process_text(cleaned)

            connection.execute("""
                UPDATE articles
                SET cleaned_text = ?, processed_text = ?
                WHERE id = ?
            """, (cleaned, processed, article["id"]))

            if processed:
                updated += 1
            else:
                empty += 1

        connection.commit()

        totals = connection.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(
                    CASE WHEN cleaned_text IS NOT NULL
                         AND TRIM(cleaned_text) != '' THEN 1 ELSE 0 END
                ) AS cleaned_count,
                SUM(
                    CASE WHEN processed_text IS NOT NULL
                         AND TRIM(processed_text) != '' THEN 1 ELSE 0 END
                ) AS processed_count
            FROM articles
        """).fetchone()

        print("=" * 60)
        print("PREPROCESSING BERITA")
        print("=" * 60)
        print(f"Artikel yang diperiksa       : {len(articles)}")
        print(f"Artikel dengan teks diproses : {updated}")
        print(f"Teks hasil kosong            : {empty}")
        print(f"Total artikel di database    : {totals['total']}")
        print(f"cleaned_text terisi          : {totals['cleaned_count']}")
        print(f"processed_text terisi        : {totals['processed_count']}")


if __name__ == "__main__":
    main()
