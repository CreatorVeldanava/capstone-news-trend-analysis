# Progres Pengembangan

## Status Saat Ini

Proyek berada pada tahap implementasi awal sistem analisis tren berita. Fondasi pengumpulan data RSS, penyimpanan SQLite, preprocessing teks, pemodelan topik menggunakan BERTopic, dan analisis distribusi berita berdasarkan tanggal telah dibuat dan diuji secara lokal.

## Progres yang Selesai

### Persiapan dan Struktur Proyek

- Repository GitHub dan lingkungan pengembangan lokal telah disiapkan.
- Struktur kode dipisahkan menjadi direktori `data-engineering/` dan `nlp/`.
- Konfigurasi sumber berita disimpan di `config/sources.json`.
- Dependensi Python dicatat dalam `requirements.txt`.
- Aturan `.gitignore` diperbarui untuk mengecualikan database lokal, log, model hasil pelatihan, backup, dan berkas cache.

### Pengumpulan dan Penyimpanan Data

- Pengumpulan berita RSS dikonfigurasi untuk lima sumber: ANTARA, detikNews, CNN Indonesia, Tempo Nasional, dan CNA Indonesia.
- Data artikel disimpan dalam database SQLite pada `data/news.db`.
- Duplikasi artikel dicegah berdasarkan URL.
- Skrip pemeriksaan database, tanggal publikasi, dan distribusi tanggal per sumber telah dibuat.
- Pengumpulan berita otomatis dijadwalkan melalui Windows Task Scheduler.
- Pengujian lokal terakhir mencatat 774 artikel dari lima sumber berita.

### Preprocessing dan Pemodelan Topik

- Preprocessing teks menggunakan Sastrawi telah dijalankan.
- Kolom teks hasil preprocessing telah terisi untuk 774 artikel pada saat pemeriksaan.
- Pemodelan topik menggunakan BERTopic telah berhasil dijalankan.
- Pengujian model mencatat 31 topik reguler dan 186 artikel yang masuk kategori outlier.
- Evaluasi koherensi topik menggunakan metrik C_v menghasilkan nilai awal 0,5349. Nilai ini masih bersifat eksploratif dan perlu dievaluasi lebih lanjut.

### Analisis Temporal

- Skrip `nlp/trend_analysis.py` telah dibuat untuk menghitung distribusi artikel berdasarkan tanggal dan topik.
- Hasil agregasi disimpan dalam `outputs/trend_daily.csv` dan `outputs/trend_topic_summary.csv`.
- Pemeriksaan terakhir mencatat 774 tanggal publikasi valid dengan 22 tanggal berbeda, dalam rentang 23 Agustus hingga 29 Oktober 2026.
- Distribusi tanggal belum merata sehingga hasil agregasi belum cukup untuk menyimpulkan tren berita yang valid.

### Dokumentasi dan Pengujian Kode

- README telah diperbarui untuk menjelaskan struktur direktori, teknologi, cara menjalankan program, dan batasan implementasi.
- Path pada skrip telah disesuaikan dengan struktur direktori baru.
- Pemeriksaan sintaks Python dan `git diff --check` telah berhasil dilakukan.
- Database, model hasil pelatihan, backup, dan cache lokal telah dipastikan tidak ikut muncul sebagai berkas yang akan dilacak Git berdasarkan aturan `.gitignore`.

## Pekerjaan Berikutnya

### Kualitas Data

- Mengumpulkan data secara berkelanjutan agar riwayat berita lebih memadai.
- Memvalidasi tanggal publikasi, kelengkapan data, dan distribusi artikel dari setiap sumber.
- Meninjau kualitas preprocessing dan hasil pengelompokan topik.
- Memeriksa ketentuan akses dan penggunaan data dari sumber berita.

### Analisis Topik dan Tren

- Mengembangkan Topic Tracking untuk mengikuti perubahan topik antarperiode.
- Mengembangkan Event Tracking untuk mengidentifikasi perkembangan suatu peristiwa.
- Mengembangkan Trend Detection menggunakan periode, metrik, dan kriteria yang terdefinisi.
- Mengevaluasi hasil analisis menggunakan data temporal yang telah divalidasi.

### Sistem dan Evaluasi

- Mengembangkan dashboard web.
- Mengintegrasikan pengumpulan data, pemrosesan NLP, dan analisis tren.
- Mengevaluasi kebutuhan Apache Spark untuk pemrosesan data berskala besar.
- Melakukan pengujian sistem dan mendokumentasikan hasil evaluasi.

## Batasan Implementasi Saat Ini

Data yang diperoleh dari RSS umumnya berupa judul dan ringkasan berita, bukan teks lengkap artikel. Cakupan tanggal historis juga berbeda antar-sumber.

BERTopic telah dijalankan, tetapi hasil pemodelan masih perlu dievaluasi. Analisis temporal yang tersedia saat ini berupa agregasi jumlah artikel berdasarkan tanggal dan topik, bukan sistem deteksi tren yang telah tervalidasi.

Topic Tracking, Event Tracking, Trend Detection lanjutan, dashboard web, dan integrasi Apache Spark belum selesai diimplementasikan.

Dokumen ini mencatat progres pengembangan dan pengujian lokal. Status commit dan push terbaru akan diperiksa secara terpisah melalui Git.