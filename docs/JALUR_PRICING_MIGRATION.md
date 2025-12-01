# Jalur-Level Pricing Integration - Summary

## Overview
Completed migration of ticket pricing from gunung-level to jalur-level, allowing each mountain route (jalur) to have independent pricing that overrides the base gunung price.

## Changes Made

### 1. Template Changes

#### templates/admin/tambah_jalur.html
- Added harga form field (optional, number input, step="0.01")
- Updated grid layout to accommodate new field alongside kuota_harian

#### templates/admin/edit_jalur.html
- Added harga form field with current value pre-populated
- Updated grid layout to match tambah_jalur.html
- Displays current harga value when editing

#### templates/user/detail_gunung.html
- Restructured to always show "Pesan" (booking) button per jalur
- Displays jalur images when available (gambar_jalur)
- Falls back to jalur.harga → jalur.harga_tiket → gunung.harga_tiket if no tiket rows exist
- Button remains visible but disabled if gunung is closed or jalur unavailable

### 2. Route Changes

#### routes/user.py (pemesanan_tiket function)

**GET request section (price_data building):**
- Updated harga_tiket_val calculation to check jalur_data.harga first
- Falls back to gunung.harga_tiket if jalur.harga not available or null
- Wrapped in try/except for safe value handling

**POST request section (booking calculation):**
- Updated harga_tiket calculation to use per_person_price from jalur or gunung
- Logic: if jalur_data exists and jalur.harga is set, use it; otherwise use gunung.harga_tiket
- Ensures correct total_harga calculation for booking

#### routes/admin.py (tambah_jalur & edit_jalur functions)

**tambah_jalur function:**
- Captures harga from request.form.get('harga') or None
- Attempts INSERT with harga column first (new schema)
- If harga column doesn't exist, catches exception and retries without harga
- Graceful fallback allows app to work on older DB schemas

**edit_jalur function:**
- Captures harga from request.form.get('harga') or None
- Attempts UPDATE with harga column first
- If harga column doesn't exist, catches exception and retries without harga
- Same graceful fallback pattern as tambah_jalur

### 3. Database Migration

#### migrations/20251201_add_harga_to_jalur.sql
```sql
ALTER TABLE jalur_pendakian 
ADD COLUMN harga DECIMAL(10,2) DEFAULT NULL 
COMMENT 'Optional jalur-level ticket price per person; if set, overrides gunung harga_tiket for this jalur';
```

**Status:** Optional - App works without this column due to fallback logic

### 4. Data Flow Diagram

```
User views detail page (GET /pemesanan/<gunung_id>)
  ↓
1. Fetch gunung data (includes harga_tiket as base price)
2. If jalur_id provided as query param, fetch jalur data (including optional harga)
3. Build price_data dict:
   - hargaTiket = jalur.harga (if exists) OR gunung.harga_tiket
4. Render template with price_data

User submits booking (POST /pemesanan/<gunung_id>)
  ↓
1. Calculate per_person_price = jalur.harga (if exists) OR gunung.harga_tiket
2. harga_tiket = per_person_price * jumlah_anggota
3. Calculate porter and alat costs
4. total_harga = harga_tiket + harga_porter + harga_alat
5. Insert pemesanan record with calculated totals

Admin adds/edits jalur
  ↓
1. Capture harga from form
2. INSERT/UPDATE jalur_pendakian with harga column
   - If column exists: success
   - If column missing: retry without harga, silently continue
```

## Backward Compatibility

All changes include graceful fallback:
- Template accepts both jalur.harga and jalur.harga_tiket (displays first available)
- Routes attempt with harga column, retry without if error
- price_data calculation works whether jalur.harga exists or not
- Old bookings still use gunung.harga_tiket if jalur.harga not set

## Testing Checklist

- [ ] Run migration: `migrations/20251201_add_harga_to_jalur.sql`
- [ ] Admin: Add new jalur with harga value, verify it saves
- [ ] Admin: Edit jalur, verify harga persists and displays
- [ ] User: View detail page for gunung with multi-jalur
- [ ] User: Check that each jalur shows correct price (jalur-specific if set)
- [ ] User: Complete booking with jalur-specific price
- [ ] User: Verify pemesanan_tiket stored correct harga_tiket amount
- [ ] Without migration: Verify fallback to gunung.harga_tiket works

## Files Modified

1. `templates/admin/tambah_jalur.html` - Added harga field
2. `templates/admin/edit_jalur.html` - Added harga field
3. `templates/user/detail_gunung.html` - Restructured pricing & button display
4. `routes/user.py` - Updated pemesanan_tiket to use jalur.harga
5. `routes/admin.py` - Updated tambah_jalur & edit_jalur with harga handling
6. `migrations/20251201_add_harga_to_jalur.sql` - New migration file (optional)

## Next Steps

1. Run DB migration to add harga column (optional but recommended)
2. Test complete workflow in dev environment
3. Admins can now set per-jalur pricing via admin panel
4. Users see correct jalur-specific prices on detail page
5. Booking calculations use jalur-level price when available
