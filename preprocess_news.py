
import re
import sqlite3
from pathlib import Path

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import (
    StopWordRemoverFactory,
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "news.db"

stemmer = StemmerFactory().create_stemmer()

stopword_factory = StopWordRemoverFactory()
stopwords = set(stopword_factory.get_stop_words())

# Tambahan kata umum yang ingin diabaikan saat analisis berita.
stopwords.update({
    "terkait", "tersebut", "menurut", "melalui",
    "terhadap", "dalam", "antara", "hingga",
    "sejumlah", "orang", "tahun", "kini",
})


def process_text(text):
    """Membersihkan, menghapus stopword, dan melakukan stemming."""
    if not text:
        return ""

    text = text.lower()
    words = re.findall(r"[a-z]+", text)

    # Hapus kata umum sebelum stemming untuk mengurangi pemrosesan.
    words = [word for word in words if word not in stopwords]

    # Menggabungkan kata agar dapat diproses oleh Sastrawi.
    text = " ".join(words)
    text = stemmer.stem(text)

    # Hilangkan stopword yang mungkin muncul kembali setelah stemming.
    words = text.split()
    words = [word for word in words if word not in stopwords]

    return " ".join(words)


def column_exists(connection, table_name, column_name):
    columns = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return any(column["name"] == column_name for column in columns)


def main():
    if not DB_PATH.exists():
        print("Database tidak ditemukan.")
        return

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row

        if not column_exists(connection, "articles", "processed_text"):
            connection.execute(
                "ALTER TABLE articles ADD COLUMN processed_text TEXT"
            )

        articles = connection.execute("""
            SELECT id, title, summary
            FROM articles
        """).fetchall()

        processed_count = 0
        empty_count = 0

        for article in articles:
            original_text = (
                f"{article['title'] or ''} "
                f"{article['summary'] or ''}"
            )

            processed_text = process_text(original_text)

            connection.execute("""
                UPDATE articles
                SET processed_text = ?
                WHERE id = ?
            """, (processed_text, article["id"]))

            if processed_text:
                processed_count += 1
            else:
                empty_count += 1

        connection.commit()

        print("=" * 60)
        print("PREPROCESSING NLP BAHASA INDONESIA")
        print("=" * 60)
        print(f"Total artikel           : {len(articles)}")
        print(f"Teks berhasil diproses  : {processed_count}")
        print(f"Teks kosong             : {empty_count}")

        print("\nContoh hasil:")
        examples = connection.execute("""
            SELECT title, cleaned_text, processed_text
            FROM articles
            WHERE processed_text IS NOT NULL
            LIMIT 3
        """).fetchall()

        for index, article in enumerate(examples, start=1):
            print(f"\n{index}. Judul: {article['title']}")
            print(f"Teks sebelumnya: {(article['cleaned_text'] or '')[:250]}")
            print(f"Teks setelahnya: {(article['processed_text'] or '')[:250]}")


if __name__ == "__main__":
    main()
