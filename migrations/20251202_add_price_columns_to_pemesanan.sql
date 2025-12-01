-- Add price columns to pemesanan so totals can be stored
ALTER TABLE `pemesanan`
  ADD COLUMN `harga_tiket` decimal(10,0) DEFAULT 0,
  ADD COLUMN `harga_porter` decimal(10,0) DEFAULT 0,
  ADD COLUMN `harga_alat` decimal(10,0) DEFAULT 0,
  ADD COLUMN `total_harga` decimal(12,0) DEFAULT 0;
