# Rancang Bangun Sistem Deteksi Tren dan Analisis Evolusi Topik Berita Berskala Besar Berbasis Big Data dan Natural Language Processing

**Status Proyek:** In Development

## Deskripsi Proyek

Proyek Capstone Teknik Informatika ini bertujuan membangun sistem untuk mendeteksi tren dan menganalisis evolusi topik berita berbahasa Indonesia menggunakan pendekatan Big Data dan Natural Language Processing (NLP).

Sistem dirancang untuk mengumpulkan berita dari berbagai sumber, menyimpan data artikel, melakukan preprocessing teks, mengelompokkan berita berdasarkan kesamaan topik, serta menganalisis perkembangan topik dari waktu ke waktu. Hasil analisis direncanakan disajikan melalui dashboard web.

## Tujuan

- Mengumpulkan berita berbahasa Indonesia dari berbagai sumber.
- Menyimpan data berita beserta sumber, URL, tanggal publikasi, dan teks artikel yang tersedia.
- Melakukan preprocessing teks untuk mendukung analisis NLP.
- Mengelompokkan artikel berdasarkan kesamaan topik.
- Menganalisis perkembangan topik dan mendeteksi tren pemberitaan.
- Menyajikan hasil analisis melalui dashboard web.

## Tim Pengembang

| Nama | Peran |
|---|---|
| Ilham Manziz | Data Engineering / Big Data |
| M. Fatih Hadziq | NLP dan Trend Analysis |
| Ariyandi Maulana Putra | Dashboard dan Integrasi |

## Teknologi

| Teknologi | Penggunaan |
|---|---|
| Python | Bahasa pemrograman utama |
| RSS, Requests, dan Feedparser | Pengambilan dan pembacaan feed berita |
| SQLite | Penyimpanan data berita secara lokal |
| Sastrawi | Preprocessing teks bahasa Indonesia |
| Sentence Transformers | Menghasilkan representasi vektor teks |
| BERTopic | Pemodelan dan pengelompokan topik |
| Git dan GitHub | Pengelolaan versi dan kolaborasi |
| Apache Spark | Kandidat teknologi pemrosesan skala besar; belum diintegrasikan |

## Fitur dan Status Implementasi

### Sudah Diimplementasikan

- Pengambilan berita dari lima sumber RSS: ANTARA, detikNews, CNN Indonesia, Tempo Nasional, dan CNA Indonesia.
- Penyimpanan artikel ke database SQLite.
- Pencegahan duplikasi artikel berdasarkan URL.
- Validasi sumber berita, data artikel, dan tanggal publikasi.
- Penanganan kesalahan pengambilan RSS dan pencatatan hasil setiap sumber.
- Preprocessing teks menggunakan Sastrawi.
- Validasi kelengkapan kolom teks hasil preprocessing.
- Pemodelan topik menggunakan BERTopic.
- Eksperimen dan evaluasi kualitas topik.
- Agregasi awal distribusi berita berdasarkan tanggal dan topik.
- Otomatisasi pengambilan berita harian melalui Windows Task Scheduler.

### Status Dataset Terakhir

Berdasarkan audit database lokal pada 25 November 2026:

| Keterangan | Hasil |
|---|---:|
| Total artikel | 2.935 |
| Integritas SQLite | OK |
| Judul kosong | 0 |
| URL kosong | 0 |
| Tanggal publikasi kosong | 0 |
| `cleaned_text` kosong | 0 |
| `processed_text` kosong | 0 |
| URL duplikat | 0 |

Jumlah artikel tersebut merupakan kondisi database lokal pada waktu pemeriksaan dan dapat berubah setelah pengambilan berita berikutnya.

### Masih Dalam Pengembangan

- Peningkatan kualitas dan cakupan data historis.
- Topic Tracking untuk mengikuti perubahan topik antarperiode.
- Event Tracking untuk mengidentifikasi perkembangan peristiwa.
- Trend Detection berdasarkan data temporal yang memadai.
- Dashboard web dan integrasi seluruh komponen.
- Evaluasi kualitas dan stabilitas hasil pemodelan topik.
- Evaluasi kebutuhan integrasi Apache Spark.

## Sumber Data dan Batasan

Data dikumpulkan dari feed RSS beberapa portal berita. Daftar sumber dan alamat feed dikelola melalui `config/sources.json`.

Feed RSS umumnya menyediakan judul, URL, tanggal publikasi, dan ringkasan. Ketersediaan serta kelengkapan isi artikel bergantung pada masing-masing sumber. Oleh karena itu, teks yang diproses dapat berupa gabungan judul dan ringkasan, bukan selalu isi artikel lengkap.

