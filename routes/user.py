from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from utils.decorators import login_required

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

    if request.method == 'POST':
        nama = request.form['nama']
        no_hp = request.form['no_hp']
        alamat = request.form['alamat']

        try:
            cur.execute("UPDATE user SET nama=%s, no_hp=%s, alamat=%s WHERE user_id=%s",
                        (nama, no_hp, alamat, user_id))
            mysql.connection.commit()
            session['nama'] = nama
            flash('Profil berhasil diperbarui!', 'success')
            return redirect(url_for('user.profile'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Pembaruan Profil Gagal: {str(e)}', 'danger')
            return redirect(url_for('user.edit_profile'))
    
    cur.execute("SELECT user_id, email, nama, no_hp, alamat FROM user WHERE user_id = %s", [user_id])
    user_data = cur.fetchone()
    cur.close()
    
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
                harga_tiket = float(gunung_data.get('harga_tiket') or 0) * jumlah_anggota
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

@user_bp.route('/bantuan')
@login_required
def bantuan():
    return render_template('user/bantuan.html', active_page='bantuan')

@user_bp.route('/ubah-bahasa/<lang>')
@login_required
def ubah_bahasa(lang):
    session['language'] = lang
    return redirect(request.referrer or url_for('user.user_dashboard'))
