import html
import json
import re
import sqlite3
import sys
import time

from contextlib import closing
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ============================================================
# KONFIGURASI
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = BASE_DIR / "config" / "sources.json"
DB_PATH = BASE_DIR / "data" / "news.db"

CONNECT_TIMEOUT = 10
READ_TIMEOUT = 30

MAX_RETRIES = 3
BACKOFF_FACTOR = 1

USER_AGENT = (
    "Mozilla/5.0 (compatible; NewsTrendResearch/1.0)"
)


# ============================================================
# HTTP SESSION
# ============================================================

def create_session():
    """Membuat session HTTP dengan retry untuk gangguan sementara."""

    retry = Retry(
        total=MAX_RETRIES,
        connect=MAX_RETRIES,
        read=MAX_RETRIES,
        status=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET"]),
        respect_retry_after_header=True,
        raise_on_status=True,
    )

    adapter = HTTPAdapter(max_retries=retry)

    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    })

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


# ============================================================
# VALIDASI KONFIGURASI
# ============================================================

def load_sources():
    """Membaca dan memvalidasi konfigurasi sumber RSS."""

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        config = json.load(file)

    if not isinstance(config, dict):
        raise ValueError(
            "Konfigurasi harus berupa object JSON."
        )

    sources = config.get("sources")

    if not isinstance(sources, list) or not sources:
        raise ValueError(
            "Daftar sumber RSS kosong atau tidak valid."
        )

    validated_sources = []
    source_names = set()

    for index, source in enumerate(sources, start=1):

        if not isinstance(source, dict):
            raise ValueError(
                f"Konfigurasi sumber ke-{index} tidak valid."
            )

        name = str(source.get("name") or "").strip()
        url = str(source.get("url") or "").strip()

        if not name:
            raise ValueError(
                f"Nama sumber ke-{index} kosong."
            )

        if not url:
            raise ValueError(
                f"URL sumber {name} kosong."
            )

        parsed_url = urlparse(url)

        if (
            parsed_url.scheme not in ("http", "https")
            or not parsed_url.netloc
        ):
            raise ValueError(
                f"URL sumber {name} tidak valid: {url}"
            )

        normalized_name = name.casefold()

        if normalized_name in source_names:
            raise ValueError(
                f"Nama sumber duplikat: {name}"
            )

        source_names.add(normalized_name)

        validated_sources.append({
            "name": name,
            "url": url,
        })

    return validated_sources


# ============================================================
# PEMBERSIHAN TEKS
# ============================================================

def clean_text(value):
    """Menghapus HTML dan merapikan spasi."""

    if value is None:
        return ""

    text = str(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# VALIDASI TANGGAL PUBLIKASI
# ============================================================

def get_publication_date(entry):
    """
    Mengambil tanggal publikasi atau pembaruan yang valid.

    Tanggal mentah dipertahankan agar format sumber tidak
    berubah. Tanggal hanya diterima jika feedparser berhasil
    menguraikannya menjadi struktur waktu yang valid.
    """

    date_fields = [
        ("published", "published_parsed"),
        ("updated", "updated_parsed"),
    ]

    for raw_field, parsed_field in date_fields:

        raw_date = str(
            entry.get(raw_field) or ""
        ).strip()

        parsed_date = entry.get(parsed_field)

        if not raw_date or parsed_date is None:
            continue

        try:
            if len(parsed_date) < 6:
                continue

            # Memastikan komponen tanggal dan waktu valid.
            datetime(*parsed_date[:6])

            return raw_date

        except (TypeError, ValueError, OverflowError):
            continue

    return None


# ============================================================
# HASIL SUMBER
# ============================================================

def make_result(
    name,
    new=0,
    duplicate=0,
    failed=0,
    duration=0,
):
    return {
        "source": name,
        "new": new,
        "duplicate": duplicate,
        "failed": failed,
        "duration": round(duration, 2),
    }


def failed_result(name, message, duration=0):
    print(f"GAGAL [{name}]: {message}")

    return make_result(
        name=name,
        failed=1,
        duration=duration,
    )


# ============================================================
# TRANSAKSI SUMBER
# ============================================================

def rollback_source(connection, savepoint, active):
    """Membatalkan seluruh perubahan dari sumber yang gagal."""

    if not active:
        return

    try:
        connection.execute(
            f"ROLLBACK TO SAVEPOINT {savepoint}"
        )

        connection.execute(
            f"RELEASE SAVEPOINT {savepoint}"
        )

    except sqlite3.Error:
        connection.rollback()
        raise


# ============================================================
# PENGAMBILAN RSS
# ============================================================

def fetch_source(source, connection, session):
    """Mengambil dan menyimpan artikel dari satu sumber RSS."""

    name = source["name"]
    url = source["url"]

    start_time = time.perf_counter()

    print(f"\nMemproses sumber: {name}")
    print(f"URL: {url}")

    savepoint = "rss_source_transaction"
    savepoint_active = False

    try:
        connection.execute(
            f"SAVEPOINT {savepoint}"
        )
        savepoint_active = True

        response = session.get(
            url,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        )

        response.raise_for_status()

        feed = feedparser.parse(response.content)

        entries = feed.entries
        feed_version = getattr(feed, "version", "")

        bozo = getattr(feed, "bozo", False)

        # Feed yang rusak tidak diproses sebagian.
        if bozo:
            raise ValueError(
                "Feed RSS/Atom memiliki format yang bermasalah: "
                f"{getattr(feed, 'bozo_exception', 'Kesalahan XML')}"
            )

        if not feed_version:
            raise ValueError(
                "Respons tidak dikenali sebagai feed RSS/Atom yang valid."
            )

        # Feed valid boleh tidak memiliki entri.
        if not entries:
            connection.execute(
                f"RELEASE SAVEPOINT {savepoint}"
            )
            savepoint_active = False

            duration = time.perf_counter() - start_time

            print(
                f"Feed valid, tetapi tidak memiliki artikel baru "
                f"untuk dibaca: {name}"
            )

            return make_result(
                name=name,
                duration=duration,
            )

        new_count = 0
        duplicate_count = 0
        failed_count = 0

        for entry in entries:

            title = clean_text(
                entry.get("title", "")
            )

            article_url = str(
                entry.get("link", "") or ""
            ).strip()

            try:
                parsed_article_url = urlparse(article_url)

                valid_url = (
                    parsed_article_url.scheme in ("http", "https")
                    and bool(parsed_article_url.netloc)
                )

            except ValueError:
                valid_url = False

            if not title or not valid_url:
                print(
                    f"Artikel dilewati [{name}]: "
                    "judul atau URL tidak valid."
                )

                failed_count += 1
                continue

            published_at = get_publication_date(entry)

            if not published_at:
                print(
                    f"Artikel dilewati [{name}]: "
                    f"tanggal publikasi tidak valid - {title[:80]}"
                )

                failed_count += 1
                continue

            summary = clean_text(
                entry.get("summary")
                or entry.get("description")
                or ""
            )

            fetched_at = datetime.now().astimezone().isoformat(
                timespec="seconds"
            )

            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO articles (
                    source,
                    title,
                    url,
                    published_at,
                    summary,
                    fetched_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    title,
                    article_url,
                    published_at,
                    summary,
                    fetched_at,
                ),
            )

            if cursor.rowcount == 1:
                new_count += 1
            else:
                duplicate_count += 1

        connection.execute(
            f"RELEASE SAVEPOINT {savepoint}"
        )
        savepoint_active = False

        duration = time.perf_counter() - start_time

        print(f"Berita baru       : {new_count}")
        print(f"Berita duplikat   : {duplicate_count}")
        print(f"Artikel dilewati  : {failed_count}")
        print(f"Waktu pemrosesan  : {duration:.2f} detik")

        return make_result(
            name=name,
            new=new_count,
            duplicate=duplicate_count,
            failed=failed_count,
            duration=duration,
        )

    except KeyboardInterrupt:
        rollback_source(
            connection,
            savepoint,
            savepoint_active,
        )
        raise

    except Exception as error:

        try:
            rollback_source(
                connection,
                savepoint,
                savepoint_active,
            )

        except sqlite3.Error as rollback_error:
            duration = time.perf_counter() - start_time

            return failed_result(
                name,
                f"{repr(error)}; rollback juga gagal: "
                f"{repr(rollback_error)}",
                duration,
            )

        duration = time.perf_counter() - start_time

        return failed_result(
            name,
            repr(error),
            duration,
        )


