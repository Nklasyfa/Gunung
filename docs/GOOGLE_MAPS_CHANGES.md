# Map Integration - Summary of Changes

## ✅ UPDATE: Menggunakan OpenStreetMap + Leaflet (GRATIS!)

Mengganti dari Google Maps API (berbayar) ke OpenStreetMap (gratis, unlimited, open-source)

## Files Modified/Created

### 1. Database
- **File**: `migrations/20251201_add_coordinates_to_gunung.sql`
- **Changes**: 
  - Tambah kolom `latitude` (DECIMAL 10,8)
  - Tambah kolom `longitude` (DECIMAL 11,8)

### 2. Routes (Backend)
- **File**: `routes/admin.py`
- **Functions Updated**:
  - `tambah_gunung()`: Terima latitude & longitude dari form
  - `edit_gunung()`: Update latitude & longitude saat edit

### 3. Admin Templates
- **File**: `templates/admin/tambah_gunung.html`
  - Tambah field: Latitude (number, step 0.0001)
  - Tambah field: Longitude (number, step 0.0001)

- **File**: `templates/admin/edit_gunung.html`
  - Tambah field: Latitude (dengan value default dari DB)
  - Tambah field: Longitude (dengan value default dari DB)

### 4. User Templates
- **File**: `templates/user/detail_gunung.html`
  - Tambah section: "Lokasi di Peta (OpenStreetMap)"
  - Tampil peta interaktif dengan OpenStreetMap
  - Marker merah dengan popup detail gunung
  - Library: Leaflet.js v1.9.4 (CDN)
  - Data peta: OpenStreetMap (gratis, community-driven)

### 5. Main App
- **File**: `app.py`
  - Hapus context processor (tidak perlu lagi)
  - Simplifikasi konfigurasi

### 6. Configuration
- **File**: `config.py`
  - Hapus `GOOGLE_MAPS_API_KEY` (tidak perlu lagi)

### 7. Documentation
- **File**: `docs/GOOGLE_MAPS_SETUP.md`
  - Update guide untuk OpenStreetMap
  - Perbandingan dengan Google Maps
  - Troubleshooting

- **File**: `docs/GOOGLE_MAPS_QUICK_START.md`
  - Setup hanya 2 langkah!
  - Tidak perlu API key
  - Tidak perlu konfigurasi

## What User Can Do Now

### Admin
1. **Tambah/Edit Gunung** dengan input:
   - Latitude (misal: -7.5898)
   - Longitude (misal: 112.7064)

### User
1. **Lihat Detail Gunung** dan akan muncul:
   - Peta interaktif OpenStreetMap (gratis, unlimited)
   - Marker merah lokasi gunung
   - Popup dengan info detail
   - Bisa zoom, pan (drag), dan scroll

## Setup Steps

1. **Run Migration**:
   ```sql
   ALTER TABLE `gunung` ADD COLUMN `latitude` DECIMAL(10, 8) DEFAULT NULL;
   ALTER TABLE `gunung` ADD COLUMN `longitude` DECIMAL(11, 8) DEFAULT NULL;
   ```

2. **Test**:
   - Tambah gunung dengan koordinat
   - Lihat di detail gunung - peta harus muncul

3. **Get Coordinates** dari:
   - OpenStreetMap (gratis, recommended)
   - Google Maps (gratis, cuma cari)
   - GPS Coordinates Tools (gratis)

## Coordinate Format

Input format untuk latitude dan longitude:
- **Latitude**: -90 to 90 (negatif untuk hemisphere selatan)
- **Longitude**: -180 to 180 (negatif untuk hemisphere barat)
- **Decimal Places**: Minimum 4 desimal untuk akurasi meter-level

Contoh Indonesia:
- Jakarta: -6.2088, 106.8456
- Yogyakarta: -7.7956, 110.3695
- Surabaya: -7.2504, 112.7688

## Keuntungan OpenStreetMap vs Google Maps

| Aspek | OpenStreetMap | Google Maps API |
|-------|---|---|
| **Biaya** | GRATIS ✅ | $5-7/1000 req ❌ |
| **Setup** | 2 menit ✅ | 15+ menit ❌ |
| **Request Limit** | Unlimited ✅ | Terbatas ❌ |
| **API Key** | Tidak perlu ✅ | Perlu ❌ |
| **Customization** | Tinggi ✅ | Tinggi ✅ |
| **Privacy** | Better ✅ | Tracking ❌ |
| **Open Source** | Ya ✅ | Proprietary ❌ |

## Libraries Used

```html
<!-- Leaflet CSS (styling peta) -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />

<!-- Leaflet JS (interaktivitas) -->
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<!-- Marker icon (dari GitHub, gratis) -->
https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png
```

Semua dari CDN publik, tidak perlu install!
