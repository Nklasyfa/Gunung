from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from utils.decorators import login_required
from datetime import datetime
import calendar

user_bp = Blueprint('user', __name__)


def _table_exists(cur, table_name):
    """Helper: cek apakah tabel ada di schema saat ini."""
    try:
        cur.execute("SELECT COUNT(*) as cnt FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = %s", [table_name])
        r = cur.fetchone()
        return int(r.get('cnt') or 0) > 0
    except Exception:
        return False

@user_bp.route('/home')
@login_required
def user_dashboard():
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT * FROM gunung ORDER BY nama_gunung")
        gunung_list = cur.fetchall()
    except Exception as e:
        gunung_list = [] 
        flash(f"Error mengambil data gunung: {e}", "danger") 
    finally:
        cur.close()
        
    return render_template('user/dashboard.html',
                           gunung_list=gunung_list,
                           user_nama=session.get('nama'),
                           active_page='home')

@user_bp.route('/gunung/<int:id>')
@login_required
def detail_gunung(id):
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    gunung_data = None
    jalur_list = []
    porter_list = []
    
    try:
        cur.execute("SELECT * FROM gunung WHERE gunung_id = %s", [id])
        gunung_data = cur.fetchone()
        
        if not gunung_data:
            flash("Gunung tidak ditemukan.", "danger")
            return redirect(url_for('user.user_dashboard'))
            
        cur.execute("SELECT * FROM jalur_pendakian WHERE gunung_id = %s", [id])
        jalur_list = cur.fetchall()
        
        # Get price range (min-max) for each jalur from tiket table
        jalur_price_range = {}
        for j in jalur_list:
            cur.execute("""
                SELECT MIN(harga) as min_harga, MAX(harga) as max_harga
                FROM tiket WHERE jalur_id = %s AND tanggal_berlaku >= CURDATE()
            """, [j['jalur_id']])
            price_data = cur.fetchone()
            if price_data and price_data.get('min_harga'):
                jalur_price_range[j['jalur_id']] = {
                    'min': int(price_data['min_harga']),
                    'max': int(price_data['max_harga'])
                }

        cur.execute("""
            SELECT t.*, j.nama_jalur
            FROM tiket t
            JOIN jalur_pendakian j ON t.jalur_id = j.jalur_id
            WHERE j.gunung_id = %s
            ORDER BY t.tanggal_berlaku DESC
        """, [id])
        tiket_list = cur.fetchall()

        cur.execute("SELECT * FROM porter WHERE gunung_id = %s AND status = 'tersedia'", [id])
        porter_list = cur.fetchall()
        
    except Exception as e:
        flash(f"Error mengambil detail gunung: {e}", "danger")
        return redirect(url_for('user.user_dashboard'))
    finally:
        cur.close()
        
    return render_template('user/detail_gunung.html',
                           gunung=gunung_data,
                           jalur_list=jalur_list,
                           tiket_list=tiket_list,
                           porter_list=porter_list,
                           jalur_price_range=jalur_price_range,
                           active_page='home')

@user_bp.route('/profile')
@login_required
def profile():
    user_id = session['user_id']
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    cur.execute("SELECT user_id, email, nama, no_hp, nik, alamat, role FROM user WHERE user_id = %s", [user_id])
    user_data = cur.fetchone()
    cur.close()
    
    return render_template('user/profile.html',
                           user=user_data,
                           active_page='profile')

@user_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user_id = session['user_id']
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    try:
        if request.method == 'POST':
            nama = request.form.get('nama', '').strip()
            no_hp = request.form.get('no_hp', '').strip()
            nik = request.form.get('nik', '').strip()
            alamat = request.form.get('alamat', '').strip()

            # basic validation
            if not nama or not no_hp or not nik or not alamat:
                flash('Semua field harus diisi.', 'warning')
                return redirect(url_for('user.edit_profile'))
            
            # Validate NIK format
            if not nik.isdigit() or len(nik) != 16:
                flash('NIK harus berupa 16 digit angka!', 'warning')
                return redirect(url_for('user.edit_profile'))

            try:
                cur.execute("UPDATE user SET nama=%s, no_hp=%s, nik=%s, alamat=%s WHERE user_id=%s",
                            (nama, no_hp, nik, alamat, user_id))
                mysql.connection.commit()
                session['nama'] = nama
                flash('Profil berhasil diperbarui!', 'success')
                return redirect(url_for('user.profile'))
            except Exception as e:
                mysql.connection.rollback()
                current_app.logger.exception('Error updating profile')
                flash(f'Pembaruan Profil Gagal: {str(e)}', 'danger')
                return redirect(url_for('user.edit_profile'))

        cur.execute("SELECT user_id, email, nama, no_hp, nik, alamat FROM user WHERE user_id = %s", [user_id])
        user_data = cur.fetchone()
    finally:
        try:
            cur.close()
        except Exception:
            pass

    return render_template('user/edit_profile.html',
                           user=user_data,
                           active_page='profile')

@user_bp.route('/profile/delete', methods=['POST'])
@login_required
def delete_account():
    user_id = session['user_id']
    mysql = current_app.mysql
    cur = mysql.connection.cursor()

    try:
        cur.execute("DELETE FROM user WHERE user_id = %s", [user_id])
        mysql.connection.commit()
        session.clear()
        flash('Akun Anda berhasil dihapus.', 'success')
        return redirect(url_for('auth.login'))
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Gagal menghapus akun: {str(e)}', 'danger')
        return redirect(url_for('user.profile'))
    finally:
        cur.close()

