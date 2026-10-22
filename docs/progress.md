# Progres Pengembangan

## Status Saat Ini

Proyek berada pada tahap implementasi awal. Fondasi pengumpulan berita, penyimpanan data, preprocessing teks, pemodelan topik, dan analisis awal berdasarkan tanggal telah dibuat dan diuji secara lokal.

## Progres yang Selesai

### Persiapan Proyek
- Repository GitHub dibuat dan repository lokal disiapkan di Windows.
- Struktur awal proyek dan konfigurasi sumber berita dibuat.
- Virtual environment Python disiapkan.
- Dependensi Python dicatat dalam `requirements.txt`.
- Aturan `.gitignore` diperbarui untuk mengecualikan database, log, model hasil pelatihan, dan berkas lokal tertentu.

### Pengumpulan dan Penyimpanan Data
- Pengumpulan berita RSS dari lima sumber dikonfigurasi: ANTARA, detikNews, CNN Indonesia, Tempo Nasional, dan CNA Indonesia.
- Data artikel disimpan ke database SQLite.
- Duplikasi artikel dicegah berdasarkan URL.
- Skrip pemeriksaan database dan tanggal dibuat.
- Pengumpulan berita harian dijadwalkan melalui Windows Task Scheduler dan telah diuji secara lokal.

### Pemrosesan dan Analisis Awal
- Preprocessing teks berita menggunakan Sastrawi telah dijalankan.
- Pemodelan topik menggunakan BERTopic telah berhasil dijalankan pada data yang tersedia saat pengujian.
- Skrip analisis awal distribusi berita berdasarkan tanggal telah dibuat.
- Hasil analisis temporal masih perlu divalidasi karena tanggal dan cakupan historis dari masing-masing feed belum seragam.

### Dokumentasi dan Version Control
- Kode implementasi awal telah diunggah ke GitHub.
- README diperbarui untuk menjelaskan teknologi, fitur, cara menjalankan program, dan status implementasi.
- Repository menggunakan commit terpisah dengan pesan yang menjelaskan perubahan.

## Pekerjaan Berikutnya

### Kualitas Data
- Mengumpulkan data secara berkelanjutan untuk membangun riwayat berita yang lebih memadai.
- Memvalidasi tanggal publikasi, kelengkapan data, dan distribusi artikel setiap sumber.
- Meninjau kualitas preprocessing dan hasil pengelompokan topik.
- Memeriksa ketentuan akses serta penggunaan data dari sumber berita.

### Analisis Topik dan Tren
- Mengembangkan Topic Tracking untuk mengikuti topik antarperiode.
- Mengembangkan Event Tracking untuk mengidentifikasi perkembangan peristiwa.
- Mengembangkan Trend Detection dengan periode dan metrik yang terdefinisi.
- Mengevaluasi hasil analisis menggunakan data temporal yang telah divalidasi.

### Sistem dan Evaluasi
- Mengembangkan dashboard web.
- Mengintegrasikan pengumpulan data, pemrosesan NLP, dan analisis tren.
- Mengevaluasi kebutuhan Apache Spark untuk pemrosesan data berskala besar.
- Melakukan pengujian sistem dan mendokumentasikan hasil evaluasi.

## Catatan

Status di atas menggambarkan implementasi dan pengujian lokal yang telah dilakukan. Pengujian awal BERTopic dan analisis tanggal belum menjadi bukti bahwa seluruh sistem telah selesai atau bahwa hasil deteksi tren sudah valid.

Dashboard web, Topic Tracking, Event Tracking, dan integrasi Apache Spark belum dinyatakan selesai. Hasil serta status setiap fitur akan diperbarui setelah implementasi dan pengujiannya dilakukan.
