# Sistem Pendukung Keputusan (SPK) Kelayakan Bansos

Sistem ini dibangun menggunakan framework **Flask (Python)** dan menggunakan **MySQL** sebagai sistem manajemen basis data.

Berikut adalah panduan langkah demi langkah untuk menjalankan aplikasi ini di komputer Anda.

## Persyaratan Sistem

Sebelum menjalankan aplikasi, pastikan komputer Anda telah terinstal perangkat lunak berikut:
1. **Python**: Versi 3.9 atau yang lebih baru. (Dapat diunduh di [python.org](https://www.python.org/downloads/))
2. **XAMPP / MySQL Server**: Untuk menjalankan database MySQL. (Dapat menggunakan XAMPP, WAMP, atau menginstal MySQL Server langsung).

---

## Langkah-Langkah Instalasi & Menjalankan Sistem

### 1. Persiapkan Database MySQL
1. Buka dan jalankan **MySQL** (jika menggunakan XAMPP, klik tombol "Start" pada modul Apache dan MySQL).
2. Buka phpMyAdmin di browser Anda (biasanya di `http://localhost/phpmyadmin`).
3. Buat database baru dengan nama: `spk_bansos`.
4. Pilih tab **Import**, lalu pilih file `database.sql` yang ada di dalam folder proyek ini.
5. Klik **Go** atau **Import** untuk mengeksekusi struktur tabel dan data ke dalam database `spk_bansos`.

### 2. Instalasi Dependensi (Library Python)
Sistem ini membutuhkan beberapa library Python seperti Flask, Pandas, dan konektor MySQL agar dapat berjalan.
1. Buka Terminal (Command Prompt / PowerShell / Git Bash) di dalam folder proyek ini. 
   *(Cara cepat di Windows: buka folder proyek, klik di bagian address bar atas (path folder), ketik `cmd`, lalu tekan Enter).*
2. **(Opsional namun disarankan)** Buat *virtual environment* agar tidak bentrok dengan library di komputer:
   ```bash
   python -m venv venv
   ```
   Lalu aktifkan:
   - Untuk Windows: `venv\Scripts\activate`
   - Untuk Mac/Linux: `source venv/bin/activate`
3. Instal semua library yang dibutuhkan dengan menjalankan perintah berikut:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Menjalankan Aplikasi
1. Setelah semua dependensi (library) berhasil terinstal, jalankan server Flask pada terminal dengan perintah:
   ```bash
   python app.py
   ```
2. Anda akan melihat informasi bahwa server telah berjalan (biasanya di `Running on http://127.0.0.1:5000/`).
3. Buka web browser (Chrome, Edge, Firefox, dll) dan akses alamat berikut:
   ```
   http://localhost:5000/
   ```

---

## Catatan Tambahan
- Pastikan username dan password database MySQL di komputer Anda sesuai dengan yang ada di file konfigurasi. Secara default, aplikasi (di file `app.py`) dikonfigurasi untuk XAMPP:
  - Host: `localhost`
  - User: `root`
  - Password: `''` (kosong)
  - Database: `spk_bansos`
  
  *(Jika Anda memiliki password untuk user root di MySQL, silakan sesuaikan variabel `DB_CONFIG` di bagian atas file `app.py`).*
- Jika ada *error* tidak mengenali perintah `python` di terminal, coba gunakan perintah `python3` (terutama untuk Mac/Linux).
- File template import data penduduk sudah tersedia di sistem, teman Anda dapat mengunduhnya langsung dari dalam aplikasi di halaman Data Penduduk.
