-- Migration: Add harga (ticket price) column to jalur_pendakian table
-- This allows per-jalur pricing (overrides gunung-level harga_tiket if set)

ALTER TABLE jalur_pendakian 
ADD COLUMN harga DECIMAL(10,2) DEFAULT NULL 
COMMENT 'Optional jalur-level ticket price per person; if set, overrides gunung harga_tiket for this jalur';

-- Note: This migration is optional. The app gracefully handles the absence of this column 
-- by falling back to gunung.harga_tiket if jalur.harga is not available.