# ============================================================
# PROGRAM UTAMA
# ============================================================

def main():

    print("=" * 65)
    print("PENGAMBILAN BERITA RSS")
    print("=" * 65)

    try:
        sources = load_sources()

    except (
        OSError,
        json.JSONDecodeError,
        ValueError,
        TypeError,
    ) as error:

        print(f"Kesalahan konfigurasi: {error}")
        return 1

    if not DB_PATH.exists():
        print(f"Database tidak ditemukan: {DB_PATH}")
        return 1

    results = []

    try:
        with create_session() as session:

            with closing(
                sqlite3.connect(DB_PATH, timeout=30)
            ) as connection:

                connection.execute(
                    "PRAGMA busy_timeout = 30000"
                )

                for source in sources:

                    result = fetch_source(
                        source,
                        connection,
                        session,
                    )

                    results.append(result)

                    # Menyimpan hasil sumber yang selesai.
                    connection.commit()

                total_articles = connection.execute(
                    "SELECT COUNT(*) FROM articles"
                ).fetchone()[0]

        total_new = sum(
            item["new"] for item in results
        )

        total_duplicates = sum(
            item["duplicate"] for item in results
        )

        total_failed = sum(
            item["failed"] for item in results
        )

        failed_sources = sum(
            1 for item in results
            if item["failed"] > 0
        )

        print("\n" + "=" * 65)
        print("RINGKASAN PENGAMBILAN RSS")
        print("=" * 65)

        for item in results:
            print(
                f"{item['source']}: "
                f"baru={item['new']}, "
                f"duplikat={item['duplicate']}, "
                f"gagal={item['failed']}, "
                f"durasi={item['duration']} detik"
            )

        print("-" * 65)
        print(f"Jumlah sumber       : {len(sources)}")
        print(f"Sumber bermasalah   : {failed_sources}")
        print(f"Artikel baru        : {total_new}")
        print(f"Artikel duplikat    : {total_duplicates}")
        print(f"Artikel gagal       : {total_failed}")
        print(f"Total artikel DB    : {total_articles}")

        if total_failed:
            print("\nStatus: SELESAI DENGAN KEGAGALAN.")
            return 1

        print("\nStatus: SEMUA SUMBER BERHASIL DIPROSES.")
        return 0

    except KeyboardInterrupt:
        print(
            "\nINTERUPSI: Pengambilan RSS dihentikan."
        )
        return 130

    except sqlite3.Error as error:
        print(f"\nKesalahan database: {error}")
        return 1

    except Exception as error:
        print(f"\nKesalahan tidak terduga: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
