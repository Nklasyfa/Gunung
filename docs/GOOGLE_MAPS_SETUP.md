# Google Maps Integration Setup

## ⚠️ Update: Menggunakan OpenStreetMap (GRATIS!)

Saya sudah mengganti dari Google Maps API (berbayar) ke **OpenStreetMap + Leaflet** yang **GRATIS 100%**!

## Overview
Fitur ini menampilkan lokasi gunung di peta interaktif menggunakan OpenStreetMap (gratis, open-source).

## Setup Steps

### 1. ✅ Database Migration (Sama)

Jalankan migration file untuk menambah kolom latitude dan longitude:

```sql
ALTER TABLE `gunung` ADD COLUMN `latitude` DECIMAL(10, 8) DEFAULT NULL COMMENT 'Latitude untuk Peta' AFTER `lokasi`;
ALTER TABLE `gunung` ADD COLUMN `longitude` DECIMAL(11, 8) DEFAULT NULL COMMENT 'Longitude untuk Peta' AFTER `latitude`;
```

### 2. ✅ Sudah Included (Tidak perlu API Key!)

Tidak perlu lagi mendaftarkan API key di Google Cloud Console. Semua library sudah included:
- **Leaflet.js** - Library peta open-source
- **OpenStreetMap** - Data peta gratis

### 3. Update Configuration (Optional)

Jika di `config.py` masih ada baris Google Maps, bisa dihapus:

```python
# BISA DIHAPUS - sudah tidak perlu:
# GOOGLE_MAPS_API_KEY = 'YOUR_GOOGLE_MAPS_API_KEY_HERE'
```

## Features

### Admin Panel (Tetap Sama)
- **Tambah Gunung**: Input latitude dan longitude saat menambah gunung baru
- **Edit Gunung**: Perbarui koordinat gunung yang sudah ada
- Format input: Decimal (8 desimal untuk latitude, 11 untuk longitude)

### User Interface
- **Detail Gunung**: Tampil peta interaktif dengan marker lokasi gunung
- **Info Popup**: Klik marker untuk melihat detail gunung (nama, lokasi, ketinggian, koordinat)
- **Zoom & Pan**: User bisa zoom in/out dan pindah-pindah peta
- **Attribution**: Otomatis muncul credit OpenStreetMap
- **Responsive**: Peta menyesuaikan ukuran layar

## How to Use

### Admin Input Coordinates
1. Pergi ke Admin Panel → Data Gunung → Tambah/Edit
2. Isi field:
   - **Latitude**: Latitude lokasi gunung (format: -7.5898)
   - **Longitude**: Longitude lokasi gunung (format: 112.7064)
3. Simpan

### Finding Coordinates
Gunakan salah satu tools ini untuk mendapat koordinat:

1. **OpenStreetMap** (Gratis):
   - Buka https://www.openstreetmap.org
   - Cari nama gunung
   - Export → Copy coordinates

2. **Google Maps** (Gratis, cuma cari):
   - Buka https://maps.google.com
   - Cari nama gunung
   - Klik kanan pada lokasi → Copy coordinates

3. **GPS Coordinates Tools** (Gratis):
   - https://coordinates-converter.com
   - https://www.gpscoordinates.net

## Examples

### Gunung Semeru
- Lokasi: Jawa Timur
- Latitude: -7.5898
- Longitude: 112.7064

### Gunung Bromo
- Lokasi: Jawa Timur
- Latitude: -7.9424
- Longitude: 112.9511

### Gunung Rinjani
- Lokasi: Lombok, Nusa Tenggara Barat
- Latitude: -8.4181
- Longitude: 116.3648

## Troubleshooting

### Peta tidak tampil
- Check: Coordinates (latitude/longitude) valid dan terisi di database
- Check: Format koordinat benar (dengan titik desimal, bukan koma)
- Check: Refresh browser (Ctrl+F5)

### Error "Latitude/Longitude are required"
- Pastikan saat input data gunung, latitude dan longitude sudah diisi
- Periksa format: gunakan format decimal (misal: -7.5898, bukan D/M/S format)

## Keuntungan OpenStreetMap

✅ **100% GRATIS** - Tidak ada biaya
✅ **Open Source** - Bisa dimodifikasi sesuai kebutuhan
✅ **Unlimited Requests** - Tidak ada rate limit
✅ **Privacy Friendly** - Tidak tracking user
✅ **Community Driven** - Data peta dari komunitas
✅ **Multiple Map Layers** - Bisa ganti style peta

## Perbandingan dengan Google Maps

| Fitur | OpenStreetMap + Leaflet | Google Maps API |
|-------|-------------------------|-----------------|
| Biaya | **GRATIS** ✅ | Berbayar ❌ |
| Request Unlimited | Ya ✅ | Terbatas ❌ |
| Setup | Simple ✅ | Kompleks ❌ |
| API Key | Tidak perlu | Perlu |
| Customization | Tinggi | Tinggi |
| Stabilitas | Stabil | Stabil |

## Library yang Digunakan

```html
<!-- CSS untuk styling peta -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />

<!-- JavaScript untuk interaktivitas -->
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<!-- Marker icons warna -->
https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png
```

Semua dari CDN publik, tidak perlu install lokal!

## Future Enhancements

Fitur yang bisa ditambahkan:
- [ ] Multiple markers untuk berbagai jalur
- [ ] Routing dari lokasi user ke gunung
- [ ] Weather overlay
- [ ] Satellite view
- [ ] Draw area untuk coverage jalur
- [ ] Offline map caching

