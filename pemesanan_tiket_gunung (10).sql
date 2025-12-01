-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Waktu pembuatan: 01 Des 2025 pada 18.23
-- Versi server: 10.4.32-MariaDB
-- Versi PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `pemesanan_tiket_gunung`
--

-- --------------------------------------------------------

--
-- Struktur dari tabel `anggota_pemesanan`
--

CREATE TABLE `anggota_pemesanan` (
  `anggota_id` int(11) NOT NULL,
  `pemesanan_id` int(11) NOT NULL,
  `user_id_anggota` int(11) NOT NULL COMMENT 'ID user yang diajak'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `detail_sewa`
--

CREATE TABLE `detail_sewa` (
  `detail_sewa_id` int(11) NOT NULL,
  `pemesanan_id` int(11) NOT NULL,
  `peralatan_id` int(11) NOT NULL,
  `jumlah` int(11) NOT NULL,
  `subtotal` decimal(10,0) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `detail_sewa`
--

INSERT INTO `detail_sewa` (`detail_sewa_id`, `pemesanan_id`, `peralatan_id`, `jumlah`, `subtotal`) VALUES
(1, 1, 1, 1, 50000),
(2, 1, 2, 2, 40000);

-- --------------------------------------------------------

--
-- Struktur dari tabel `gunung`
--

CREATE TABLE `gunung` (
  `gunung_id` int(11) NOT NULL,
  `nama_gunung` varchar(50) NOT NULL,
  `lokasi` varchar(100) NOT NULL,
  `latitude` decimal(10,8) DEFAULT NULL COMMENT 'Latitude untuk Google Maps',
  `longitude` decimal(11,8) DEFAULT NULL COMMENT 'Longitude untuk Google Maps',
  `ketinggian` int(5) DEFAULT 0 COMMENT 'Ketinggian dalam MDPL',
  `deskripsi` text NOT NULL,
  `sejarah` text DEFAULT NULL COMMENT 'Sejarah singkat gunung',
  `estimasi_waktu` varchar(100) DEFAULT 'N/A' COMMENT 'Estimasi waktu pendakian',
  `kuota_harian` int(4) DEFAULT 100 COMMENT 'Kuota pendaki per hari',
  `status_pendakian` enum('dibuka','ditutup') NOT NULL,
  `gambar` varchar(255) DEFAULT NULL,
  `kuota_bulanan` int(11) DEFAULT 500,
  `harga_tiket` decimal(10,0) NOT NULL DEFAULT 0,
  `min_days` int(11) NOT NULL DEFAULT 1,
  `max_days` int(11) NOT NULL DEFAULT 2
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `gunung`
--

INSERT INTO `gunung` (`gunung_id`, `nama_gunung`, `lokasi`, `latitude`, `longitude`, `ketinggian`, `deskripsi`, `sejarah`, `estimasi_waktu`, `kuota_harian`, `status_pendakian`, `gambar`, `kuota_bulanan`, `harga_tiket`, `min_days`, `max_days`) VALUES
(1, 'Gunung Lawu', 'Jawa Timur', -7.62600000, 111.19700000, 3265, 'Gunung populer dengan jalur Cemoro Sewu dan Cemoro Kandang', 'Gunung Lawu dikenal memiliki nilai sejarah tinggi, dengan banyak situs peninggalan Majapahit di lerengnya.', '2 hari 1 malam (via Cemoro Sewu)', 200, 'dibuka', '360_F_180045614_wUikfPv1VhpukGYtUBDfA2sGggXXJmQ5_1764551392.jpg', 500, 0, 1, 2),
(2, 'Gunung Semeru', 'Jawa Timur', NULL, NULL, 0, 'Gunung tertinggi di Jawa dengan puncak Mahameru', NULL, 'N/A', 100, 'ditutup', NULL, 500, 0, 1, 2),
(3, 'Gunung Merbabu', 'Jawa Tengah', NULL, NULL, 0, 'Gunung dengan jalur Selo, Suwanting dan Thekelan', NULL, 'N/A', 100, 'dibuka', NULL, 500, 0, 1, 2),
(4, 'Gunung Sumbing', 'Jawa Tengah', NULL, NULL, 0, 'Gunung tertinggi ke dua di jawa tengah', NULL, 'N/A', 100, 'dibuka', NULL, 500, 0, 1, 2),
(6, 'GUnung NGaiw', 'Ngawi', NULL, NULL, 0, 'isi singkat', NULL, 'N/A', 100, 'dibuka', NULL, 500, 0, 1, 2);

-- --------------------------------------------------------

--
-- Struktur dari tabel `jalur_pendakian`
--

CREATE TABLE `jalur_pendakian` (
  `jalur_id` int(11) NOT NULL,
  `gunung_id` int(11) NOT NULL,
  `nama_jalur` varchar(50) NOT NULL,
  `deskripsi` text NOT NULL,
  `estimasi` varchar(50) NOT NULL,
  `gambar_jalur` varchar(255) DEFAULT NULL,
  `tingkat_kesulitan` enum('mudah','sedang','sulit') DEFAULT 'sedang',
  `estimasi_waktu` int(11) DEFAULT 0,
  `gambar` varchar(255) DEFAULT NULL,
  `tersedia` tinyint(1) NOT NULL DEFAULT 1,
  `kuota_harian` int(11) NOT NULL DEFAULT 0,
  `harga` decimal(10,2) DEFAULT NULL COMMENT 'Optional jalur-level ticket price per person; if set, overrides gunung harga_tiket for this jalur'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `jalur_pendakian`
--

INSERT INTO `jalur_pendakian` (`jalur_id`, `gunung_id`, `nama_jalur`, `deskripsi`, `estimasi`, `gambar_jalur`, `tingkat_kesulitan`, `estimasi_waktu`, `gambar`, `tersedia`, `kuota_harian`, `harga`) VALUES
(1, 1, 'Cemoro Sewu', 'Jalur favorit', '8 jam', NULL, 'sedang', 0, NULL, 1, 0, NULL),
(2, 1, 'Cemoro Kandang', 'Jalur lebih panjang', '10 jam', NULL, 'sedang', 0, NULL, 1, 0, NULL),
(3, 3, 'Thekelan', 'Jalur resmi Merbabu', '9 jam', 'uploads\\jalur\\chainsaw-man-the-3840x2160-23852_1764511082.jpg', 'sedang', 0, NULL, 1, 0, NULL),
(7, 1, 'Banaran', '1', '9 jam', 'IMG-20251019-WA0004_1764551523.jpg', 'sedang', 0, NULL, 1, 0, NULL),
(9, 4, 'jalur ngawiw', 'qq', '9 jam', NULL, 'sedang', 0, NULL, 1, 20, NULL),
(10, 3, 'ajajjaja', 'q', '9 jam', NULL, 'sedang', 0, NULL, 0, 200, NULL),
(11, 6, 'kiww akiakaiiaia', 'wwwwwwwww', '9 jam', 'Thumbnail_1764552118.png', 'sulit', 0, NULL, 1, 4, NULL);

-- --------------------------------------------------------

--
-- Struktur dari tabel `kuota_bulanan_user`
--

CREATE TABLE `kuota_bulanan_user` (
  `kuota_bulanan_user_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `tahun_bulan` varchar(7) NOT NULL,
  `kuota_tersisa` int(11) DEFAULT 10,
  `kuota_awal` int(11) DEFAULT 10
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `log_transaksi`
--

CREATE TABLE `log_transaksi` (
  `log_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `aksi` varchar(50) NOT NULL,
  `waktu` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `log_transaksi`
--

INSERT INTO `log_transaksi` (`log_id`, `user_id`, `aksi`, `waktu`) VALUES
(1, 1, 'Membuat pemesanan', '2025-09-10 10:01:00'),
(2, 1, 'Melakukan pembayaran', '2025-09-10 11:00:00');

-- --------------------------------------------------------

--
-- Struktur dari tabel `notifikasi`
--

CREATE TABLE `notifikasi` (
  `notifikasi_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `pesan` text NOT NULL,
  `status_baca` enum('belum','sudah') NOT NULL,
  `waktu_kirim` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `notifikasi`
--

INSERT INTO `notifikasi` (`notifikasi_id`, `user_id`, `pesan`, `status_baca`, `waktu_kirim`) VALUES
(1, 1, 'Pembayaran Anda berhasil', 'sudah', '2025-09-10 11:01:00'),
(2, 2, 'Segera lakukan pembayaran', 'belum', '2025-09-12 15:05:00');

-- --------------------------------------------------------

--
-- Struktur dari tabel `pembayaran`
--

CREATE TABLE `pembayaran` (
  `pembayaran_id` int(11) NOT NULL,
  `pemesanan_id` int(11) NOT NULL,
  `metode_bayar` enum('transfer','e-wallet','qris') NOT NULL,
  `jumlah` decimal(10,0) NOT NULL,
  `tanggal_bayar` datetime NOT NULL,
  `status_bayar` enum('menunggu','berhasil','gagal') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `pembayaran`
--

INSERT INTO `pembayaran` (`pembayaran_id`, `pemesanan_id`, `metode_bayar`, `jumlah`, `tanggal_bayar`, `status_bayar`) VALUES
(1, 1, 'transfer', 25000, '2025-09-10 11:00:00', 'berhasil'),
(2, 2, 'qris', 25000, '2025-09-09 14:06:21', 'menunggu');

-- --------------------------------------------------------

--
-- Struktur dari tabel `pemesanan`
--

CREATE TABLE `pemesanan` (
  `pemesanan_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `tiket_id` int(11) NOT NULL,
  `tanggal_pesan` datetime NOT NULL,
  `status` enum('menunggu','berhasil','gagal') NOT NULL,
  `kuota_bulanan_berkurang` int(11) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `pemesanan`
--

INSERT INTO `pemesanan` (`pemesanan_id`, `user_id`, `tiket_id`, `tanggal_pesan`, `status`, `kuota_bulanan_berkurang`) VALUES
(1, 1, 1, '2025-09-10 10:00:00', 'berhasil', 1),
(2, 2, 2, '2025-09-12 15:00:00', 'menunggu', 1);

-- --------------------------------------------------------

--
-- Struktur dari tabel `pendaki`
--

CREATE TABLE `pendaki` (
  `pendaki_id` int(11) NOT NULL,
  `pemesanan_id` int(11) NOT NULL,
  `nama_pendaki` varchar(50) NOT NULL,
  `nik` varchar(50) NOT NULL,
  `tgl_lahir` date NOT NULL,
  `jenis_kelamin` enum('Laki','Perempuan') NOT NULL,
  `kontak_darurat` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `pendaki`
--

INSERT INTO `pendaki` (`pendaki_id`, `pemesanan_id`, `nama_pendaki`, `nik`, `tgl_lahir`, `jenis_kelamin`, `kontak_darurat`) VALUES
(1, 1, 'Nopal Berkabar', '3512345678', '2000-05-12', 'Laki', '081212121212'),
(2, 1, 'Budi Santoso', '3519876543', '1999-03-01', 'Laki', '081313131313'),
(3, 2, 'Amimir', '3515678912', '2001-07-20', 'Perempuan', '082414141414');

-- --------------------------------------------------------

--
-- Struktur dari tabel `peralatan_sewa`
--

CREATE TABLE `peralatan_sewa` (
  `peralatan_id` int(11) NOT NULL,
  `nama_peralatan` varchar(50) NOT NULL,
  `harga_sewa` decimal(10,0) NOT NULL,
  `stok` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `peralatan_sewa`
--

INSERT INTO `peralatan_sewa` (`peralatan_id`, `nama_peralatan`, `harga_sewa`, `stok`) VALUES
(1, 'Tenda 2 orang', 50000, 10),
(2, 'Sleeping Bag', 10000, 20),
(3, 'Carrier 60L', 30000, 15);

-- --------------------------------------------------------

--
-- Struktur dari tabel `porter`
--

CREATE TABLE `porter` (
  `porter_id` int(11) NOT NULL,
  `gunung_id` int(11) NOT NULL,
  `nama_porter` varchar(50) NOT NULL,
  `umur` int(11) NOT NULL,
  `pengalaman_tahun` int(11) NOT NULL,
  `kontak` varchar(50) NOT NULL,
  `status` enum('tersedia','sedang bertugas') NOT NULL,
  `harga_per_hari` decimal(10,0) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `porter`
--

INSERT INTO `porter` (`porter_id`, `gunung_id`, `nama_porter`, `umur`, `pengalaman_tahun`, `kontak`, `status`, `harga_per_hari`) VALUES
(1, 1, 'Suhari', 35, 10, '081999999999', 'tersedia', 200000),
(2, 1, 'Slamet', 28, 5, '082888888888', 'tersedia', 150000),
(3, 2, 'Dimas', 40, 15, '083777777777', 'sedang bertugas', 200000);

-- --------------------------------------------------------

--
-- Struktur dari tabel `punishment`
--

CREATE TABLE `punishment` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `violation` varchar(255) NOT NULL,
  `punishment` varchar(255) NOT NULL,
  `points` int(11) DEFAULT 0,
  `detail` text DEFAULT NULL,
  `date` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `rating_review`
--

CREATE TABLE `rating_review` (
  `review_id` int(11) NOT NULL,
  `pemesanan_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `rating` int(11) NOT NULL,
  `komentar` text NOT NULL,
  `tanggal_review` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `rating_review`
--

INSERT INTO `rating_review` (`review_id`, `pemesanan_id`, `user_id`, `rating`, `komentar`, `tanggal_review`) VALUES
(1, 1, 1, 5, 'Jalur bagus, bersih dan sedikit bikin istigfar', '2025-09-12 12:00:00');

-- --------------------------------------------------------

--
-- Struktur dari tabel `sewa_porter`
--

CREATE TABLE `sewa_porter` (
  `sewa_porter_id` int(11) NOT NULL,
  `pemesanan_id` int(11) NOT NULL,
  `porter_id` int(11) NOT NULL,
  `lama_sewa_hari` int(11) NOT NULL,
  `total_biaya` decimal(10,0) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `sewa_porter`
--

INSERT INTO `sewa_porter` (`sewa_porter_id`, `pemesanan_id`, `porter_id`, `lama_sewa_hari`, `total_biaya`) VALUES
(1, 1, 1, 2, 300000),
(2, 2, 2, 1, 120000);

-- --------------------------------------------------------

--
-- Struktur dari tabel `tiket`
--

CREATE TABLE `tiket` (
  `tiket_id` int(11) NOT NULL,
  `jalur_id` int(11) NOT NULL,
  `harga` decimal(10,0) NOT NULL,
  `kuota_harian` int(11) DEFAULT NULL,
  `tanggal_berlaku` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `tiket`
--

INSERT INTO `tiket` (`tiket_id`, `jalur_id`, `harga`, `kuota_harian`, `tanggal_berlaku`) VALUES
(1, 1, 25000, 100, '2025-09-20 00:00:00'),
(2, 2, 25000, 80, '2025-09-20 00:00:00'),
(3, 3, 85000, 50, '2025-09-21 00:00:00');

-- --------------------------------------------------------

--
-- Struktur dari tabel `user`
--

CREATE TABLE `user` (
  `user_id` int(11) NOT NULL,
  `email` varchar(50) NOT NULL,
  `password` varchar(50) NOT NULL,
  `nama` varchar(50) NOT NULL,
  `no_hp` varchar(50) NOT NULL,
  `nik` varchar(20) DEFAULT NULL COMMENT 'Nomor Identitas Kependudukan',
  `alamat` text NOT NULL,
  `role` varchar(50) NOT NULL DEFAULT 'user'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `user`
--

INSERT INTO `user` (`user_id`, `email`, `password`, `nama`, `no_hp`, `nik`, `alamat`, `role`) VALUES
(1, 'nopal@gmail.com', '54321', 'Nopal Berkabar', '082345678901', NULL, 'Madiun', 'user'),
(2, 'budi@gmail.com', '12345', 'Budi Santoso', '081234567890', NULL, 'Magetan', 'user'),
(3, 'amimir@gmail.com', '18276', 'Amimir', '0811111998', NULL, 'Ngawi', 'user'),
(9, 'mama@gmail.com', '123456', 'mama', '08111111111111111111111', NULL, '1111111111', 'user'),
(11, 'nakulasaputra08@gmail.com', '123456', 'Nakula Syafa Saputra', '085791686412', NULL, 'Dusun Sidorejo Rt03/Rw05 Desa Jeblogan Kecamatan Paron', 'user'),
(12, 'admin@gmail.com', 'admin123', 'Admin Utama', '08123', NULL, 'Kantor Pusat', 'admin'),
(15, '24111814116@mhs.unesa.ac.id', '123456', 'q', '1', NULL, '1', 'user'),
(17, 'nakulasaputra081@gmail.com', '123456', 'Nakula Syafa Saputra', '085791686412', '3521101205060001', 'Dusun Sidorejo Rt03/Rw05 Desa Jeblogan Kecamatan Paron', 'user');

--
-- Indexes for dumped tables
--

--
-- Indeks untuk tabel `anggota_pemesanan`
--
ALTER TABLE `anggota_pemesanan`
  ADD PRIMARY KEY (`anggota_id`),
  ADD KEY `pemesanan_id` (`pemesanan_id`),
  ADD KEY `user_id_anggota` (`user_id_anggota`);

--
-- Indeks untuk tabel `detail_sewa`
--
ALTER TABLE `detail_sewa`
  ADD PRIMARY KEY (`detail_sewa_id`),
  ADD KEY `pemesanan_id` (`pemesanan_id`),
  ADD KEY `peralatan_id` (`peralatan_id`);

--
-- Indeks untuk tabel `gunung`
--
ALTER TABLE `gunung`
  ADD PRIMARY KEY (`gunung_id`);

--
-- Indeks untuk tabel `jalur_pendakian`
--
ALTER TABLE `jalur_pendakian`
  ADD PRIMARY KEY (`jalur_id`),
  ADD KEY `gunung_id` (`gunung_id`);

--
-- Indeks untuk tabel `kuota_bulanan_user`
--
ALTER TABLE `kuota_bulanan_user`
  ADD PRIMARY KEY (`kuota_bulanan_user_id`),
  ADD UNIQUE KEY `user_id` (`user_id`,`tahun_bulan`);

--
-- Indeks untuk tabel `log_transaksi`
--
ALTER TABLE `log_transaksi`
  ADD PRIMARY KEY (`log_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indeks untuk tabel `notifikasi`
--
ALTER TABLE `notifikasi`
  ADD PRIMARY KEY (`notifikasi_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indeks untuk tabel `pembayaran`
--
ALTER TABLE `pembayaran`
  ADD PRIMARY KEY (`pembayaran_id`),
  ADD KEY `pemesanan_id` (`pemesanan_id`);

--
-- Indeks untuk tabel `pemesanan`
--
ALTER TABLE `pemesanan`
  ADD PRIMARY KEY (`pemesanan_id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `tiket_id` (`tiket_id`);

--
-- Indeks untuk tabel `pendaki`
--
ALTER TABLE `pendaki`
  ADD PRIMARY KEY (`pendaki_id`),
  ADD KEY `pemesanan_id` (`pemesanan_id`);

--
-- Indeks untuk tabel `peralatan_sewa`
--
ALTER TABLE `peralatan_sewa`
  ADD PRIMARY KEY (`peralatan_id`);

--
-- Indeks untuk tabel `porter`
--
ALTER TABLE `porter`
  ADD PRIMARY KEY (`porter_id`),
  ADD KEY `gunung_id` (`gunung_id`);

--
-- Indeks untuk tabel `punishment`
--
ALTER TABLE `punishment`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `rating_review`
--
ALTER TABLE `rating_review`
  ADD PRIMARY KEY (`review_id`),
  ADD KEY `pemesanan_id` (`pemesanan_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indeks untuk tabel `sewa_porter`
--
ALTER TABLE `sewa_porter`
  ADD PRIMARY KEY (`sewa_porter_id`),
  ADD KEY `pemesanan_id` (`pemesanan_id`),
  ADD KEY `porter_id` (`porter_id`);

--
-- Indeks untuk tabel `tiket`
--
ALTER TABLE `tiket`
  ADD PRIMARY KEY (`tiket_id`),
  ADD KEY `jalur_id` (`jalur_id`);

--
-- Indeks untuk tabel `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`user_id`);

--
-- AUTO_INCREMENT untuk tabel yang dibuang
--

--
-- AUTO_INCREMENT untuk tabel `anggota_pemesanan`
--
ALTER TABLE `anggota_pemesanan`
  MODIFY `anggota_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT untuk tabel `detail_sewa`
--
ALTER TABLE `detail_sewa`
  MODIFY `detail_sewa_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT untuk tabel `gunung`
--
ALTER TABLE `gunung`
  MODIFY `gunung_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT untuk tabel `jalur_pendakian`
--
ALTER TABLE `jalur_pendakian`
  MODIFY `jalur_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT untuk tabel `kuota_bulanan_user`
--
ALTER TABLE `kuota_bulanan_user`
  MODIFY `kuota_bulanan_user_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT untuk tabel `log_transaksi`
--
ALTER TABLE `log_transaksi`
  MODIFY `log_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT untuk tabel `notifikasi`
--
ALTER TABLE `notifikasi`
  MODIFY `notifikasi_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT untuk tabel `pembayaran`
--
ALTER TABLE `pembayaran`
  MODIFY `pembayaran_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT untuk tabel `pemesanan`
--
ALTER TABLE `pemesanan`
  MODIFY `pemesanan_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT untuk tabel `pendaki`
--
ALTER TABLE `pendaki`
  MODIFY `pendaki_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT untuk tabel `peralatan_sewa`
--
ALTER TABLE `peralatan_sewa`
  MODIFY `peralatan_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT untuk tabel `porter`
--
ALTER TABLE `porter`
  MODIFY `porter_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT untuk tabel `punishment`
--
ALTER TABLE `punishment`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT untuk tabel `rating_review`
--
ALTER TABLE `rating_review`
  MODIFY `review_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT untuk tabel `sewa_porter`
--
ALTER TABLE `sewa_porter`
  MODIFY `sewa_porter_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT untuk tabel `tiket`
--
ALTER TABLE `tiket`
  MODIFY `tiket_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT untuk tabel `user`
--
ALTER TABLE `user`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=18;

--
-- Ketidakleluasaan untuk tabel pelimpahan (Dumped Tables)
--

--
-- Ketidakleluasaan untuk tabel `detail_sewa`
--
ALTER TABLE `detail_sewa`
  ADD CONSTRAINT `detail_sewa_ibfk_1` FOREIGN KEY (`pemesanan_id`) REFERENCES `pemesanan` (`pemesanan_id`),
  ADD CONSTRAINT `detail_sewa_ibfk_2` FOREIGN KEY (`peralatan_id`) REFERENCES `peralatan_sewa` (`peralatan_id`);

--
-- Ketidakleluasaan untuk tabel `jalur_pendakian`
--
ALTER TABLE `jalur_pendakian`
  ADD CONSTRAINT `jalur_pendakian_ibfk_1` FOREIGN KEY (`gunung_id`) REFERENCES `gunung` (`gunung_id`);

--
-- Ketidakleluasaan untuk tabel `log_transaksi`
--
ALTER TABLE `log_transaksi`
  ADD CONSTRAINT `log_transaksi_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`);

--
-- Ketidakleluasaan untuk tabel `notifikasi`
--
ALTER TABLE `notifikasi`
  ADD CONSTRAINT `notifikasi_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`);

--
-- Ketidakleluasaan untuk tabel `pembayaran`
--
ALTER TABLE `pembayaran`
  ADD CONSTRAINT `pembayaran_ibfk_1` FOREIGN KEY (`pemesanan_id`) REFERENCES `pemesanan` (`pemesanan_id`);

--
-- Ketidakleluasaan untuk tabel `pemesanan`
--
ALTER TABLE `pemesanan`
  ADD CONSTRAINT `pemesanan_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`),
  ADD CONSTRAINT `pemesanan_ibfk_2` FOREIGN KEY (`tiket_id`) REFERENCES `tiket` (`tiket_id`);

--
-- Ketidakleluasaan untuk tabel `pendaki`
--
ALTER TABLE `pendaki`
  ADD CONSTRAINT `pendaki_ibfk_1` FOREIGN KEY (`pemesanan_id`) REFERENCES `pemesanan` (`pemesanan_id`);

--
-- Ketidakleluasaan untuk tabel `porter`
--
ALTER TABLE `porter`
  ADD CONSTRAINT `porter_ibfk_1` FOREIGN KEY (`gunung_id`) REFERENCES `gunung` (`gunung_id`);

--
-- Ketidakleluasaan untuk tabel `rating_review`
--
ALTER TABLE `rating_review`
  ADD CONSTRAINT `rating_review_ibfk_1` FOREIGN KEY (`pemesanan_id`) REFERENCES `pemesanan` (`pemesanan_id`),
  ADD CONSTRAINT `rating_review_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`);

--
-- Ketidakleluasaan untuk tabel `sewa_porter`
--
ALTER TABLE `sewa_porter`
  ADD CONSTRAINT `sewa_porter_ibfk_1` FOREIGN KEY (`pemesanan_id`) REFERENCES `pemesanan` (`pemesanan_id`),
  ADD CONSTRAINT `sewa_porter_ibfk_2` FOREIGN KEY (`porter_id`) REFERENCES `porter` (`porter_id`);

--
-- Ketidakleluasaan untuk tabel `tiket`
--
ALTER TABLE `tiket`
  ADD CONSTRAINT `tiket_ibfk_1` FOREIGN KEY (`jalur_id`) REFERENCES `jalur_pendakian` (`jalur_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
