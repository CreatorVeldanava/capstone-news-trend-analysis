
# Progres Pengembangan

Dokumen ini mencatat perkembangan implementasi, eksperimen, hasil pengujian, dan pekerjaan lanjutan pada proyek Capstone.

**Judul Penelitian:**

Rancang Bangun Sistem Deteksi Tren dan Analisis Evolusi Topik Berita Berskala Besar Berbasis Big Data dan Natural Language Processing.

**Status:** In Development — tahap pengembangan dan evaluasi model.

## 1. Ringkasan Proyek

Proyek ini bertujuan membangun sistem analisis berita berbahasa Indonesia untuk mengelompokkan artikel berdasarkan kesamaan topik, mengikuti evolusi topik, mengidentifikasi perkembangan peristiwa, dan mendeteksi tren berita berdasarkan data temporal.

Pengembangan dilakukan melalui pengumpulan berita RSS, penyimpanan data, preprocessing, pemodelan topik, evaluasi, serta pengembangan komponen analisis lanjutan.

## 2. Progres yang Telah Dilakukan

### 2.1 Persiapan dan Struktur Proyek

- Repository GitHub dan lingkungan pengembangan lokal telah disiapkan.
- Struktur kode dipisahkan menjadi direktori `data-engineering/`, `nlp/`, dan `dashboard-frontend/`.
- Konfigurasi sumber berita disimpan di `config/sources.json`.
- Dependensi Python dicatat dalam `requirements.txt`.
- Aturan `.gitignore` digunakan untuk mengecualikan database lokal, model hasil pelatihan, backup, log, dan virtual environment.

### 2.2 Pengumpulan dan Penyimpanan Data

- Pengumpulan berita RSS dikonfigurasi untuk lima sumber: ANTARA, detikNews, CNN Indonesia, Tempo Nasional, dan CNA Indonesia.
- Data artikel disimpan menggunakan SQLite.
- Duplikasi artikel dicegah berdasarkan URL.
- Pemeriksaan kelengkapan data, tanggal publikasi, dan distribusi sumber telah dilakukan.
- Pengambilan berita harian telah dikonfigurasi melalui Windows Task Scheduler.
- Pemeriksaan dataset mencatat 1.044 artikel dalam database lokal pada pemeriksaan terakhir.
- Sebanyak 774 artikel digunakan dalam eksperimen pemodelan awal.
- Dataset mencakup tanggal 23 Agustus hingga 2 November 2026, dengan 25 tanggal publikasi berbeda.

**Batasan data:** Data RSS yang dikumpulkan umumnya berisi judul dan ringkasan, bukan selalu isi artikel lengkap. Distribusi tanggal juga belum merata sehingga analisis tren jangka panjang masih membutuhkan validasi data lebih lanjut.

### 2.3 Preprocessing Teks

- Preprocessing teks bahasa Indonesia menggunakan Sastrawi telah dibuat.
- Pembersihan teks mencakup penghapusan elemen HTML, normalisasi, tokenisasi, stopword removal, dan stemming.
- Eksperimen Protected Terms dilakukan untuk mempertahankan kata penting yang dapat berubah makna akibat stemming.
- Kata yang dilindungi dalam eksperimen meliputi `pemerintah`, `asian`, `tersangka`, dan `pelaku`.
- Hasil pemeriksaan menunjukkan kata-kata tersebut berhasil dipertahankan dalam teks hasil preprocessing.

Eksperimen Protected Terms masih menjadi kandidat preprocessing yang perlu dievaluasi lebih lanjut melalui stabilitas dan kualitas pengelompokan topik.

### 2.4 Pemodelan Topik BERTopic

Model menggunakan embedding `paraphrase-multilingual-MiniLM-L12-v2` dan BERTopic dengan `min_topic_size=5`.

Hasil eksperimen utama pada 774 artikel:

| Pengujian | Topik | Outlier | C_v |
|---|---:|---:|---:|
| Model utama | 31 | 186 | 0,5309 |
| Protected Terms | 34 | 216 | 0,5511 |

Nilai C_v merupakan hasil evaluasi eksploratif dan belum menjadi bukti tunggal bahwa suatu model lebih baik. Perbandingan lanjutan juga telah dilakukan menggunakan evaluasi silang pada dua versi preprocessing.

Hasil evaluasi silang:

- Model utama pada teks standar: 0,5352.
- Protected Terms pada teks standar: 0,5504.
- Model utama pada teks Protected Terms: 0,5267.
- Protected Terms pada teks Protected Terms: 0,5555.

Protected Terms memperoleh nilai koherensi lebih tinggi dalam pengujian tersebut. Namun, hasilnya masih perlu diperiksa melalui evaluasi kualitas kelompok topik dan pengujian stabilitas model.

### 2.5 Pengujian Artikel Baru

Sebanyak 270 artikel baru telah diproses menggunakan preprocessing Protected Terms dan diuji menggunakan model yang telah dilatih sebelumnya melalui `transform()`.

Hasil pengujian:

| Keterangan | Jumlah |
|---|---:|
| Artikel diuji | 270 |
| Mendapat penempatan topik | 244 |
| Outlier | 26 |
| Assignment coverage | 90,37% |