@user_bp.route('/pemesanan/<int:gunung_id>', methods=['GET', 'POST'])
@login_required
def pemesanan_tiket(gunung_id):
    """Form pemesanan dengan anggota, durasi, aktivitas, porter, dan alat"""
    user_id = session['user_id']
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    
    try:
        # Get gunung details dengan konfigurasi durasi
        cur.execute("""
            SELECT gunung_id, nama_gunung, harga_tiket, min_days, max_days 
            FROM gunung WHERE gunung_id = %s
        """, [gunung_id])
        gunung_data = cur.fetchone()
        
        if not gunung_data:
            flash("Gunung tidak ditemukan.", "danger")
            return redirect(url_for('user.user_dashboard'))
        
        # Get users (anggota) yang terdaftar
        cur.execute("""
            SELECT user_id, nama, nik, email, alamat FROM user WHERE role = 'user' ORDER BY nama
        """)
        users_list = cur.fetchall()
        
        # Get porter tersedia
        cur.execute("""
            SELECT porter_id, nama_porter, harga_per_hari FROM porter 
            WHERE gunung_id = %s AND status = 'tersedia' ORDER BY nama_porter
        """, [gunung_id])
        porter_list = cur.fetchall()
        
        # Get alat sewa dengan stok
        cur.execute("""
            SELECT peralatan_id, nama_peralatan, harga_sewa, stok 
            FROM peralatan_sewa WHERE stok > 0 ORDER BY nama_peralatan
        """)
        alat_list = cur.fetchall()

        # Get available tiket for this gunung (join with jalur name)
        cur.execute("""
            SELECT t.tiket_id, t.jalur_id, t.harga, DATE_FORMAT(t.tanggal_berlaku, '%%Y-%%m-%%d') as tdate, j.nama_jalur
            FROM tiket t
            JOIN jalur_pendakian j ON t.jalur_id = j.jalur_id
            WHERE j.gunung_id = %s
            ORDER BY t.tanggal_berlaku
        """, [gunung_id])
        tiket_list = list(cur.fetchall())
        # Sanitize for JSON serialization (Decimal -> float)
        for t in tiket_list:
            if 'harga' in t:
                try:
                    t['harga'] = float(t['harga'])
                except:
                    t['harga'] = 0.0
        
        # Allow optional jalur_id in querystring so front-end can deep-link from a specific jalur
        selected_jalur_id = request.args.get('jalur_id', type=int)
        
        # Try to load jalur-level info (including optional harga) when jalur_id provided
        jalur_data = None
        if selected_jalur_id:
            try:
                # Try with harga column if present
                cur.execute("SELECT jalur_id, nama_jalur, kuota_harian, estimasi, gambar_jalur, harga FROM jalur_pendakian WHERE jalur_id = %s", [selected_jalur_id])
                jalur_data = cur.fetchone()
            except Exception:
                # fallback: older schema without 'harga'
                try:
                    cur.execute("SELECT jalur_id, nama_jalur, kuota_harian, estimasi, gambar_jalur FROM jalur_pendakian WHERE jalur_id = %s", [selected_jalur_id])
                    jalur_data = cur.fetchone()
                except Exception:
                    jalur_data = None

        if request.method == 'POST':
            # Process booking
            # Client must submit a tiket_id (explicit date+jalur+harga)
            tiket_id = request.form.get('tiket_id', type=int)
            durasi = request.form.get('durasi', 1, type=int)
            aktivitas = request.form.get('aktivitas')  # 'tektok' atau 'camp'

            # Normalize anggota / porter inputs: the client sometimes submits a single
            # value (string or int) instead of a list. Ensure we always have a list
            # of string ids so iteration is safe.
            def _to_list(value):
                # value may be: None, list, comma-separated string, single string, or int
                if value is None:
                    return []
                if isinstance(value, list):
                    out = []
                    for v in value:
                        if isinstance(v, str) and ',' in v:
                            out.extend([s for s in v.split(',') if s != ''])
                        else:
                            out.append(str(v))
                    return out
                # single scalar
                if isinstance(value, (int, float)):
                    return [str(int(value))]
                if isinstance(value, str):
                    if value.strip() == '':
                        return []
                    if ',' in value:
                        return [s for s in value.split(',') if s != '']
                    return [value]
                try:
                    return list(value)
                except Exception:
                    return []

            anggota_ids = _to_list(request.form.getlist('anggota_ids') or request.form.get('anggota_ids'))
            porter_ids = _to_list(request.form.getlist('porter_id') or request.form.get('porter_id'))

            alat_data_str = request.form.get('alat_id', '[]')
            # Parse equipment data from JSON. The client may sometimes send a bare int
            # (e.g. "5") which json.loads will return as an int. Ensure alat_data is a list.
            import json
            try:
                alat_data = json.loads(alat_data_str) if alat_data_str not in (None, '') else []
            except Exception:
                # Fallback: if value looks like comma-separated ids (e.g. "1_2,3_1")
                try:
                    if isinstance(alat_data_str, str) and ',' in alat_data_str:
                        alat_data = [s for s in alat_data_str.split(',') if s != '']
                    else:
                        alat_data = [alat_data_str]
                except Exception:
                    alat_data = []
            # Ensure alat_data is iterable (list). If it's a single scalar, wrap it.
            if not isinstance(alat_data, list):
                if alat_data in (None, ''):
                    alat_data = []
                else:
                    alat_data = [alat_data]
            
            # Validation
            if not tiket_id:
                flash("Silakan pilih tiket (tanggal/jalur) terlebih dahulu.", "warning")
                return redirect(url_for('user.pemesanan_tiket', gunung_id=gunung_id))
            
            if not aktivitas:
                flash("Silakan pilih jenis aktivitas (Tektok atau Camp).", "warning")
                return redirect(url_for('user.pemesanan_tiket', gunung_id=gunung_id))

            
            # Use safe defaults if min/max not present
            min_days = int(gunung_data.get('min_days') or 1)
            max_days = int(gunung_data.get('max_days') or max(1, min_days))

            if durasi < min_days or durasi > max_days:
                flash(f"Durasi harus antara {min_days} - {max_days} hari.", "warning")
                return redirect(url_for('user.pemesanan_tiket', gunung_id=gunung_id))
            
            if not anggota_ids:
                flash("Minimal pilih 1 anggota.", "warning")
                return redirect(url_for('user.pemesanan_tiket', gunung_id=gunung_id))
            
            try:
                # Resolve tiket info (if provided) and Calculate pricing
                tiket_row = None
                if tiket_id:
                    try:
                        cur.execute("SELECT tiket_id, jalur_id, harga, tanggal_berlaku FROM tiket WHERE tiket_id = %s", [tiket_id])
                        tiket_row = cur.fetchone()
                    except Exception:
                        tiket_row = None

                # Calculate pricing
                # sanitize anggota_ids (remove empties) and compute count
                anggota_ids = [a for a in (anggota_ids or []) if str(a).strip() != '']
                jumlah_anggota = len(anggota_ids)
                # Prefer tiket-level price, then jalur-level, then gunung-level
                per_person_price = 0
                if tiket_row and tiket_row.get('harga') is not None:
                    try:
                        per_person_price = float(tiket_row.get('harga') or 0)
                    except Exception:
                        per_person_price = 0
                elif jalur_data and jalur_data.get('harga'):
                    per_person_price = float(jalur_data.get('harga') or 0)
                else:
                    per_person_price = float(gunung_data.get('harga_tiket') or 0)
                harga_tiket = per_person_price * jumlah_anggota
                harga_porter = 0
                harga_alat = 0
                
                # Calculate porter cost
                for porter_id in (porter_ids or []):
                    try:
                        cur.execute("SELECT harga_per_hari FROM porter WHERE porter_id = %s", [porter_id])
                        porter = cur.fetchone()
                        if porter:
                            harga_porter += float(porter.get('harga_per_hari') or 0) * durasi
                    except Exception:
                        # ignore individual porter lookup errors and continue
                        continue
                
                # Calculate equipment cost (use peralatan_sewa table)
                for alat_str in (alat_data or []):
                    try:
                        s = str(alat_str)
                        if '_' in s:
                            alat_id, jumlah = s.split('_')
                            jumlah = int(jumlah) if jumlah else 0
                            if jumlah > 0:
                                cur.execute("SELECT harga_sewa FROM peralatan_sewa WHERE peralatan_id = %s", [alat_id])
                                alat = cur.fetchone()
                                if alat:
                                    harga_alat += float(alat.get('harga_sewa') or 0) * jumlah * durasi
                        else:
                            # if client sent just an id as scalar, treat jumlah = 1
                            alat_id = s
                            jumlah = 1
                            cur.execute("SELECT harga_sewa FROM peralatan_sewa WHERE peralatan_id = %s", [alat_id])
                            alat = cur.fetchone()
                            if alat:
                                harga_alat += float(alat.get('harga_sewa') or 0) * jumlah * durasi
                    except Exception:
                        continue
                
                total_harga = harga_tiket + harga_porter + harga_alat
                
                # Insert pemesanan. The project has evolved and different DB schemas
                # exist: older code used `pemesanan_tiket` with many pricing columns;
                # your SQL dump uses `pemesanan`, `anggota_pemesanan`, `detail_sewa`,
                # and `sewa_porter`. Detect which table exists and adapt accordingly so
                # the app can work with your database without schema changes.

                def table_exists(table_name):
                    try:
                        cur.execute("SELECT COUNT(*) as cnt FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = %s", [table_name])
                        r = cur.fetchone()
                        return int(r.get('cnt') or 0) > 0
                    except Exception:
                        return False

                if table_exists('pemesanan_tiket'):
                    # current code path (keep backward compatible)
                    # ensure tanggal_pesan is defined (use current timestamp)
                    tanggal_pesan = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cur.execute("""
                        INSERT INTO pemesanan_tiket 
                        (user_id, gunung_id, tanggal_pesan, durasi, aktivitas, jumlah_anggota, 
                         harga_tiket, harga_porter, harga_alat, total_harga, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                    """, (user_id, gunung_id, tanggal_pesan, durasi, aktivitas, jumlah_anggota,
                          harga_tiket, harga_porter, harga_alat, total_harga))
                    mysql.connection.commit()
                    pemesanan_id = cur.lastrowid

                    # Insert anggota
                    for anggota_id in anggota_ids:
                        cur.execute("SELECT user_id, nama FROM user WHERE user_id = %s", [anggota_id])
                        anggota = cur.fetchone()
                        if anggota:
                            cur.execute("INSERT INTO pemesanan_anggota (pemesanan_id, user_id, nama) VALUES (%s, %s, %s)",
                                        (pemesanan_id, anggota['user_id'], anggota['nama']))

                    # Insert porter assignments
                    for porter_id in porter_ids:
                        cur.execute("SELECT harga_per_hari FROM porter WHERE porter_id = %s", [porter_id])
                        porter = cur.fetchone()
                        if porter:
                            cur.execute("INSERT INTO pemesanan_porter (pemesanan_id, porter_id, jumlah, harga_per_hari) VALUES (%s, %s, 1, %s)",
                                        (pemesanan_id, porter_id, porter['harga_per_hari']))

                    # Insert equipment (use peralatan_sewa table)
                    for alat_str in alat_data:
                        if '_' in str(alat_str):
                            alat_id, jumlah = str(alat_str).split('_')
                            jumlah = int(jumlah) if jumlah else 0
                            if jumlah > 0:
                                cur.execute("SELECT harga_sewa FROM peralatan_sewa WHERE peralatan_id = %s", [alat_id])
                                alat = cur.fetchone()
                                if alat:
                                    cur.execute("INSERT INTO pemesanan_alat (pemesanan_id, alat_id, jumlah, harga_satuan) VALUES (%s, %s, %s, %s)",
                                                (pemesanan_id, alat_id, jumlah, alat['harga_sewa']))

                    mysql.connection.commit()
                    # Redirect user to pembayaran page for this pemesanan
                    return redirect(url_for('user.pembayaran', pemesanan_id=pemesanan_id))
                else:
                    # Adapt to your provided schema (pemesanan + anggota_pemesanan + detail_sewa + sewa_porter)
                    # Use the tiket_id provided by the form and verify it exists.
                    try:
                        cur.execute("SELECT tiket_id, harga, tanggal_berlaku FROM tiket WHERE tiket_id = %s LIMIT 1", [tiket_id])
                        r = cur.fetchone()
                        if not r:
                            raise Exception('tiket_not_found')
                    except Exception:
                        mysql.connection.rollback()
                        flash('Tidak dapat menemukan tiket (tiket_id) untuk jalur/tanggal yang dipilih. Silakan pilih jalur/tanggal lain.', 'danger')
                        return redirect(url_for('user.pemesanan_tiket', gunung_id=gunung_id))

                    # Determine booking timestamp (use now) and prepare price columns if present
                    booking_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    tanggal_pesan_val = booking_time

                    # detect if pemesanan table has price columns
                    try:
                        cur.execute("SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'pemesanan' AND COLUMN_NAME IN ('harga_tiket','harga_porter','harga_alat','total_harga')")
                        existing_cols = [c.get('COLUMN_NAME') for c in cur.fetchall()]
                    except Exception:
                        existing_cols = []

                    cols = ['user_id','tiket_id','tanggal_pesan','status']
                    vals = [user_id, tiket_id, tanggal_pesan_val, 'menunggu']
                    
                    # Check if durasi column exists and add it
                    try:
                        cur.execute("SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'pemesanan' AND COLUMN_NAME = 'durasi'")
                        if cur.fetchone():
                            cols.append('durasi'); vals.append(durasi)
                    except Exception:
                        pass
                    
                    if 'harga_tiket' in existing_cols:
                        cols.append('harga_tiket'); vals.append(harga_tiket)
                    if 'harga_porter' in existing_cols:
                        cols.append('harga_porter'); vals.append(harga_porter)
                    if 'harga_alat' in existing_cols:
                        cols.append('harga_alat'); vals.append(harga_alat)
                    if 'total_harga' in existing_cols:
                        cols.append('total_harga'); vals.append(total_harga)

                    placeholders = ','.join(['%s'] * len(vals))
                    cols_sql = ','.join(cols)
                    cur.execute(f"INSERT INTO pemesanan ({cols_sql}) VALUES ({placeholders})", tuple(vals))
                    mysql.connection.commit()
                    pemesanan_id = cur.lastrowid

                    # Insert anggota into anggota_pemesanan (user_id_anggota)
                    for anggota_id in anggota_ids:
                        try:
                            cur.execute("INSERT INTO anggota_pemesanan (pemesanan_id, user_id_anggota) VALUES (%s, %s)", (pemesanan_id, anggota_id))
                        except Exception:
                            continue

                    # Insert sewa_porter entries
                    for porter_id in porter_ids:
                        try:
                            cur.execute("SELECT harga_per_hari FROM porter WHERE porter_id = %s", [porter_id])
                            p = cur.fetchone()
                            if p:
                                total_biaya = float(p.get('harga_per_hari') or 0) * durasi
                                cur.execute("INSERT INTO sewa_porter (pemesanan_id, porter_id, lama_sewa_hari, total_biaya) VALUES (%s, %s, %s, %s)",
                                            (pemesanan_id, porter_id, durasi, total_biaya))
                        except Exception:
                            continue

                    # Insert equipment into detail_sewa
                    for alat_str in (alat_data or []):
                        try:
                            s = str(alat_str)
                            if '_' in s:
                                alat_id, jumlah = s.split('_')
                                jumlah = int(jumlah) if jumlah else 0
                            else:
                                alat_id = s
                                jumlah = 1
                            if jumlah > 0:
                                cur.execute("SELECT harga_sewa FROM peralatan_sewa WHERE peralatan_id = %s", [alat_id])
                                a = cur.fetchone()
                                if a:
                                    subtotal = float(a.get('harga_sewa') or 0) * jumlah * durasi
                                    cur.execute("INSERT INTO detail_sewa (pemesanan_id, peralatan_id, jumlah, subtotal) VALUES (%s, %s, %s, %s)",
                                                (pemesanan_id, alat_id, jumlah, subtotal))
                        except Exception:
                            continue

                    # Kuota akan dihitung otomatis dari pemesanan yang ada
                    # Tidak perlu update tiket.kuota_harian karena sistem menghitung dynamically


                    mysql.connection.commit()
                    # Redirect to pembayaran so user can complete payment
                    return redirect(url_for('user.pembayaran', pemesanan_id=pemesanan_id))
                
            except Exception as e:
                mysql.connection.rollback()
                flash(f"Error saat membuat pemesanan: {str(e)}", "danger")
        
    except Exception as e:
        flash(f"Error saat mengambil data: {e}", "danger")
        return redirect(url_for('user.user_dashboard'))
    finally:
        cur.close()
    
    # Build safe price_data for client-side JS. Ensure only JSON-serializable primitives.
    try:
        # Use jalur-level price if available, otherwise fall back to gunung price
        if jalur_data and jalur_data.get('harga'):
            harga_tiket_val = float(jalur_data.get('harga') or 0)
        else:
            harga_tiket_val = float(gunung_data.get('harga_tiket') or 0)
    except Exception:
        harga_tiket_val = 0.0

    porters_map = {}
    for p in (porter_list or []):
        try:
            porters_map[str(p.get('porter_id'))] = float(p.get('harga_per_hari') or 0)
        except Exception:
            porters_map[str(p.get('porter_id'))] = 0.0

    alats_map = {}
    for a in (alat_list or []):
        try:
            alats_map[str(a.get('peralatan_id'))] = float(a.get('harga_sewa') or 0)
        except Exception:
            alats_map[str(a.get('peralatan_id'))] = 0.0

    price_data = {
        'hargaTiket': harga_tiket_val,
        'porters': porters_map,
        'alats': alats_map
    }
    # tiketPrices mapping for client-side lookup
    tiket_prices_map = {}
    for t in (locals().get('tiket_list') or []):
        try:
            tiket_prices_map[str(t.get('tiket_id'))] = float(t.get('harga') or 0)
        except Exception:
            tiket_prices_map[str(t.get('tiket_id'))] = 0.0
    price_data['tiketPrices'] = tiket_prices_map
    
    # Build users_data untuk client-side JS (untuk lookup user_id)
    users_data = {}
    for u in (users_list or []):
        try:
            users_data[str(u.get('user_id'))] = {
                'user_id': u.get('user_id'),
                'nama': u.get('nama') or '',
                'nik': u.get('nik') or '',
                'email': u.get('email') or '',
                'alamat': u.get('alamat') or ''
            }
        except Exception:
            pass

    return render_template('user/pemesanan_tiket.html',
                           gunung=gunung_data,
                           users_list=users_list,
                           porter_list=porter_list,
                           alat_list=alat_list,
                           tiket_list=locals().get('tiket_list', []),
                           selected_jalur_id=selected_jalur_id,
                           jalur_data=jalur_data,
                           price_data=price_data,
                           users_data=users_data,
                           active_page='home')


