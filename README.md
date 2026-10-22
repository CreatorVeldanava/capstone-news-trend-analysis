# Rancang Bangun Sistem Deteksi Tren dan Analisis Evolusi Topik Berita Berskala Besar Berbasis Big Data dan Natural Language Processing

**Status Proyek:** In Development

## Deskripsi Proyek

Proyek Capstone Teknik Informatika ini bertujuan membangun sistem untuk mendeteksi tren dan menganalisis evolusi topik berita berbahasa Indonesia menggunakan pendekatan Big Data dan Natural Language Processing (NLP).

Sistem dirancang untuk mengumpulkan berita dari berbagai sumber, menyimpan riwayat artikel, mengelompokkan berita berdasarkan kesamaan topik, serta menganalisis perkembangan topik dari waktu ke waktu. Hasil analisis nantinya akan disajikan melalui dashboard web.

## Tujuan

- Mengumpulkan berita berbahasa Indonesia dari berbagai sumber.
- Menyimpan data berita beserta sumber, URL, tanggal publikasi, dan ringkasan.
- Melakukan preprocessing teks untuk mendukung analisis NLP.
- Mengelompokkan artikel berdasarkan kesamaan topik.
- Menganalisis perkembangan topik dan mendeteksi tren pemberitaan.
- Menyajikan hasil analisis melalui dashboard web.

## Tim Pengembang

| Nama | Rencana Peran |
|---|---|
| Ilham Manziz | Data Engineering / Big Data |
| M. Fatih Hadziq | NLP dan Trend Analysis |
| Ariyandi Maulana Putra | Dashboard dan Integrasi |

Pembagian peran merupakan rencana kerja awal dan dapat disesuaikan berdasarkan kesepakatan tim serta perkembangan implementasi.

## Teknologi

| Teknologi | Penggunaan |
|---|---|
| Python | Bahasa pemrograman utama |
| RSS dan Requests | Pengambilan berita dari sumber RSS |
| Feedparser | Membaca dan memproses feed RSS |
| SQLite | Penyimpanan data berita secara lokal |
| Sastrawi | Stemming dan preprocessing teks bahasa Indonesia |
| Sentence Transformers | Menghasilkan representasi vektor teks |
| BERTopic | Pemodelan dan pengelompokan topik berita |
| Git dan GitHub | Pengelolaan versi kode dan kolaborasi |
| Apache Spark | Kandidat teknologi pemrosesan data berskala besar pada tahap pengembangan berikutnya |

## Fitur dan Status Implementasi

### Sudah Diimplementasikan

- Pengambilan berita dari lima sumber RSS: ANTARA, detikNews, CNN Indonesia, Tempo Nasional, dan CNA Indonesia.
- Penyimpanan artikel ke database SQLite.
- Pencegahan duplikasi artikel berdasarkan URL.
- Pemeriksaan jumlah data, kelengkapan data, dan tanggal publikasi.
- Preprocessing teks berita menggunakan Sastrawi.
- Pemodelan topik menggunakan BERTopic.
- Analisis awal distribusi berita berdasarkan tanggal.
- Otomatisasi pengambilan berita harian melalui Windows Task Scheduler.

### Masih Dalam Pengembangan

- Validasi dan peningkatan kualitas data berita historis.
- Topic Tracking untuk mengikuti perubahan topik antarperiode.
- Event Tracking untuk mengidentifikasi perkembangan suatu peristiwa.
- Trend Detection yang dievaluasi berdasarkan data temporal yang memadai.
- Pengembangan dashboard web.
- Integrasi seluruh komponen sistem.
- Evaluasi performa dan kualitas hasil analisis.
- Penggunaan Apache Spark jika diperlukan untuk pemrosesan berskala besar.

## Sumber Data

Data dikumpulkan dari feed RSS beberapa portal berita. Daftar sumber dan alamat feed dikelola melalui `config/sources.json`.

