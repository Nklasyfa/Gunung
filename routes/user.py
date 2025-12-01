from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from utils.decorators import login_required
from datetime import datetime
import calendar

user_bp = Blueprint('user', __name__)

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
                           active_page='home')

@user_bp.route('/profile')
@login_required
def profile():
    user_id = session['user_id']
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    cur.execute("SELECT user_id, email, nama, no_hp, alamat, role FROM user WHERE user_id = %s", [user_id])
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
            alamat = request.form.get('alamat', '').strip()

            # basic validation
            if not nama or not no_hp or not alamat:
                flash('Semua field harus diisi.', 'warning')
                return redirect(url_for('user.edit_profile'))

            try:
                cur.execute("UPDATE user SET nama=%s, no_hp=%s, alamat=%s WHERE user_id=%s",
                            (nama, no_hp, alamat, user_id))
                mysql.connection.commit()
                session['nama'] = nama
                flash('Profil berhasil diperbarui!', 'success')
                return redirect(url_for('user.profile'))
            except Exception as e:
                mysql.connection.rollback()
                current_app.logger.exception('Error updating profile')
                flash(f'Pembaruan Profil Gagal: {str(e)}', 'danger')
                return redirect(url_for('user.edit_profile'))

        cur.execute("SELECT user_id, email, nama, no_hp, alamat FROM user WHERE user_id = %s", [user_id])
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
            SELECT user_id, nama FROM user WHERE role = 'user' ORDER BY nama
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
            tanggal_pesan = request.form.get('tanggal_pesan')
            durasi = request.form.get('durasi', 1, type=int)
            aktivitas = request.form.get('aktivitas')  # 'tektok' atau 'camp'
            anggota_ids = request.form.getlist('anggota_ids')
            porter_ids = request.form.getlist('porter_id')
            alat_data_str = request.form.get('alat_id', '[]')
            
            # Parse equipment data from JSON
            import json
            try:
                alat_data = json.loads(alat_data_str) if alat_data_str != '[]' else []
            except:
                alat_data = []
            
            # Validation
            if not tanggal_pesan or not aktivitas:
                flash("Tanggal dan aktivitas harus dipilih.", "warning")
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
                # Calculate pricing
                jumlah_anggota = len(anggota_ids)
                # Use jalur-level price if available, otherwise fall back to gunung price
                per_person_price = 0
                if jalur_data and jalur_data.get('harga'):
                    per_person_price = float(jalur_data.get('harga') or 0)
                else:
                    per_person_price = float(gunung_data.get('harga_tiket') or 0)
                harga_tiket = per_person_price * jumlah_anggota
                harga_porter = 0
                harga_alat = 0
                
                # Calculate porter cost
                for porter_id in porter_ids:
                    cur.execute("SELECT harga_per_hari FROM porter WHERE porter_id = %s", [porter_id])
                    porter = cur.fetchone()
                    if porter:
                        harga_porter += float(porter['harga_per_hari']) * durasi
                
                # Calculate equipment cost (use peralatan_sewa table)
                for alat_str in alat_data:
                    if '_' in str(alat_str):
                        alat_id, jumlah = str(alat_str).split('_')
                        jumlah = int(jumlah) if jumlah else 0
                        if jumlah > 0:
                            cur.execute("SELECT harga_sewa FROM peralatan_sewa WHERE peralatan_id = %s", [alat_id])
                            alat = cur.fetchone()
                            if alat:
                                harga_alat += float(alat['harga_sewa']) * jumlah * durasi
                
                total_harga = harga_tiket + harga_porter + harga_alat
                
                # Insert pemesanan
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
                    cur.execute("""
                        SELECT user_id, nama FROM user WHERE user_id = %s
                    """, [anggota_id])
                    anggota = cur.fetchone()
                    if anggota:
                        cur.execute("""
                            INSERT INTO pemesanan_anggota (pemesanan_id, user_id, nama)
                            VALUES (%s, %s, %s)
                        """, (pemesanan_id, anggota['user_id'], anggota['nama']))
                
                # Insert porter assignments
                for porter_id in porter_ids:
                    cur.execute("SELECT harga_per_hari FROM porter WHERE porter_id = %s", [porter_id])
                    porter = cur.fetchone()
                    if porter:
                        cur.execute("""
                            INSERT INTO pemesanan_porter (pemesanan_id, porter_id, jumlah, harga_per_hari)
                            VALUES (%s, %s, 1, %s)
                        """, (pemesanan_id, porter_id, porter['harga_per_hari']))
                
                # Insert equipment (use peralatan_sewa table)
                for alat_str in alat_data:
                    if '_' in str(alat_str):
                        alat_id, jumlah = str(alat_str).split('_')
                        jumlah = int(jumlah) if jumlah else 0
                        if jumlah > 0:
                            cur.execute("SELECT harga_sewa FROM peralatan_sewa WHERE peralatan_id = %s", [alat_id])
                            alat = cur.fetchone()
                            if alat:
                                cur.execute("""
                                    INSERT INTO pemesanan_alat (pemesanan_id, alat_id, jumlah, harga_satuan)
                                    VALUES (%s, %s, %s, %s)
                                """, (pemesanan_id, alat_id, jumlah, alat['harga_sewa']))
                
                mysql.connection.commit()
                flash(f"Pemesanan berhasil dibuat! Total: Rp {total_harga:,.0f}", "success")
                return redirect(url_for('user.user_dashboard'))
                
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

    return render_template('user/pemesanan_tiket.html',
                           gunung=gunung_data,
                           users_list=users_list,
                           porter_list=porter_list,
                           alat_list=alat_list,
                           selected_jalur_id=selected_jalur_id,
                           price_data=price_data,
                           active_page='home')


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

            # fetch pemesanan for these tiket_ids
            pemesanan_rows = []
            if tiket_ids:
                placeholders = ', '.join(['%s'] * len(tiket_ids))
                query = f"SELECT pemesanan_id, tiket_id FROM pemesanan WHERE tiket_id IN ({placeholders}) AND status != 'gagal'"
                cur.execute(query, tuple(tiket_ids))
                pemesanan_rows = cur.fetchall()

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

            # compute used seats per tiket
            used_per_tiket = {}
            for p in pemesanan_rows:
                pid = p['pemesanan_id']
                tid = p['tiket_id']
                used_per_tiket.setdefault(tid, 0)
                used_per_tiket[tid] += 1 + int(anggota_count.get(pid, 0))

            # iterate dates
            last_day = calendar.monthrange(year, month)[1]
            for day in range(1, last_day + 1):
                dt = datetime(year, month, day)
                row = {'date': dt.strftime('%d-%m-%Y'), 'cells': []}
                for j in jalur_list:
                    key = (j['jalur_id'], dt.strftime('%Y-%m-%d'))
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
                        k = int(j.get('kuota_harian') or 0)
                        row['cells'].append(k if k > 0 else '-')
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

@user_bp.route('/ubah-bahasa/<lang>')
@login_required
def ubah_bahasa(lang):
    session['language'] = lang
    return redirect(request.referrer or url_for('user.user_dashboard'))
