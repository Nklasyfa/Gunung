from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
import os
import time
from utils.decorators import admin_required
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

# allowed extensions for uploaded images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file_storage, subfolder):
    """Save uploaded file to static/uploads/<subfolder> and return the saved relative filename.
    Returns None if no file was saved or file is not allowed.
    """
    if not file_storage:
        return None
    filename = file_storage.filename
    if filename == '':
        return None
    if not allowed_file(filename):
        return None

    uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads', subfolder)
    os.makedirs(uploads_dir, exist_ok=True)
    # make filename safer and unique
    filename = secure_filename(filename)
    name, ext = os.path.splitext(filename)
    timestamp = int(time.time())
    saved_name = f"{name}_{timestamp}{ext}"
    save_path = os.path.join(uploads_dir, saved_name)
    file_storage.save(save_path)
    # return only the saved filename (we'll prefix uploads/<subfolder>/ in templates)
    return saved_name

@admin_bp.route('/')
@admin_required
def admin_dashboard():
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) as total_gunung FROM gunung")
    total_gunung = cur.fetchone()['total_gunung']
    cur.execute("SELECT COUNT(*) as total_user FROM user WHERE role = 'user'")
    total_user = cur.fetchone()['total_user']
    cur.close()
    
    return render_template('admin/dashboard.html',
                           active_page='admin_dashboard',
                           total_gunung=total_gunung,
                           total_user=total_user)

# === GUNUNG CRUD ===
@admin_bp.route('/gunung')
@admin_required
def gunung():
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM gunung ORDER BY nama_gunung")
    gunung_list = cur.fetchall()
    cur.close()
    return render_template('admin/gunung.html',
                           gunung_list=gunung_list,
                           active_page='gunung')