@user_bp.route('/pembayaran/<int:pemesanan_id>', methods=['GET', 'POST'])
@login_required
def pembayaran(pemesanan_id):
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    user_id = session['user_id']

    # verify ownership + load pemesanan (support legacy `pemesanan_tiket` or new `pemesanan` schema)
    pem = None
    if _table_exists(cur, 'pemesanan_tiket'):
        cur.execute("SELECT * FROM pemesanan_tiket WHERE pemesanan_id = %s", [pemesanan_id])
        pem = cur.fetchone()
    else:
        cur.execute("""
            SELECT p.*, t.harga as tiket_harga, t.tanggal_berlaku as tiket_tanggal, j.jalur_id, j.nama_jalur, g.gunung_id, g.nama_gunung
            FROM pemesanan p
            LEFT JOIN tiket t ON p.tiket_id = t.tiket_id
            LEFT JOIN jalur_pendakian j ON t.jalur_id = j.jalur_id
            LEFT JOIN gunung g ON j.gunung_id = g.gunung_id
            WHERE p.pemesanan_id = %s
        """, [pemesanan_id])
        pem = cur.fetchone()
        if pem:
            # jumlah_anggota: pemesan + anggota_pemesanan
            try:
                cur.execute("SELECT COUNT(*) as cnt FROM anggota_pemesanan WHERE pemesanan_id = %s", [pemesanan_id])
                r = cur.fetchone() or {'cnt': 0}
                anggota_cnt = int(r.get('cnt') or 0)
            except Exception:
                anggota_cnt = 0
            pem['jumlah_anggota'] = 1 + anggota_cnt
            # durasi may not be stored in new schema; default to 1
            try:
                pem['durasi'] = int(pem.get('durasi') or 1)
            except Exception:
                pem['durasi'] = 1
            # compute total_harga if missing
            try:
                if not pem.get('total_harga'):
                    tiket_price = float(pem.get('tiket_harga') or 0)
                    harga_tiket = tiket_price * pem['jumlah_anggota']
                    cur.execute("SELECT COALESCE(SUM(total_biaya),0) as s FROM sewa_porter WHERE pemesanan_id = %s", [pemesanan_id])
                    rp = cur.fetchone() or {'s': 0}
                    harga_porter = float(rp.get('s') or 0)
                    cur.execute("SELECT COALESCE(SUM(subtotal),0) as s FROM detail_sewa WHERE pemesanan_id = %s", [pemesanan_id])
                    ra = cur.fetchone() or {'s': 0}
                    harga_alat = float(ra.get('s') or 0)
                    pem['total_harga'] = harga_tiket + harga_porter + harga_alat
            except Exception:
                pem['total_harga'] = pem.get('total_harga') or 0

    if not pem or int(pem.get('user_id')) != int(user_id):
        cur.close()
        flash('Pemesanan tidak ditemukan atau Anda tidak berwenang.', 'danger')
        return redirect(url_for('user.riwayat_pemesanan'))

    if request.method == 'POST':
        metode = request.form.get('metode') or 'transfer'
        jumlah = float(pem.get('total_harga') or 0)
        try:
            cur.execute("INSERT INTO pembayaran (pemesanan_id, metode_bayar, jumlah, tanggal_bayar, status_bayar) VALUES (%s, %s, %s, NOW(), 'berhasil')",
                        (pemesanan_id, metode, jumlah))
            # update status depending on schema
            if _table_exists(cur, 'pemesanan_tiket'):
                cur.execute("UPDATE pemesanan_tiket SET status = 'berhasil' WHERE pemesanan_id = %s", [pemesanan_id])
            else:
                cur.execute("UPDATE pemesanan SET status = 'berhasil' WHERE pemesanan_id = %s", [pemesanan_id])
            mysql.connection.commit()
            flash('Pembayaran berhasil dicatat. Terima kasih!', 'success')
            return redirect(url_for('user.riwayat_pemesanan'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Gagal memproses pembayaran: {e}', 'danger')

    cur.close()
    return render_template('user/pembayaran.html', pemesanan=pem, active_page='home')


@user_bp.route('/riwayat')
@login_required
def riwayat_pemesanan():
    user_id = session['user_id']
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    try:
        if _table_exists(cur, 'pemesanan_tiket'):
            cur.execute("SELECT pt.*, g.nama_gunung FROM pemesanan_tiket pt LEFT JOIN gunung g ON pt.gunung_id = g.gunung_id WHERE pt.user_id = %s ORDER BY pt.pemesanan_id DESC", [user_id])
            rows = cur.fetchall()
        else:
            cur.execute("SELECT p.*, g.nama_gunung, t.tanggal_berlaku FROM pemesanan p LEFT JOIN tiket t ON p.tiket_id = t.tiket_id LEFT JOIN jalur_pendakian j ON t.jalur_id = j.jalur_id LEFT JOIN gunung g ON j.gunung_id = g.gunung_id WHERE p.user_id = %s ORDER BY p.pemesanan_id DESC", [user_id])
            rows = cur.fetchall()
    except Exception as e:
        rows = []
        flash(f'Error mengambil riwayat: {e}', 'danger')
    finally:
        cur.close()

    return render_template('user/riwayat_pemesanan.html', pemesanan_list=rows, active_page='riwayat_pemesanan')


@user_bp.route('/ticket/<int:pemesanan_id>/download')
@login_required
def download_ticket(pemesanan_id):
    user_id = session['user_id']
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    pem = None
    try:
        if _table_exists(cur, 'pemesanan_tiket'):
            cur.execute("SELECT pt.*, g.nama_gunung FROM pemesanan_tiket pt LEFT JOIN gunung g ON pt.gunung_id = g.gunung_id WHERE pt.pemesanan_id = %s", [pemesanan_id])
            pem = cur.fetchone()
        else:
            cur.execute("SELECT p.*, t.harga as tiket_harga, j.nama_jalur, g.nama_gunung FROM pemesanan p LEFT JOIN tiket t ON p.tiket_id = t.tiket_id LEFT JOIN jalur_pendakian j ON t.jalur_id = j.jalur_id LEFT JOIN gunung g ON j.gunung_id = g.gunung_id WHERE p.pemesanan_id = %s", [pemesanan_id])
            pem = cur.fetchone()
            if pem:
                try:
                    cur.execute("SELECT COUNT(*) as cnt FROM anggota_pemesanan WHERE pemesanan_id = %s", [pemesanan_id])
                    r = cur.fetchone() or {'cnt': 0}
                    anggota_cnt = int(r.get('cnt') or 0)
                except Exception:
                    anggota_cnt = 0
                # Use count directly - booker is already included in anggota_pemesanan
                # If no records, default to 1 (the booker)
                pem['jumlah_anggota'] = anggota_cnt if anggota_cnt > 0 else 1
                try:
                    pem['durasi'] = int(pem.get('durasi') or 1)
                except Exception:
                    pem['durasi'] = 1
                # compute total if missing
                try:
                    if not pem.get('total_harga'):
                        tiket_price = float(pem.get('tiket_harga') or 0)
                        harga_tiket = tiket_price * pem['jumlah_anggota']
                        cur.execute("SELECT COALESCE(SUM(total_biaya),0) as s FROM sewa_porter WHERE pemesanan_id = %s", [pemesanan_id])
                        rp = cur.fetchone() or {'s': 0}
                        harga_porter = float(rp.get('s') or 0)
                        cur.execute("SELECT COALESCE(SUM(subtotal),0) as s FROM detail_sewa WHERE pemesanan_id = %s", [pemesanan_id])
                        ra = cur.fetchone() or {'s': 0}
                        harga_alat = float(ra.get('s') or 0)
                        pem['total_harga'] = harga_tiket + harga_porter + harga_alat
                except Exception:
                    pem['total_harga'] = pem.get('total_harga') or 0
    finally:
        cur.close()

    if not pem or int(pem.get('user_id')) != int(user_id):
        flash('Pemesanan tidak ditemukan atau Anda tidak berwenang.', 'danger')
        return redirect(url_for('user.riwayat_pemesanan'))

    # Generate PDF ticket using fpdf2
    from fpdf import FPDF
    from io import BytesIO
    from flask import make_response
    
    class TicketPDF(FPDF):
        def header(self):
            self.set_font('Helvetica', 'B', 20)
            self.set_text_color(122, 57, 224)  # Purple color
            self.cell(0, 15, 'TIKET PENDAKIAN', align='C', new_x="LMARGIN", new_y="NEXT")
            self.set_font('Helvetica', '', 12)
            self.set_text_color(100, 100, 100)
            self.cell(0, 8, 'Sistem Pemesanan Tiket Gunung', align='C', new_x="LMARGIN", new_y="NEXT")
            self.ln(10)
        
        def footer(self):
            self.set_y(-25)
            self.set_font('Helvetica', 'I', 9)
            self.set_text_color(128, 128, 128)
            self.cell(0, 5, 'Silakan bawa tiket ini dalam bentuk cetak atau digital', align='C', new_x="LMARGIN", new_y="NEXT")
            self.cell(0, 5, 'saat melakukan registrasi di pos pendakian.', align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf = TicketPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=30)
    
    # Ticket Info Box
    pdf.set_fill_color(240, 244, 255)  # Light purple background
    pdf.set_draw_color(122, 57, 224)  # Purple border
    pdf.rect(10, pdf.get_y(), 190, 80, style='DF')
    
    y_start = pdf.get_y() + 5
    pdf.set_xy(15, y_start)
    
    # Ticket ID
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Tiket #{pem.get('pemesanan_id', '-')}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(15)
    
    pdf.ln(3)
    pdf.set_x(15)
    
    # Details
    pdf.set_font('Helvetica', '', 11)
    details = [
        ('Gunung', pem.get('nama_gunung') or str(pem.get('gunung_id', '-'))),
        ('Jalur', pem.get('nama_jalur', '-')),
        ('Tanggal Pesan', str(pem.get('tanggal_pesan', '-'))),
        ('Durasi', f"{pem.get('durasi', 1)} hari"),
        ('Jumlah Anggota', f"{pem.get('jumlah_anggota', 1)} orang"),
        ('Total Harga', f"Rp {int(pem.get('total_harga', 0)):,}"),
        ('Status', str(pem.get('status', '-')).upper()),
    ]
    
    for label, value in details:
        pdf.set_x(15)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(50, 7, f"{label}:", new_x="RIGHT")
        pdf.set_font('Helvetica', '', 11)
        pdf.cell(0, 7, str(value), new_x="LMARGIN", new_y="NEXT")
    
    # Output PDF
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    
    resp = make_response(pdf_output.read())
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = f'attachment; filename=tiket_{pemesanan_id}.pdf'
    return resp


@user_bp.route('/pemesanan/<int:pemesanan_id>/hapus', methods=['POST'])
@login_required
def hapus_pemesanan(pemesanan_id):
    """Hapus pemesanan dan kembalikan kuota"""
    user_id = session['user_id']
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    
    try:
        # Cek apakah pemesanan ada dan milik user ini
        if _table_exists(cur, 'pemesanan_tiket'):
            cur.execute("SELECT * FROM pemesanan_tiket WHERE pemesanan_id = %s AND user_id = %s", [pemesanan_id, user_id])
        else:
            cur.execute("SELECT p.*, t.jalur_id FROM pemesanan p LEFT JOIN tiket t ON p.tiket_id = t.tiket_id WHERE p.pemesanan_id = %s AND p.user_id = %s", [pemesanan_id, user_id])
        
        pemesanan = cur.fetchone()
        
        if not pemesanan:
            flash('Pemesanan tidak ditemukan atau Anda tidak berwenang.', 'danger')
            return redirect(url_for('user.riwayat_pemesanan'))
        
        # Kuota akan otomatis berkurang saat data pemesanan dihapus
        # Tidak perlu restore kuota karena sistem menghitung dynamically dari pemesanan yang ada
        
        # Hapus relasi terlebih dahulu (urutan penting untuk foreign key constraints)
        try:
            cur.execute("DELETE FROM anggota_pemesanan WHERE pemesanan_id = %s", [pemesanan_id])
        except Exception:
            pass
        
        try:
            cur.execute("DELETE FROM sewa_porter WHERE pemesanan_id = %s", [pemesanan_id])
        except Exception:
            pass
        
        try:
            cur.execute("DELETE FROM detail_sewa WHERE pemesanan_id = %s", [pemesanan_id])
        except Exception:
            pass
        
        try:
            # Hapus pembayaran jika ada
            cur.execute("DELETE FROM pembayaran WHERE pemesanan_id = %s", [pemesanan_id])
        except Exception:
            pass
        
        # Hapus pemesanan
        if _table_exists(cur, 'pemesanan_tiket'):
            cur.execute("DELETE FROM pemesanan_tiket WHERE pemesanan_id = %s", [pemesanan_id])
        else:
            cur.execute("DELETE FROM pemesanan WHERE pemesanan_id = %s", [pemesanan_id])
        
        mysql.connection.commit()
        flash('Pemesanan berhasil dihapus dan kuota telah dikembalikan.', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error menghapus pemesanan: {str(e)}', 'danger')
    finally:
        cur.close()
    
    return redirect(url_for('user.riwayat_pemesanan'))


@user_bp.route('/kuota-bulanan')
@login_required
def kuota_bulanan():
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    try:
        # parameters
        month = request.args.get('month', type=int) or datetime.now().month
        year = request.args.get('year', type=int) or datetime.now().year
        selected_gunung = request.args.get('gunung_id', type=int)

        # gunung list for selector
        try:
            cur.execute("SELECT gunung_id, nama_gunung FROM gunung ORDER BY nama_gunung")
            gunung_list = cur.fetchall()
        except Exception:
            gunung_list = []

        jalur_list = []
        table_rows = []

        if selected_gunung:
            # get jalur for gunung
            cur.execute("SELECT jalur_id, nama_jalur, kuota_harian FROM jalur_pendakian WHERE gunung_id = %s ORDER BY nama_jalur", [selected_gunung])
            jalur_list = cur.fetchall()

            jalur_ids = [j['jalur_id'] for j in jalur_list] if jalur_list else []

            # fetch tiket for all jalur in the month in one query
            tiket_map = {}  # (jalur_id, date) -> tiket dict
            if jalur_ids:
                placeholders = ', '.join(['%s'] * len(jalur_ids))
                query = f"""
                    SELECT tiket_id, jalur_id, kuota_harian, DATE(tanggal_berlaku) as tdate
                    FROM tiket
                    WHERE jalur_id IN ({placeholders}) AND YEAR(tanggal_berlaku) = %s AND MONTH(tanggal_berlaku) = %s
                    """
                params = tuple(jalur_ids) + (year, month)
                cur.execute(query, params)
                tiket_rows = cur.fetchall()
            else:
                tiket_rows = []

            # map tiket_id -> (jalur_id, date, kuota)
            tickets_by_id = {}
            for t in tiket_rows:
                # ensure tdate is a date/datetime
                tdate = t.get('tdate')
                if hasattr(tdate, 'strftime'):
                    tdate_str = tdate.strftime('%Y-%m-%d')
                else:
                    # fallback if string
                    try:
                        tdate_str = str(tdate)
                    except Exception:
                        tdate_str = ''
                key = (t['jalur_id'], tdate_str)
                tiket_map[key] = t
                tickets_by_id[t['tiket_id']] = t

            tiket_ids = list(tickets_by_id.keys())

            # fetch pemesanan for these tiket_ids (exclude only 'dibatalkan' status)
            pemesanan_rows = []
            if tiket_ids:
                placeholders = ', '.join(['%s'] * len(tiket_ids))
                # Include semua status kecuali dibatalkan/gagal
                query = f"SELECT pemesanan_id, tiket_id, status FROM pemesanan WHERE tiket_id IN ({placeholders}) AND status NOT IN ('dibatalkan', 'gagal')"
                cur.execute(query, tuple(tiket_ids))
                pemesanan_rows = cur.fetchall()
                print(f"DEBUG Kuota: Found {len(pemesanan_rows)} pemesanan for tiket_ids: {tiket_ids}")

            pemesanan_ids = [p['pemesanan_id'] for p in pemesanan_rows] if pemesanan_rows else []

            # fetch anggota counts per pemesanan
            anggota_count = {}
            if pemesanan_ids:
                placeholders = ', '.join(['%s'] * len(pemesanan_ids))
                query = f"SELECT pemesanan_id, COUNT(*) as cnt FROM anggota_pemesanan WHERE pemesanan_id IN ({placeholders}) GROUP BY pemesanan_id"
                cur.execute(query, tuple(pemesanan_ids))
                rows = cur.fetchall()
                for r in rows:
                    anggota_count[r['pemesanan_id']] = int(r['cnt'] or 0)
                print(f"DEBUG Kuota: anggota_count = {anggota_count}")

            # compute used seats per tiket
            used_per_tiket = {}
            for p in pemesanan_rows:
                pid = p['pemesanan_id']
                tid = p['tiket_id']
                used_per_tiket.setdefault(tid, 0)
                # anggota_count already includes ALL members (from anggota_pemesanan table)
                # Don't add 1, just use the count directly
                count = int(anggota_count.get(pid, 0))
                used_per_tiket[tid] += count
                print(f"DEBUG Kuota: pemesanan_id={pid}, tiket_id={tid}, anggota={count}, total_used={used_per_tiket[tid]}")


            # Only show dates that have ticket entries (not all days in month)
            # Collect all unique dates from tiket_map
            unique_dates = sorted(set(key[1] for key in tiket_map.keys()))
            
            for date_str in unique_dates:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                row = {'date': dt.strftime('%d-%m-%Y'), 'cells': []}
                for j in jalur_list:
                    key = (j['jalur_id'], date_str)
                    if key in tiket_map:
                        t = tiket_map[key]
                        tiket_id = t['tiket_id']
                        initial_quota = int(t.get('kuota_harian') or 0)
                        used = int(used_per_tiket.get(tiket_id, 0))
                        remaining = initial_quota - used
                        if remaining < 0:
                            remaining = 0
                        row['cells'].append(remaining)
                    else:
                        row['cells'].append('-')
                table_rows.append(row)

        months = [(i, datetime(year, i, 1).strftime('%B')) for i in range(1,13)]
        years = [year - 1, year, year + 1]

        return render_template('user/kuota_bulanan.html',
                               gunung_list=gunung_list,
                               jalur_list=jalur_list,
                               table_rows=table_rows,
                               selected_gunung=selected_gunung,
                               month=month,
                               year=year,
                               months=months,
                               years=years,
                               active_page='kuota_bulanan')
    except Exception as e:
        current_app.logger.exception('Error in kuota_bulanan')
        flash(f"Terjadi kesalahan saat mengambil data kuota: {e}", 'danger')
        return redirect(url_for('user.user_dashboard'))
    finally:
        try:
            cur.close()
        except Exception:
            pass

@user_bp.route('/bantuan')
@login_required
def bantuan():
    return render_template('user/bantuan.html', active_page='bantuan')

@user_bp.route('/punish')
@login_required
def punish():
    """Tampilan riwayat punish untuk user"""
    user_id = session['user_id']
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    
    try:
        cur.execute("""
            SELECT p.id, p.violation, p.punishment, p.points, p.detail, p.date
            FROM punishment p
            WHERE p.user_id = %s
            ORDER BY p.date DESC
        """, [user_id])
        punish_list = cur.fetchall()
    finally:
        cur.close()
    
    return render_template('user/punish.html', punish_list=punish_list, active_page='punish')
