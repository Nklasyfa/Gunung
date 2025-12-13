-- Tambahkan tiket untuk tanggal di masa depan (Desember 2025 - Januari 2026)
-- agar kalender bisa menampilkan tanggal yang bisa diklik

-- Tiket untuk Jalur 1 (Cemoro Sewu - Gunung Lawu)
INSERT INTO `tiket` (`jalur_id`, `harga`, `kuota_harian`, `tanggal_berlaku`) VALUES
(1, 35000, 100, '2025-12-14 00:00:00'),
(1, 35000, 100, '2025-12-15 00:00:00'),
(1, 35000, 100, '2025-12-20 00:00:00'),
(1, 35000, 100, '2025-12-21 00:00:00'),
(1, 35000, 100, '2025-12-25 00:00:00'),
(1, 35000, 100, '2025-12-26 00:00:00'),
(1, 35000, 100, '2025-12-27 00:00:00'),
(1, 35000, 100, '2025-12-28 00:00:00'),
(1, 40000, 100, '2026-01-01 00:00:00'),
(1, 40000, 100, '2026-01-04 00:00:00'),
(1, 40000, 100, '2026-01-05 00:00:00'),
(1, 35000, 100, '2026-01-11 00:00:00'),
(1, 35000, 100, '2026-01-12 00:00:00');

-- Tiket untuk Jalur 2 (Cemoro Kandang - Gunung Lawu)
INSERT INTO `tiket` (`jalur_id`, `harga`, `kuota_harian`, `tanggal_berlaku`) VALUES
(2, 50000, 80, '2025-12-14 00:00:00'),
(2, 50000, 80, '2025-12-15 00:00:00'),
(2, 50000, 80, '2025-12-20 00:00:00'),
(2, 50000, 80, '2025-12-21 00:00:00'),
(2, 50000, 80, '2025-12-27 00:00:00'),
(2, 50000, 80, '2025-12-28 00:00:00'),
(2, 55000, 80, '2026-01-01 00:00:00'),
(2, 50000, 80, '2026-01-11 00:00:00'),
(2, 50000, 80, '2026-01-12 00:00:00');

-- Tiket untuk Jalur 3 (Thekelan - Gunung Merbabu)
INSERT INTO `tiket` (`jalur_id`, `harga`, `kuota_harian`, `tanggal_berlaku`) VALUES
(3, 85000, 50, '2025-12-14 00:00:00'),
(3, 85000, 50, '2025-12-20 00:00:00'),
(3, 85000, 50, '2025-12-21 00:00:00'),
(3, 85000, 50, '2025-12-27 00:00:00'),
(3, 85000, 50, '2026-01-01 00:00:00'),
(3, 85000, 50, '2026-01-11 00:00:00');

-- Tambahkan kolom durasi ke tabel pemesanan jika belum ada
ALTER TABLE `pemesanan` ADD COLUMN IF NOT EXISTS `durasi` INT(11) DEFAULT 1 AFTER `total_harga`;