Ketersediaan feed juga bergantung pada koneksi jaringan dan layanan masing-masing portal berita. Kegagalan koneksi pada satu sumber tidak selalu menghentikan pemrosesan sumber lainnya, tetapi dapat menyebabkan hasil pengambilan berita berstatus parsial.

Cakupan tanggal antarartikel belum merata. Analisis tren jangka panjang perlu mempertimbangkan kualitas tanggal, kelengkapan teks, dan distribusi data.

## Struktur Proyek

```text
capstone-news-trend-analysis/
├── config/
│   └── sources.json
├── data-engineering/
│   ├── database.py
│   ├── fetch_news.py
│   ├── preprocess_news.py
│   └── experiments/
├── dashboard-frontend/
├── docs/
│   └── progress.md
├── nlp/
│   ├── topic_model.py
│   └── trend_analysis.py
├── run_daily_fetch.bat
├── requirements.txt
├── README.md
└── .gitignore
```

Folder `dashboard-frontend/` disiapkan untuk pengembangan dashboard. Implementasi dashboard masih dalam tahap pengembangan. Database lokal, backup, log, model hasil pelatihan, dan virtual environment tidak disertakan dalam repository.

## Persiapan Lingkungan

Langkah berikut menggunakan PowerShell pada Windows.

### 1. Clone repository

```powershell
git clone https://github.com/CreatorVeldanava/capstone-news-trend-analysis.git
cd capstone-news-trend-analysis
```

### 2. Buat dan aktifkan virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Instal dependensi

```powershell
python -m pip install -r requirements.txt
```

### 4. Inisialisasi database

```powershell
python data-engineering/database.py
```

### 5. Ambil berita dari RSS

```powershell
python data-engineering/fetch_news.py
```

Perintah ini mengakses sumber RSS dan dapat menambahkan artikel baru ke database. Hasil pengambilan bergantung pada ketersediaan jaringan dan layanan RSS. Periksa ringkasan proses untuk mengetahui sumber yang berhasil maupun gagal.

### 6. Jalankan pemeriksaan data

```powershell
python data-engineering/experiments/check_database.py
python data-engineering/experiments/check_dates.py
python data-engineering/experiments/check_source_dates.py
```

### 7. Jalankan preprocessing

```powershell
python data-engineering/preprocess_news.py
```

Skrip ini melakukan pembersihan dan preprocessing teks artikel yang tersimpan dalam database.

### 8. Jalankan pemodelan topik

```powershell
python nlp/topic_model.py
```

Pemodelan BERTopic dapat memerlukan sumber daya komputasi dan waktu yang cukup besar.

### 9. Jalankan analisis agregasi tren

```powershell
python nlp/trend_analysis.py
```

Skrip ini menghasilkan agregasi jumlah artikel berdasarkan tanggal dan topik. Hasilnya belum dapat dianggap sebagai sistem deteksi tren final atau pelacakan evolusi topik.

## Otomatisasi Pengambilan Berita

Skrip `run_daily_fetch.bat` menjalankan pengambilan berita dan preprocessing secara berurutan serta menyimpan log ke `logs/fetch_news.log`.

Penjadwalan dilakukan melalui Windows Task Scheduler pada komputer tempat sistem dikonfigurasi. Jadwal lokal tersebut tidak otomatis tersedia ketika repository di-clone pada komputer lain.

Task Scheduler hanya dapat menjalankan tugas ketika komputer tersedia. Jika komputer mati pada waktu jadwal, eksekusi dapat dicoba setelah komputer kembali aktif apabila opsi `StartWhenAvailable` diaktifkan.

Hasil setiap eksekusi perlu diperiksa melalui log. Jika salah satu sumber RSS gagal, proses dapat tetap melanjutkan sumber lain dan preprocessing, tetapi status akhir pipeline dapat menunjukkan kegagalan parsial.

## Kolaborasi Git

Pengembangan dilakukan melalui branch fitur. Perubahan diintegrasikan ke branch `main` melalui Pull Request sesuai aturan repository.

## Lisensi dan Penggunaan Data

Penggunaan data mengikuti ketentuan dan kebijakan masing-masing sumber berita. Repository ini berfokus pada pengembangan sistem analisis; ketersediaan data lokal tidak berarti seluruh isi artikel dapat didistribusikan ulang.

## Dokumentasi Progres

Perkembangan implementasi, eksperimen, hasil evaluasi, dan rencana pengembangan proyek dapat dilihat pada dokumen berikut:

- [Progres Pengembangan Proyek](docs/progress.md)

Dokumen tersebut diperbarui mengikuti perkembangan pekerjaan tim. Hasil eksperimen yang masih bersifat sementara tetap ditandai sebagai hasil sementara sampai proses evaluasi dan validasi selesai.