-- Add latitude and longitude columns to gunung table
ALTER TABLE `gunung` ADD COLUMN `latitude` DECIMAL(10, 8) DEFAULT NULL COMMENT 'Latitude untuk Google Maps' AFTER `lokasi`;
ALTER TABLE `gunung` ADD COLUMN `longitude` DECIMAL(11, 8) DEFAULT NULL COMMENT 'Longitude untuk Google Maps' AFTER `latitude`;