@admin_bp.route('/gunung/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_gunung():
    if request.method == 'POST':
        nama_gunung = request.form['nama_gunung']
        lokasi = request.form['lokasi']
        ketinggian = request.form['ketinggian']
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        status = request.form['status_pendakian']
        deskripsi = request.form['deskripsi']
        sejarah = request.form['sejarah']
        # estimasi_waktu and kuota_harian moved to jalur_pendakian level
        harga_tiket = request.form.get('harga_tiket', 0)
        min_days = request.form.get('min_days', 1, type=int)
        max_days = request.form.get('max_days', 2, type=int)
        # handle file upload
        gambar_file = request.files.get('gambar')
        gambar_path = save_uploaded_file(gambar_file, 'gunung')
        
        mysql = current_app.mysql
        cur = mysql.connection.cursor()
        try:
            if gambar_path:
                cur.execute("""
                    INSERT INTO gunung (nama_gunung, lokasi, latitude, longitude, ketinggian, status_pendakian, deskripsi, sejarah, harga_tiket, min_days, max_days, gambar) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (nama_gunung, lokasi, latitude, longitude, ketinggian, status, deskripsi, sejarah, harga_tiket, min_days, max_days, gambar_path))
            else:
                cur.execute("""
                    INSERT INTO gunung (nama_gunung, lokasi, latitude, longitude, ketinggian, status_pendakian, deskripsi, sejarah, harga_tiket, min_days, max_days) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (nama_gunung, lokasi, latitude, longitude, ketinggian, status, deskripsi, sejarah, harga_tiket, min_days, max_days))
            mysql.connection.commit()
            flash(f'Gunung {nama_gunung} berhasil ditambahkan!', 'success')
            return redirect(url_for('admin.gunung'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Gagal menambah gunung: {str(e)}', 'danger')
        finally:
            cur.close()
            
    return render_template('admin/tambah_gunung.html', active_page='gunung')

@admin_bp.route('/gunung/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_gunung(id):
    mysql = current_app.mysql

    if request.method == 'POST':
        # use a dedicated cursor for POST handling
        cur = mysql.connection.cursor()
        nama_gunung = request.form['nama_gunung']
        lokasi = request.form['lokasi']
        ketinggian = request.form['ketinggian']
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        status = request.form['status_pendakian']
        deskripsi = request.form['deskripsi']
        sejarah = request.form['sejarah']
        # estimasi_waktu and kuota_harian moved to jalur_pendakian level
        harga_tiket = request.form.get('harga_tiket', 0)
        min_days = request.form.get('min_days', 1, type=int)
        max_days = request.form.get('max_days', 2, type=int)
        # handle file upload
        gambar_file = request.files.get('gambar')
        gambar_path = save_uploaded_file(gambar_file, 'gunung')

        try:
            if gambar_path:
                cur.execute("""
                    UPDATE gunung SET 
                    nama_gunung=%s, lokasi=%s, latitude=%s, longitude=%s, ketinggian=%s, status_pendakian=%s, 
                    deskripsi=%s, sejarah=%s, harga_tiket=%s, min_days=%s, max_days=%s, gambar=%s
                    WHERE gunung_id=%s
                """, (nama_gunung, lokasi, latitude, longitude, ketinggian, status, deskripsi, sejarah, harga_tiket, min_days, max_days, gambar_path, id))
            else:
                cur.execute("""
                    UPDATE gunung SET 
                    nama_gunung=%s, lokasi=%s, latitude=%s, longitude=%s, ketinggian=%s, status_pendakian=%s, 
                    deskripsi=%s, sejarah=%s, harga_tiket=%s, min_days=%s, max_days=%s
                    WHERE gunung_id=%s
                """, (nama_gunung, lokasi, latitude, longitude, ketinggian, status, deskripsi, sejarah, harga_tiket, min_days, max_days, id))
            mysql.connection.commit()
            flash(f'Data Gunung {nama_gunung} berhasil diperbarui!', 'success')
            return redirect(url_for('admin.gunung'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Gagal memperbarui gunung: {str(e)}', 'danger')
        finally:
            cur.close()

    # GET: fetch gunung data with its own cursor
    cur_get = mysql.connection.cursor()
    cur_get.execute("SELECT * FROM gunung WHERE gunung_id = %s", [id])
    gunung_data = cur_get.fetchone()
    cur_get.close()
    
    if not gunung_data:
        flash('Data gunung tidak ditemukan.', 'danger')
        return redirect(url_for('admin.gunung'))
        
    return render_template('admin/edit_gunung.html',
                           gunung=gunung_data,
                           active_page='gunung')

@admin_bp.route('/gunung/hapus/<int:id>', methods=['POST'])
@admin_required
def hapus_gunung(id):
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM gunung WHERE gunung_id = %s", [id])
        mysql.connection.commit()
        flash('Data gunung berhasil dihapus.', 'success')
    except Exception as e:
        mysql.connection.rollback()
        if '1451' in str(e):
            flash('Gagal menghapus gunung. Data ini terhubung dengan data lain (misal: tiket atau jalur).', 'danger')
        else:
            flash(f'Gagal menghapus gunung: {str(e)}', 'danger')
    finally:
        cur.close()
    
    return redirect(url_for('admin.gunung'))


# === JALUR PENDAKIAN CRUD ===
@admin_bp.route('/jalur')
@admin_required
def jalur():
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT j.*, g.nama_gunung FROM jalur_pendakian j
        JOIN gunung g ON j.gunung_id = g.gunung_id
        ORDER BY j.jalur_id DESC
    """)
    jalur_list = cur.fetchall()
    cur.close()
    return render_template('admin/jalur.html', jalur_list=jalur_list, active_page='jalur')


@admin_bp.route('/jalur/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_jalur():
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        gunung_id = request.form['gunung_id']
        nama_jalur = request.form['nama_jalur']
        deskripsi = request.form.get('deskripsi', '')
        estimasi = request.form.get('estimasi', '')
        kuota_harian = request.form.get('kuota_harian') or 0
        tingkat_kesulitan = request.form.get('tingkat_kesulitan', 'sedang')
        # tersedia expected as '1' or '0' from form
        tersedia = int(request.form.get('tersedia', '1'))
        harga = request.form.get('harga') or None
        gambar_file = request.files.get('gambar_jalur')
        gambar_path = save_uploaded_file(gambar_file, 'jalur')

        try:
            # Try with harga column first
            if gambar_path:
                cur.execute("""
                    INSERT INTO jalur_pendakian (gunung_id, nama_jalur, deskripsi, estimasi, gambar_jalur, tingkat_kesulitan, tersedia, kuota_harian, harga)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (gunung_id, nama_jalur, deskripsi, estimasi, gambar_path, tingkat_kesulitan, tersedia, kuota_harian, harga))
            else:
                cur.execute("""
                    INSERT INTO jalur_pendakian (gunung_id, nama_jalur, deskripsi, estimasi, tingkat_kesulitan, tersedia, kuota_harian, harga)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (gunung_id, nama_jalur, deskripsi, estimasi, tingkat_kesulitan, tersedia, kuota_harian, harga))
            mysql.connection.commit()
            flash(f'Jalur {nama_jalur} berhasil ditambahkan!', 'success')
            return redirect(url_for('admin.jalur'))
        except Exception as e:
            # If harga column doesn't exist, retry without it
            try:
                mysql.connection.rollback()
                if gambar_path:
                    cur.execute("""
                        INSERT INTO jalur_pendakian (gunung_id, nama_jalur, deskripsi, estimasi, gambar_jalur, tingkat_kesulitan, tersedia, kuota_harian)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (gunung_id, nama_jalur, deskripsi, estimasi, gambar_path, tingkat_kesulitan, tersedia, kuota_harian))
                else:
                    cur.execute("""
                        INSERT INTO jalur_pendakian (gunung_id, nama_jalur, deskripsi, estimasi, tingkat_kesulitan, tersedia, kuota_harian)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (gunung_id, nama_jalur, deskripsi, estimasi, tingkat_kesulitan, tersedia, kuota_harian))
                mysql.connection.commit()
                flash(f'Jalur {nama_jalur} berhasil ditambahkan!', 'success')
                return redirect(url_for('admin.jalur'))
            except Exception as e2:
                mysql.connection.rollback()
                flash(f'Gagal menambah jalur: {str(e2)}', 'danger')
        finally:
            cur.close()

    # GET -> show form
    cur.execute("SELECT gunung_id, nama_gunung FROM gunung ORDER BY nama_gunung")
    gunung_list = cur.fetchall()
    cur.close()
    return render_template('admin/tambah_jalur.html', gunung_list=gunung_list, active_page='jalur')


@admin_bp.route('/jalur/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_jalur(id):
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        gunung_id = request.form['gunung_id']
        nama_jalur = request.form['nama_jalur']
        deskripsi = request.form.get('deskripsi', '')
        estimasi = request.form.get('estimasi', '')
        kuota_harian = request.form.get('kuota_harian') or 0
        tingkat_kesulitan = request.form.get('tingkat_kesulitan', 'sedang')
        tersedia = int(request.form.get('tersedia', '1'))
        harga = request.form.get('harga') or None
        gambar_file = request.files.get('gambar_jalur')
        gambar_path = save_uploaded_file(gambar_file, 'jalur')

        try:
            if gambar_path:
                cur.execute("""
                    UPDATE jalur_pendakian SET gunung_id=%s, nama_jalur=%s, deskripsi=%s, estimasi=%s, gambar_jalur=%s, tingkat_kesulitan=%s, tersedia=%s, kuota_harian=%s, harga=%s
                    WHERE jalur_id=%s
                """, (gunung_id, nama_jalur, deskripsi, estimasi, gambar_path, tingkat_kesulitan, tersedia, kuota_harian, harga, id))
            else:
                cur.execute("""
                    UPDATE jalur_pendakian SET gunung_id=%s, nama_jalur=%s, deskripsi=%s, estimasi=%s, tingkat_kesulitan=%s, tersedia=%s, kuota_harian=%s, harga=%s
                    WHERE jalur_id=%s
                """, (gunung_id, nama_jalur, deskripsi, estimasi, tingkat_kesulitan, tersedia, kuota_harian, harga, id))
            mysql.connection.commit()
            flash(f'Jalur {nama_jalur} berhasil diperbarui!', 'success')
            return redirect(url_for('admin.jalur'))
        except Exception as e:
            # If harga column doesn't exist, retry without it
            try:
                mysql.connection.rollback()
                if gambar_path:
                    cur.execute("""
                        UPDATE jalur_pendakian SET gunung_id=%s, nama_jalur=%s, deskripsi=%s, estimasi=%s, gambar_jalur=%s, tingkat_kesulitan=%s, tersedia=%s, kuota_harian=%s
                        WHERE jalur_id=%s
                    """, (gunung_id, nama_jalur, deskripsi, estimasi, gambar_path, tingkat_kesulitan, tersedia, kuota_harian, id))
                else:
                    cur.execute("""
                        UPDATE jalur_pendakian SET gunung_id=%s, nama_jalur=%s, deskripsi=%s, estimasi=%s, tingkat_kesulitan=%s, tersedia=%s, kuota_harian=%s
                        WHERE jalur_id=%s
                    """, (gunung_id, nama_jalur, deskripsi, estimasi, tingkat_kesulitan, tersedia, kuota_harian, id))
                mysql.connection.commit()
                flash(f'Jalur {nama_jalur} berhasil diperbarui!', 'success')
                return redirect(url_for('admin.jalur'))
            except Exception as e2:
                mysql.connection.rollback()
                flash(f'Gagal memperbarui jalur: {str(e2)}', 'danger')
        finally:
            cur.close()

    cur.execute("SELECT * FROM jalur_pendakian WHERE jalur_id = %s", [id])
    jalur_data = cur.fetchone()
    if not jalur_data:
        cur.close()
        flash('Jalur tidak ditemukan.', 'danger')
        return redirect(url_for('admin.jalur'))

    cur.execute("SELECT gunung_id, nama_gunung FROM gunung ORDER BY nama_gunung")
    gunung_list = cur.fetchall()
    cur.close()
    return render_template('admin/edit_jalur.html', jalur=jalur_data, gunung_list=gunung_list, active_page='jalur')


@admin_bp.route('/jalur/hapus/<int:id>', methods=['POST'])
@admin_required
def hapus_jalur(id):
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM jalur_pendakian WHERE jalur_id = %s", [id])
        mysql.connection.commit()
        flash('Jalur berhasil dihapus.', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Gagal menghapus jalur: {str(e)}', 'danger')
    finally:
        cur.close()

    return redirect(url_for('admin.jalur'))

# === PORTER CRUD ===
@admin_bp.route('/porter')
@admin_required
def porter():
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT p.*, g.nama_gunung 
        FROM porter p
        JOIN gunung g ON p.gunung_id = g.gunung_id
        ORDER BY p.porter_id DESC
    """)
    porter_list = cur.fetchall()
    cur.close()
    return render_template('admin/porter.html',
                           porter_list=porter_list,
                           active_page='porter')

@admin_bp.route('/porter/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_porter():
    mysql = current_app.mysql
    
    if request.method == 'POST':
        nama_porter = request.form['nama_porter']
        no_hp = request.form['no_hp']
        gunung_id = request.form['gunung_id']
        tarif_harian = request.form['tarif_harian']
        
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO porter (nama_porter, no_hp, gunung_id, tarif_harian, status) 
                VALUES (%s, %s, %s, %s, 'tersedia')
            """, (nama_porter, no_hp, gunung_id, tarif_harian))
            mysql.connection.commit()
            flash(f'Porter {nama_porter} berhasil ditambahkan!', 'success')
            return redirect(url_for('admin.porter'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Gagal menambah porter: {str(e)}', 'danger')
        finally:
            cur.close()
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM gunung ORDER BY nama_gunung")
    gunung_list = cur.fetchall()
    cur.close()
    
    return render_template('admin/tambah_porter.html', 
                           gunung_list=gunung_list,
                           active_page='porter')

@admin_bp.route('/porter/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_porter(id):
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        nama_porter = request.form['nama_porter']
        no_hp = request.form['no_hp']
        gunung_id = request.form['gunung_id']
        tarif_harian = request.form['tarif_harian']
        status = request.form.get('status', 'tersedia')
        
        try:
            cur.execute("""
                UPDATE porter SET 
                nama_porter=%s, no_hp=%s, gunung_id=%s, tarif_harian=%s, status=%s
                WHERE porter_id=%s
            """, (nama_porter, no_hp, gunung_id, tarif_harian, status, id))
            mysql.connection.commit()
            flash(f'Porter {nama_porter} berhasil diperbarui!', 'success')
            return redirect(url_for('admin.porter'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Gagal memperbarui porter: {str(e)}', 'danger')
        finally:
            cur.close()
    
    cur.execute("SELECT * FROM porter WHERE porter_id = %s", [id])
    porter_data = cur.fetchone()
    
    if not porter_data:
        flash('Porter tidak ditemukan.', 'danger')
        return redirect(url_for('admin.porter'))
    
    cur.execute("SELECT * FROM gunung ORDER BY nama_gunung")
    gunung_list = cur.fetchall()
    cur.close()
    
    return render_template('admin/edit_porter.html',
                           porter=porter_data,
                           gunung_list=gunung_list,
                           active_page='porter')

@admin_bp.route('/porter/hapus/<int:id>', methods=['POST'])
@admin_required
def hapus_porter(id):
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM porter WHERE porter_id = %s", [id])
        mysql.connection.commit()
        flash('Porter berhasil dihapus.', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Gagal menghapus porter: {str(e)}', 'danger')
    finally:
        cur.close()
    
    return redirect(url_for('admin.porter'))

@admin_bp.route('/peralatan/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_peralatan():
    mysql = current_app.mysql
    
    if request.method == 'POST':
        nama_peralatan = request.form['nama_peralatan']
        deskripsi = request.form.get('deskripsi', '')
        harga_sewa = request.form['harga_sewa']
        stok = request.form['stok']
        
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO peralatan_sewa (nama_peralatan, deskripsi, harga_sewa, stok) 
                VALUES (%s, %s, %s, %s)
            """, (nama_peralatan, deskripsi, harga_sewa, stok))
            mysql.connection.commit()
            flash(f'Peralatan {nama_peralatan} berhasil ditambahkan!', 'success')
            return redirect(url_for('admin.peralatan'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Gagal menambah peralatan: {str(e)}', 'danger')
        finally:
            cur.close()
    
    return render_template('admin/tambah_peralatan.html', active_page='peralatan')

@admin_bp.route('/peralatan/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_peralatan(id):
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        nama_peralatan = request.form['nama_peralatan']
        deskripsi = request.form.get('deskripsi', '')
        harga_sewa = request.form['harga_sewa']
        stok = request.form['stok']
        
        try:
            cur.execute("""
                UPDATE peralatan_sewa SET 
                nama_peralatan=%s, deskripsi=%s, harga_sewa=%s, stok=%s
                WHERE peralatan_id=%s
            """, (nama_peralatan, deskripsi, harga_sewa, stok, id))
            mysql.connection.commit()
            flash(f'Peralatan {nama_peralatan} berhasil diperbarui!', 'success')
            return redirect(url_for('admin.peralatan'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Gagal memperbarui peralatan: {str(e)}', 'danger')
        finally:
            cur.close()
    
    cur.execute("SELECT * FROM peralatan_sewa WHERE peralatan_id = %s", [id])
    peralatan_data = cur.fetchone()
    cur.close()
    
    if not peralatan_data:
        flash('Peralatan tidak ditemukan.', 'danger')
        return redirect(url_for('admin.peralatan'))
    
    return render_template('admin/edit_peralatan.html',
                           peralatan=peralatan_data,
                           active_page='peralatan')

@admin_bp.route('/peralatan/hapus/<int:id>', methods=['POST'])
@admin_required
def hapus_peralatan(id):
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM peralatan_sewa WHERE peralatan_id = %s", [id])
        mysql.connection.commit()
        flash('Peralatan berhasil dihapus.', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Gagal menghapus peralatan: {str(e)}', 'danger')
    finally:
        cur.close()
    
    return redirect(url_for('admin.peralatan'))

@admin_bp.route('/peralatan')
@admin_required
def peralatan():
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM peralatan_sewa ORDER BY nama_peralatan")
    peralatan_list = cur.fetchall()
    cur.close()
    return render_template('admin/peralatan.html',
                           peralatan_list=peralatan_list,
                           active_page='peralatan')

@admin_bp.route('/bantuan')
@admin_required
def bantuan():
    return render_template('admin/bantuan.html', active_page='bantuan')

# ======================
# List Punish
# ======================
@admin_bp.route('/punish', methods=['GET'])
@admin_required
def punish_list():
    """Menampilkan semua punish user"""
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            SELECT p.id, u.nama, p.violation, p.punishment, p.points, p.detail, p.date
            FROM punishment p
            JOIN user u ON p.user_id = u.user_id
            ORDER BY p.date DESC
        """)
        punishments = cur.fetchall()
    except Exception as e:
        flash(f"Error mengambil data punish: {e}", "danger")
        punishments = []
    finally:
        cur.close()
    
    return render_template('admin/punish.html', punishments=punishments, halaman_aktif='punish')


# ======================
# Add Punish
# ======================
@admin_bp.route('/punish/add', methods=['GET', 'POST'])
@admin_required
def punish_add():
    """Form untuk menambahkan punish baru ke user"""
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    
    try:
        # Ambil daftar user untuk dropdown
        cur.execute("SELECT user_id, nama FROM user ORDER BY nama")
        users = cur.fetchall()
        
        if request.method == 'POST':
            user_id = request.form.get('user_id')
            violation = request.form.get('violation', '').strip()
            punishment = request.form.get('punishment', '').strip()
            points = request.form.get('points', 0, type=int)
            detail = request.form.get('detail', '').strip()
            
            if not user_id or not violation or not punishment:
                flash("User, pelanggaran, dan hukuman harus diisi!", "warning")
                return redirect(url_for('admin.punish_add'))
            
            cur.execute("""
                INSERT INTO punishment (user_id, violation, punishment, points, detail, date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, violation, punishment, points, detail, datetime.now()))
            mysql.connection.commit()
            flash("Punish berhasil ditambahkan!", "success")
            return redirect(url_for('admin.punish_list'))
    
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Gagal menambahkan punish: {e}", "danger")
    
    finally:
        cur.close()
    
    return render_template('admin/punish_add.html', users=users, halaman_aktif='punish')