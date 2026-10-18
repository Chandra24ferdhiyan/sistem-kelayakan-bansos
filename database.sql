-- ============================================================
-- DATABASE: Sistem Pendukung Keputusan Klasifikasi Kelayakan
-- Penerima Bansos - Kecamatan Paranggupito
-- ============================================================

-- Membuat database
CREATE DATABASE IF NOT EXISTS spk_bansos
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;

USE spk_bansos;

-- ============================================================
-- TABEL: users (Untuk Autentikasi)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nama_lengkap VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Insert Admin Default (Password: admin123)
-- Hash generated using werkzeug.security.generate_password_hash('admin123')
INSERT IGNORE INTO users (username, password_hash, nama_lengkap) VALUES 
('admin', 'scrypt:32768:8:1$x0jSztc2T46qZkZp$3f78e478540c72eff45ea084045fcaa2abaf6aa0bf247e034079afccf2655bfd240e94bb5484501a5592c300262174300407fcf8deebe5962002167d5ffabb10', 'Administrator Bansos');


-- ============================================================
-- TABEL: bobot_kriteria (Pengaturan Bobot Dinamis)
-- ============================================================
CREATE TABLE IF NOT EXISTS bobot_kriteria (
    kode_kriteria VARCHAR(50) PRIMARY KEY,
    nama_kriteria VARCHAR(100) NOT NULL,
    tipe ENUM('cost', 'benefit') NOT NULL,
    bobot DECIMAL(5,2) NOT NULL
) ENGINE=InnoDB;

-- Insert Bobot Default
INSERT IGNORE INTO bobot_kriteria (kode_kriteria, nama_kriteria, tipe, bobot) VALUES
('pendapatan', 'Pendapatan', 'cost', 0.40),
('luas_lahan', 'Luas Lahan', 'cost', 0.15),
('jumlah_tanggungan', 'Jumlah Tanggungan', 'benefit', 0.35),
('kepadatan_penduduk', 'Kepadatan Penduduk', 'benefit', 0.10);


-- ============================================================
-- TABEL: penduduk
-- Menyimpan data warga beserta parameter sosio-ekonomi
-- dan kepadatan penduduk untuk proses klasifikasi SAW.
-- ============================================================
CREATE TABLE IF NOT EXISTS penduduk (
    id INT AUTO_INCREMENT PRIMARY KEY,           -- ID unik (Auto Increment)
    nama VARCHAR(100) NOT NULL,                  -- Nama lengkap warga
    alamat VARCHAR(255) NOT NULL,                -- Alamat domisili di Kec. Paranggupito
    pendapatan DECIMAL(15,2) NOT NULL,           -- Pendapatan bulanan (Rp) - Kriteria Cost
    jumlah_tanggungan INT NOT NULL,              -- Jumlah anggota keluarga tanggungan - Kriteria Benefit
    luas_lahan DECIMAL(10,2) NOT NULL,           -- Luas lahan yang dimiliki (m²) - Kriteria Cost
    kepadatan_penduduk DECIMAL(10,2) NOT NULL,   -- Kepadatan penduduk desa (jiwa/km²) - Kriteria Benefit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- DATA SAMPEL: 10 data warga Kecamatan Paranggupito
-- Data ini digunakan untuk demonstrasi dan pengujian sistem.
-- ============================================================
INSERT INTO penduduk (nama, alamat, pendapatan, jumlah_tanggungan, luas_lahan, kepadatan_penduduk) VALUES
('Slamet Widodo',      'Desa Gudangharjo, RT 01/RW 02',    800000.00,  5, 50.00,  320.50),
('Sri Mulyani',        'Desa Paranggupito, RT 03/RW 01',   1200000.00, 3, 120.00, 280.75),
('Bambang Sutrisno',   'Desa Songbanyu, RT 02/RW 03',      500000.00,  6, 30.00,  410.20),
('Dewi Sartika',       'Desa Gudangharjo, RT 04/RW 01',    2500000.00, 2, 250.00, 150.30),
('Ahmad Fauzi',        'Desa Parangkidang, RT 01/RW 04',   750000.00,  4, 80.00,  350.00),
('Siti Nurhaliza',     'Desa Paranggupito, RT 02/RW 02',   1800000.00, 1, 200.00, 190.60),
('Joko Prasetyo',      'Desa Songbanyu, RT 05/RW 01',      600000.00,  7, 40.00,  450.80),
('Rina Agustina',      'Desa Gudangharjo, RT 03/RW 03',    950000.00,  3, 90.00,  300.00),
('Hendra Wijaya',      'Desa Parangkidang, RT 01/RW 02',   3000000.00, 1, 300.00, 120.40),
('Yulia Permata Sari', 'Desa Paranggupito, RT 04/RW 03',   700000.00,  5, 60.00,  380.90);
