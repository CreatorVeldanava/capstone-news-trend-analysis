import re
import sqlite3
import html
import sys

from pathlib import Path

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import (
    StopWordRemoverFactory,
)


# ============================================================
# KONFIGURASI
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "news.db"

DATABASE_TIMEOUT = 30


# ============================================================
# INISIALISASI NLP
# ============================================================

stemmer = StemmerFactory().create_stemmer()

stopword_factory = StopWordRemoverFactory()
stopwords = set(stopword_factory.get_stop_words())

stopwords.update({
    "terkait", "tersebut", "menurut", "melalui",
    "terhadap", "dalam", "antara", "hingga",
    "sejumlah", "orang", "tahun", "kini",
})


# ============================================================
# PEMBERSIHAN TEKS
# ============================================================

def clean_text(text):
    """Membersihkan entitas HTML, tag HTML, dan spasi."""

    if text is None:
        return ""

    text = html.unescape(str(text))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# PREPROCESSING NLP
# ============================================================

def process_text(text):
    """Melakukan tokenisasi, stopword removal, dan stemming."""

    text = clean_text(text).lower()

    words = re.findall(r"[a-z]+", text)

    words = [
        word for word in words
        if word not in stopwords
    ]

    if not words:
        return ""

    text = stemmer.stem(" ".join(words))

    words = [
        word for word in text.split()
        if word not in stopwords
    ]

    return " ".join(words)


# ============================================================
# VALIDASI STRUKTUR DATABASE
# ============================================================

def get_columns(connection):
    """Mengambil nama kolom tabel articles."""

    return {
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(articles)"
        )
    }


def ensure_column(connection, column_name):
    """Memastikan kolom preprocessing tersedia."""

    allowed_columns = {
        "cleaned_text",
        "processed_text",
    }

    if column_name not in allowed_columns:
        raise ValueError(
            f"Nama kolom tidak diizinkan: {column_name}"
        )

    columns = get_columns(connection)

    if column_name not in columns:
        connection.execute(
            f"ALTER TABLE articles ADD COLUMN {column_name} TEXT"
        )


def validate_structure(connection):
    """Memastikan tabel dan kolom dasar tersedia."""

    tables = {
        row["name"]
        for row in connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
        """)
    }

    if "articles" not in tables:
        raise RuntimeError(
            "Tabel articles tidak ditemukan."
        )

    required = {
        "id",
        "title",
        "summary",
    }

    missing = required - get_columns(connection)

    if missing:
        raise RuntimeError(
            f"Kolom wajib tidak ditemukan: {sorted(missing)}"
        )


# ============================================================
# VALIDASI HASIL PREPROCESSING
# ============================================================

def validate_results(connection):
    """Menghitung kelengkapan hasil preprocessing."""

    return connection.execute("""
        SELECT
            COUNT(*) AS total,

            COALESCE(SUM(
                CASE
                    WHEN cleaned_text IS NOT NULL
                     AND TRIM(cleaned_text) != ''
                    THEN 1 ELSE 0
                END
            ), 0) AS cleaned_count,

            COALESCE(SUM(
                CASE
                    WHEN processed_text IS NOT NULL
                     AND TRIM(processed_text) != ''
                    THEN 1 ELSE 0
                END
            ), 0) AS processed_count

        FROM articles
    """).fetchone()


# ============================================================
# PROGRAM UTAMA
# ============================================================

def main():

    if not DB_PATH.exists():
        print(f"Database tidak ditemukan: {DB_PATH}")
        return 1

    connection = None

    try:
        connection = sqlite3.connect(
            DB_PATH,
            timeout=DATABASE_TIMEOUT,
        )

        connection.row_factory = sqlite3.Row

        connection.execute(
            f"PRAGMA busy_timeout = {DATABASE_TIMEOUT * 1000}"
        )

        # Semua perubahan skema dan data berada
        # dalam satu transaksi.
        connection.execute("BEGIN IMMEDIATE")

        validate_structure(connection)

        ensure_column(connection, "cleaned_text")
        ensure_column(connection, "processed_text")

        # Seluruh artikel diperiksa untuk mendeteksi
        # perbedaan hasil preprocessing.
        articles = connection.execute("""
            SELECT
                id,
                title,
                summary,
                cleaned_text,
                processed_text
            FROM articles
            ORDER BY id
        """).fetchall()

        updated = 0
        cleaned_changed = 0
        processed_changed = 0
        empty = 0

        for article in articles:

            title = clean_text(
                article["title"]
            )

            summary = clean_text(
                article["summary"]
            )

            cleaned = clean_text(
                f"{title} {summary}"
            )

            processed = process_text(cleaned)

            if not cleaned or not processed:
                empty += 1

                raise RuntimeError(
                    "Hasil preprocessing kosong pada "
                    f"artikel ID {article['id']}. "
                    "Transaksi dibatalkan."
                )

            old_cleaned = article["cleaned_text"] or ""
            old_processed = article["processed_text"] or ""

            clean_diff = old_cleaned != cleaned
            processed_diff = old_processed != processed

            if not clean_diff and not processed_diff:
                continue

            connection.execute("""
                UPDATE articles
                SET cleaned_text = ?,
                    processed_text = ?
                WHERE id = ?
            """, (
                cleaned,
                processed,
                article["id"],
            ))

            updated += 1

            if clean_diff:
                cleaned_changed += 1

            if processed_diff:
                processed_changed += 1

        # Validasi seluruh isi database sebelum commit.
        totals = validate_results(connection)

        total = totals["total"]
        cleaned_count = totals["cleaned_count"]
        processed_count = totals["processed_count"]

        print("=" * 65)
        print("PREPROCESSING BERITA")
        print("=" * 65)

        print(
            f"Artikel diperiksa              : {len(articles)}"
        )
        print(
            f"Artikel diperbarui             : {updated}"
        )
        print(
            f"Perubahan cleaned_text         : {cleaned_changed}"
        )
        print(
            f"Perubahan processed_text       : {processed_changed}"
        )
        print(
            f"Teks kosong                    : {empty}"
        )
        print(
            f"Total artikel database         : {total}"
        )
        print(
            f"cleaned_text terisi            : {cleaned_count}"
        )
        print(
            f"processed_text terisi          : {processed_count}"
        )

        if (
            empty > 0
            or cleaned_count != total
            or processed_count != total
        ):
            raise RuntimeError(
                "Validasi preprocessing gagal. "
                "Seluruh perubahan transaksi dibatalkan."
            )

        connection.commit()

        print("\nPreprocessing dan validasi berhasil.")

        return 0

    except sqlite3.Error as error:

        if connection is not None and connection.in_transaction:
            connection.rollback()

        print(f"Kesalahan database: {error}")

        return 1

    except KeyboardInterrupt:

        if connection is not None and connection.in_transaction:
            connection.rollback()

        print("\nProses dihentikan. Transaksi dibatalkan.")

        return 130

    except Exception as error:

        if connection is not None and connection.in_transaction:
            connection.rollback()

        print(f"Kesalahan preprocessing: {error}")

        return 1

    finally:

        if connection is not None:
            connection.close()


if __name__ == "__main__":
    sys.exit(main())
