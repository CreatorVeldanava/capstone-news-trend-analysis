
import json
import re
import html
import sqlite3
from datetime import datetime
from pathlib import Path

import feedparser
import requests

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config" / "sources.json"
DB_PATH = BASE_DIR / "data" / "news.db"
TIMEOUT = 45


def load_sources():
    """Membaca daftar sumber RSS."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        config = json.load(file)

    return config["sources"]


def clean_text(text):
    """Membersihkan tag HTML dan spasi dari ringkasan."""
    if not text:
        return ""

    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_source(source, connection):
    """Mengambil berita RSS dan menyimpannya ke database."""
    name = source["name"]
    url = source["url"]

    print(f"\nMemproses sumber: {name}")

    try:
        response = requests.get(
            url,
            timeout=TIMEOUT,
            headers={"User-Agent": "NewsTrendResearch/1.0"}
        )
        response.raise_for_status()

        feed = feedparser.parse(response.content)

        if not feed.entries:
            print("Tidak ada berita yang berhasil dibaca.")
            return {"source": name, "new": 0, "duplicate": 0, "failed": 0}

        new_count = 0
        duplicate_count = 0
        failed_count = 0

        for entry in feed.entries:
            title = clean_text(entry.get("title", ""))
            article_url = entry.get("link", "").strip()

            if not title or not article_url:
                failed_count += 1
                continue

            published_at = (
                entry.get("published")
                or entry.get("updated")
                or None
            )

            summary = clean_text(
                entry.get("summary")
                or entry.get("description")
                or ""
            )

            fetched_at = datetime.now().astimezone().isoformat(
                timespec="seconds"
            )

            try:
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO articles
                    (source, title, url, published_at, summary, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        title,
                        article_url,
                        published_at,
                        summary,
                        fetched_at
                    )
                )

                if cursor.rowcount == 1:
                    new_count += 1
                else:
                    duplicate_count += 1

            except sqlite3.Error as error:
                print(f"Gagal menyimpan artikel: {error}")
                failed_count += 1

        connection.commit()

        print(f"Berita baru disimpan : {new_count}")
        print(f"Berita duplikat      : {duplicate_count}")
        print(f"Berita gagal         : {failed_count}")

        return {
            "source": name,
            "new": new_count,
            "duplicate": duplicate_count,
            "failed": failed_count
        }

    except requests.RequestException as error:
        print(f"Gagal mengakses RSS: {error}")
    except Exception as error:
        print(f"Terjadi kesalahan: {error}")

    return {"source": name, "new": 0, "duplicate": 0, "failed": 1}


def main():
    print("=" * 60)
    print("PENGAMBILAN BERITA RSS DAN PENYIMPANAN DATABASE")
    print("=" * 60)

    try:
        sources = load_sources()
    except (OSError, json.JSONDecodeError, KeyError) as error:
        print(f"Gagal membaca konfigurasi sumber: {error}")
        return

    if not DB_PATH.exists():
        print("Database belum ditemukan. Jalankan: python database.py")
        return

    try:
        with sqlite3.connect(DB_PATH) as connection:
            results = [
                fetch_source(source, connection)
                for source in sources
            ]

            total_new = sum(item["new"] for item in results)
            total_duplicates = sum(item["duplicate"] for item in results)
            total_failed = sum(item["failed"] for item in results)

            total_articles = connection.execute(
                "SELECT COUNT(*) FROM articles"
            ).fetchone()[0]

        print("\n" + "=" * 60)
        print("RINGKASAN")
        print("=" * 60)
        print(f"Sumber RSS diproses : {len(sources)}")
        print(f"Berita baru         : {total_new}")
        print(f"Berita duplikat     : {total_duplicates}")
        print(f"Berita gagal        : {total_failed}")
        print(f"Total berita di DB   : {total_articles}")
        print("\nProses selesai.")

    except sqlite3.Error as error:
        print(f"Terjadi kesalahan database: {error}")


if __name__ == "__main__":
    main()