Feed RSS umumnya menyediakan judul, URL, tanggal publikasi, dan ringkasan. Ketersediaan serta kelengkapan isi artikel bergantung pada masing-masing sumber. Karena itu, sistem belum mengasumsikan bahwa seluruh teks artikel lengkap tersedia.

Data yang terkumpul disimpan secara bertahap di database lokal agar riwayat pemberitaan dapat bertambah seiring waktu. Kualitas tanggal publikasi dan kelengkapan data perlu divalidasi sebelum digunakan untuk menarik kesimpulan tren.

## Struktur Proyek

```text
capstone-news-trend-analysis/
├── config/
│   └── sources.json
├── docs/
│   └── progress.md
├── database.py
├── fetch_news.py
├── check_database.py
├── check_dates.py
├── check_source_dates.py
├── preprocess_news.py
├── topic_model.py
├── trend_analysis.py
├── run_daily_fetch.bat
├── requirements.txt
├── README.md
└── .gitignore
```

Database lokal, log, model hasil pelatihan, dan virtual environment tidak disertakan dalam repository.

## Persiapan Lingkungan

Pastikan Python sudah terpasang di komputer. Langkah berikut menggunakan PowerShell pada Windows.

### 1. Clone repository

```powershell
git clone https://github.com/CreatorVeldanava/capstone-news-trend-analysis.git
cd capstone-news-trend-analysis
```

### 2. Buat virtual environment

```powershell
python -m venv .venv
```

Aktifkan lingkungan virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Instal dependensi

```powershell
python -m pip install -r requirements.txt
```

### 4. Inisialisasi database

```powershell
python database.py
```

### 5. Ambil berita

```powershell
python fetch_news.py
```

### 6. Periksa data

```powershell
python check_database.py
```

### 7. Jalankan preprocessing

```powershell
python preprocess_news.py
```

### 8. Jalankan pemodelan topik

```powershell
python topic_model.py
```

### 9. Jalankan analisis tren harian

```powershell
python trend_analysis.py
```

Catatan: jalankan tahapan sesuai urutan kebutuhan data. Pemodelan topik memerlukan data yang sudah diproses, sedangkan analisis tren perlu divalidasi dengan rentang waktu dan kualitas tanggal yang memadai. Pemodelan BERTopic dapat memerlukan sumber daya komputasi dan waktu yang cukup besar.

## Menjalankan Pengumpulan Berita Harian

Proyek menyediakan `run_daily_fetch.bat` untuk menjalankan pengambilan berita menggunakan virtual environment proyek. Otomatisasi dijadwalkan melalui Windows Task Scheduler pada komputer pengembang.

Pengumpulan harian bergantung pada komputer yang menyala, koneksi internet, dan ketersediaan feed RSS. Dashboard web dan layanan server yang berjalan terus-menerus belum menjadi bagian dari implementasi saat ini.

## Batasan Saat Ini

- Data yang terkumpul masih dalam tahap pengembangan dan validasi.
- Feed RSS tidak selalu menyediakan teks artikel lengkap.
- Tanggal publikasi dari berbagai sumber perlu dinormalisasi dan diperiksa.
- Analisis tren saat ini masih berupa analisis awal dan belum dapat dianggap sebagai hasil penelitian final.
- Topic Tracking, Event Tracking, dan dashboard web belum selesai diimplementasikan.
- Apache Spark masih menjadi rencana pengembangan, bukan komponen yang sudah terintegrasi.

## Lisensi dan Penggunaan Data

Proyek ini dikembangkan untuk keperluan akademik. Penggunaan data berita harus memperhatikan ketentuan masing-masing sumber, hak cipta, kebijakan akses, dan batasan penggunaan feed maupun isi artikel.

## Status Pengembangan

Proyek telah memiliki fondasi awal berupa pengumpulan berita RSS, penyimpanan SQLite, preprocessing teks, pemodelan topik dengan BERTopic, serta analisis awal berdasarkan tanggal. Pengembangan berikutnya difokuskan pada peningkatan kualitas data temporal, pelacakan evolusi topik, deteksi tren, dan pengembangan dashboard.
