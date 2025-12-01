# Quick Start: Google Maps Integration

## ✅ UPDATE: Sekarang GRATIS Menggunakan OpenStreetMap!

Tidak perlu API Key Google lagi! Menggunakan **OpenStreetMap + Leaflet** yang **100% GRATIS & UNLIMITED**.

## 2 Langkah Setup (Super Simple)

### Step 1: Update Database (1 menit)
Buka MySQL dan jalankan:
```sql
ALTER TABLE `gunung` ADD COLUMN `latitude` DECIMAL(10, 8) DEFAULT NULL;
ALTER TABLE `gunung` ADD COLUMN `longitude` DECIMAL(11, 8) DEFAULT NULL;
```

### Step 2: Sudah Selesai! ✅
Tidak perlu lagi setup API key atau config tambahan. Semua sudah included di kode!

## ✅ Done!

Sekarang Anda bisa:
- **Admin**: Input latitude & longitude saat tambah/edit gunung
- **User**: Lihat peta lokasi gunung di halaman detail (GRATIS, tanpa API key!)

## Dapat Koordinat Dari Mana?

### Cara 1: OpenStreetMap (Paling Mudah, Gratis)
```
1. Buka: https://www.openstreetmap.org
2. Cari nama gunung
3. Lihat URL bar - format: lat=X&lon=Y
4. Copy latitude & longitude
```

### Cara 2: Google Maps (Gratis, cuma cari)
```
1. Buka: https://maps.google.com
2. Cari nama gunung
3. Klik kanan pada lokasi
4. Pilih "Copy coordinates"
5. Paste di form latitude & longitude
```

### Cara 3: Coordinates Converter (Gratis)
```
https://www.gpscoordinates.net
- Cari gunung
- Copy latitude & longitude
```

## Contoh Koordinat Indonesia

| Gunung | Latitude | Longitude |
|--------|----------|-----------|
| Semeru | -7.5898 | 112.7064 |
| Bromo | -7.9424 | 112.9511 |
| Rinjani | -8.4181 | 116.3648 |
| Papandayan | -7.3164 | 107.2195 |
| Merapi | -7.5409 | 110.4426 |

## Troubleshooting

**Peta tidak muncul?**
- ✓ Apakah longitude/latitude sudah di input form?
- ✓ Format benar? (misal: -7.5898, bukan koma)
- ✓ Refresh browser (Ctrl+F5)

**Tidak ada error tapi peta blank?**
- Tunggu sebentar, peta sedang loading
- Check browser console (F12) untuk error message

## Keuntungan OpenStreetMap

✅ **100% GRATIS** - Selamanya gratis
✅ **Unlimited** - Request unlimited, tidak ada rate limit
✅ **Open Source** - Bisa customize kapan saja
✅ **Privacy** - Tidak tracking, lebih private
✅ **Community** - Peta dari komunitas worldwide

## Perbandingan

| | OpenStreetMap | Google Maps |
|---|---|---|
| **Biaya** | GRATIS ✅ | Berbayar ❌ |
| **Setup** | 2 menit ✅ | 15 menit ❌ |
| **Unlimited** | Ya ✅ | Terbatas ❌ |
| **Privacy** | Baik ✅ | Tracking ❌ |

## Referensi Lengkap
Lihat: `docs/GOOGLE_MAPS_SETUP.md`

## Yang Dimunculkan di Peta

- ✅ Marker merah untuk lokasi gunung
- ✅ Popup dengan detail gunung (nama, lokasi, ketinggian, koordinat)
- ✅ Zoom in/out
- ✅ Pan (drag peta)
- ✅ Attribution OpenStreetMap otomatis