Artikel baru berhasil ditempatkan pada 33 topik yang telah tersedia dalam model.

Assignment coverage menunjukkan cakupan penempatan artikel, bukan akurasi atau ketepatan klasifikasi topik. Oleh karena itu, pemeriksaan manual terhadap kelompok artikel tetap diperlukan.

### 2.6 Audit Kualitas Topik

Pemeriksaan manual terhadap hasil pengelompokan menemukan beberapa kelompok yang masih bercampur, sementara kelompok lainnya menunjukkan kesamaan tema atau peristiwa yang cukup jelas.

Beberapa temuan:

- Topic 0 dan Topic 1 masih menunjukkan pencampuran tema.
- Topic 5 cenderung mengelompokkan berbagai jenis berita olahraga.
- Topic 9 memiliki kelompok berita kecelakaan dan kriminal dengan beberapa peristiwa berbeda.
- Topic 15 menunjukkan indikasi pengelompokan berdasarkan format berita karena sebagian besar judul diawali `VIDEO`.
- Topic 17 relatif konsisten pada tema bencana dan cuaca.
- Topic 22 relatif konsisten pada tema ekonomi.

Audit ini menjadi dasar perbaikan dan evaluasi model berikutnya. Pengelompokan berdasarkan tema luas tidak selalu berarti seluruh artikel membahas peristiwa yang sama.

### 2.7 Eksperimen Prefix Judul

Pemeriksaan prefix pada hasil prediksi 244 artikel menemukan:

- 15 judul dengan prefix `VIDEO`.
- 4 judul dengan prefix `FOTO`.

Eksperimen BERTopic Protected Terms tanpa prefix kemudian dijalankan pada 774 artikel dengan konfigurasi yang sama.

Hasil eksperimen:

| Keterangan | Hasil |
|---|---:|
| Dokumen | 774 |
| Prefix dihapus | 0 |
| Topik | 29 |
| Outlier | 174 |
| Persentase outlier | 22,48% |

Tidak ditemukan prefix yang dapat dihapus pada `processed_text`. Dengan demikian, eksperimen ini belum dapat digunakan untuk menyimpulkan bahwa penghapusan prefix meningkatkan kualitas topik.

Pemeriksaan lanjutan diperlukan untuk mengetahui apakah prefix hanya terdapat pada judul dan apakah judul ikut diproses dalam teks yang digunakan model.

## 3. Pekerjaan yang Sedang Berlangsung

- Menuntaskan evaluasi kualitas dan pencampuran kelompok topik.
- Memeriksa perbedaan teks judul, ringkasan, dan `processed_text`.
- Menentukan pendekatan preprocessing yang paling sesuai.
- Mengevaluasi konsistensi dan stabilitas hasil BERTopic.
- Menyiapkan dasar pengembangan Topic Tracking.

## 4. Rencana Pengembangan Berikutnya

### Kualitas Data dan Preprocessing

- Memperbaiki kualitas dan pemerataan data historis.
- Memvalidasi tanggal publikasi dan kelengkapan teks.
- Meninjau penggunaan judul dan ringkasan dalam preprocessing.
- Menentukan perlakuan terhadap prefix dan format berita.

### Analisis Topik dan Peristiwa

- Mengembangkan Topic Tracking untuk mengikuti perubahan topik antarperiode.
- Mengembangkan Event Tracking untuk membedakan peristiwa tertentu dalam kelompok topik yang lebih luas.
- Mengembangkan Trend Detection berdasarkan indikator temporal yang terdefinisi.
- Melakukan evaluasi hasil analisis menggunakan data yang telah divalidasi.

### Integrasi Sistem

- Mengembangkan dashboard web.
- Mengintegrasikan pengumpulan data, preprocessing, pemodelan topik, dan analisis tren.
- Mengevaluasi kebutuhan Apache Spark untuk pemrosesan data berskala besar.
- Mempertimbangkan AI Summary/RAG sebagai komponen pendukung setelah fondasi analisis selesai.

## 5. Batasan dan Catatan Evaluasi

- Dataset saat ini terutama memanfaatkan judul dan ringkasan RSS, bukan selalu isi artikel lengkap.
- Distribusi tanggal publikasi belum merata.
- Nilai coherence tidak secara langsung menunjukkan akurasi pengelompokan.
- Assignment coverage bukan ukuran ketepatan prediksi.
- Beberapa kelompok topik masih memerlukan perbaikan.
- Topic Tracking, Event Tracking, dan Trend Detection belum selesai diimplementasikan.
- Dashboard web dan integrasi Apache Spark masih dalam tahap pengembangan atau evaluasi kebutuhan.

## 6. Status Keseluruhan

Proyek telah memiliki fondasi pengumpulan data, penyimpanan, preprocessing, pemodelan BERTopic, serta eksperimen dan evaluasi awal.

Hasil yang diperoleh saat ini bersifat sementara dan belum dinyatakan sebagai hasil final penelitian. Setiap permasalahan kualitas data, preprocessing, pemodelan, dan integrasi akan ditinjau serta diselesaikan sebelum sistem dinyatakan selesai.

Dokumen ini akan diperbarui mengikuti perkembangan implementasi dan hasil pengujian berikutnya.
