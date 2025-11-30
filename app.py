import os 
from flask import Flask, get_flashed_messages, render_template, request, redirect, url_for, session, flash, g
from flask_mysqldb import MySQL
from config import Config
from functools import wraps # Penting untuk decorator
import requests
from flask import jsonify
from dotenv import load_dotenv
import MySQLdb
import MySQLdb.cursors
from flask_babel import Babel, lazy_gettext as _
from datetime import timedelta

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(APP_ROOT, 'static')
TEMPLATE_FOLDER = os.path.join(APP_ROOT, 'templates')

app = Flask(__name__,
            template_folder=TEMPLATE_FOLDER,
            static_folder=STATIC_FOLDER)

app.config.from_object(Config)
app.secret_key = 'super_secret_key_anda' 
mysql = MySQL(app)

# === DECORATOR (PENJAGA HALAMAN) ===

# Penjaga untuk semua user yang sudah login (Admin & User biasa)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Anda perlu login terlebih dahulu.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Penjaga HANYA UNTUK ADMIN
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Cek sudah login atau belum
        if 'user_id' not in session:
            flash('Anda perlu login terlebih dahulu.', 'warning')
            return redirect(url_for('login'))
        # 2. Cek apakah rolenya 'admin'
        if session.get('role') != 'admin':
            flash('Halaman ini hanya bisa diakses oleh Admin!', 'danger')
            return redirect(url_for('user_dashboard')) # Dilempar ke dashboard user
        return f(*args, **kwargs)
    return decorated_function

# === AUTENTIKASI (LOGIN, REGISTER, LOGOUT) ===

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        # Jika sudah login, lempar ke dashboard masing-masing
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        # Ambil 'role' saat login
        result = cur.execute("SELECT user_id, email, password, nama, role FROM user WHERE email = %s AND password = %s", (email, password))
        
        if result > 0:
            user = cur.fetchone()
            # Simpan semua data ke session
            session['user_id'] = user['user_id']
            session['nama'] = user['nama']
            session['role'] = user['role'] # <-- PENTING
            
            flash('Login Berhasil! Selamat datang.', 'success')
            
            # Logika pemisah: Admin ke /admin, User ke /home
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Email atau Password salah! Coba lagi.', 'danger')
            return render_template('login.html')

    # Tampilkan halaman login untuk GET request
    flashed_messages = get_flashed_messages(with_categories=True)
    return render_template('login.html', messages=flashed_messages)

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        nama = request.form['nama']
        email = request.form['email']
        password = request.form['password']
        no_hp = request.form['no_hp']
        alamat = request.form['alamat']

        cur = mysql.connection.cursor()
        try:
            # Saat daftar, 'role' otomatis di-set sebagai 'user'
            cur.execute("INSERT INTO user (email, password, nama, no_hp, alamat, role) VALUES (%s, %s, %s, %s, %s, 'user')",
                        (email, password, nama, no_hp, alamat))
            mysql.connection.commit()
            flash('Registrasi Berhasil! Silakan masuk dengan akun baru Anda.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            mysql.connection.rollback()
            error_message = 'Email sudah terdaftar. Silakan gunakan email lain atau masuk.'
            if '1062' not in str(e):
                error_message = f'Registrasi Gagal karena kesalahan sistem. ({str(e)})'
                
            flash(error_message, 'danger')
            return render_template('login.html', show_register=True) 
            
    # GET request ke /register tidak diizinkan, redirect ke login
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    session.clear() # Hapus semua data session
    flash('Anda telah berhasil keluar.', 'success')
    return redirect(url_for('login'))

# === HALAMAN USER BIASA (PENDAKI) ===

@app.route('/home')
@login_required
def user_dashboard():
    # Ambil data gunung untuk dashboard user
    cur = mysql.connection.cursor()
    try:
        # Mengambil SEMUA data gunung untuk tampilan card baru
        cur.execute("SELECT * FROM gunung ORDER BY nama_gunung")
        gunung_list = cur.fetchall()
    except Exception as e:
        gunung_list = [] 
        flash(f"Error mengambil data gunung: {e}", "danger") 
    cur.close()
        
    return render_template('user/dashboard.html',
                           gunung_list=gunung_list,
                           user_nama=session.get('nama'),
                           active_page='home') # Kirim active_page

# HALAMAN BARU: DETAIL GUNUNG (DIPERBARUI UNTUK MENGAMBIL DATA JALUR DAN PORTER)
@app.route('/gunung/<int:id>')
@login_required
def detail_gunung(id):
    cur = mysql.connection.cursor()
    gunung_data = None
    jalur_list = []
    porter_list = []
    
    try:
        # 1. Ambil data lengkap gunung
        cur.execute("SELECT * FROM gunung WHERE gunung_id = %s", [id])
        gunung_data = cur.fetchone()
        
        if not gunung_data:
            flash("Gunung tidak ditemukan.", "danger")
            return redirect(url_for('user_dashboard'))
            
        # 2. Ambil data Jalur Pendakian yang terkait dengan Gunung ini
        cur.execute("SELECT * FROM jalur_pendakian WHERE gunung_id = %s", [id])
        jalur_list = cur.fetchall()

        # 3. Ambil data Tiket yang tersedia untuk jalur-jalur gunung ini
        cur.execute("""
            SELECT t.*, j.nama_jalur
            FROM tiket t
            JOIN jalur_pendakian j ON t.jalur_id = j.jalur_id
            WHERE j.gunung_id = %s
            ORDER BY t.tanggal_berlaku DESC
        """, [id])
        tiket_list = cur.fetchall()

        # 4. Ambil data Porter yang tersedia di Gunung ini
        # Kita hanya ingin porter yang statusnya 'tersedia'
        cur.execute("SELECT * FROM porter WHERE gunung_id = %s AND status = 'tersedia'", [id])
        porter_list = cur.fetchall()
        
    except Exception as e:
        flash(f"Error mengambil detail gunung: {e}", "danger")
        return redirect(url_for('user_dashboard'))
    finally:
        cur.close()
        
    # KIRIM SEMUA DATA PENTING KE TEMPLATE
    return render_template('user/detail_gunung.html',
                           gunung=gunung_data,
                           jalur_list=jalur_list, # <-- PENTING
                           tiket_list=tiket_list, # <-- PENTING
                           porter_list=porter_list, # <-- PENTING
                           active_page='home')

@app.route('/profile')
@login_required
def profile():
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT user_id, email, nama, no_hp, alamat, role FROM user WHERE user_id = %s", [user_id])
    user_data = cur.fetchone()
    cur.close()
    
    return render_template('user/profile.html',
                           user=user_data,
                           active_page='profile')

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    # Rute ini tetap ada, tapi link dari sidebar dihapus
    user_id = session['user_id']
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        nama = request.form['nama']
        no_hp = request.form['no_hp']
        alamat = request.form['alamat']

        try:
            cur.execute("UPDATE user SET nama=%s, no_hp=%s, alamat=%s WHERE user_id=%s",
                        (nama, no_hp, alamat, user_id))
            mysql.connection.commit()
            session['nama'] = nama # Update session
            flash('Profil berhasil diperbarui!', 'success')
            return redirect(url_for('profile')) # Redirect ke halaman profil
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Pembaruan Profil Gagal: {str(e)}', 'danger')
            return redirect(url_for('edit_profile'))
    
    # GET request
    cur.execute("SELECT user_id, email, nama, no_hp, alamat FROM user WHERE user_id = %s", [user_id])
    user_data = cur.fetchone()
    cur.close()
    
    # Arahkan ke template edit_profile.html (jika masih mau dipakai)
    return render_template('user/edit_profile.html',
                           user=user_data,
                           active_page='profile') # Aktifkan 'profile'

@app.route('/profile/delete', methods=['POST'])
@login_required
def delete_account():
    user_id = session['user_id']
    cur = mysql.connection.cursor()

    try:
        cur.execute("DELETE FROM user WHERE user_id = %s", [user_id])
        mysql.connection.commit()
        session.clear()
        flash('Akun Anda berhasil dihapus.', 'success')
        return redirect(url_for('login'))
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Gagal menghapus akun: {str(e)}', 'danger')
        return redirect(url_for('profile'))


# === HALAMAN KHUSUS ADMIN ===

@app.route('/admin')
@admin_required
def admin_dashboard():
    # Halaman dashboard admin
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

# --- DATA MASTER GUNUNG (CRUD) ---
# (PENTING: Kita harus update form-nya untuk menerima data baru)

# READ (Tampil List Gunung)
@app.route('/admin/gunung')
@admin_required
def gunung():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM gunung ORDER BY nama_gunung")
    gunung_list = cur.fetchall()
    cur.close()
    return render_template('admin/gunung.html',
                           gunung_list=gunung_list,
                           active_page='gunung')

# CREATE (Halaman Form Tambah)
@app.route('/admin/gunung/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_gunung():
    if request.method == 'POST':
        # Ambil data baru dari form
        nama_gunung = request.form['nama_gunung']
        lokasi = request.form['lokasi']
        ketinggian = request.form['ketinggian']
        status = request.form['status_pendakian']
        deskripsi = request.form['deskripsi']
        sejarah = request.form['sejarah']
        estimasi_waktu = request.form['estimasi_waktu']
        kuota_harian = request.form['kuota_harian']
        
        cur = mysql.connection.cursor()
        try:
            # Masukkan data baru ke DB
            cur.execute("""
                INSERT INTO gunung (nama_gunung, lokasi, ketinggian, status_pendakian, deskripsi, sejarah, estimasi_waktu, kuota_harian) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (nama_gunung, lokasi, ketinggian, status, deskripsi, sejarah, estimasi_waktu, kuota_harian))
            mysql.connection.commit()
            flash(f'Gunung {nama_gunung} berhasil ditambahkan!', 'success')
            return redirect(url_for('gunung'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Gagal menambah gunung: {str(e)}', 'danger')
        finally:
            cur.close()
            
    return render_template('admin/tambah_gunung.html', active_page='gunung')

# UPDATE (Halaman Form Edit)
@app.route('/admin/gunung/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_gunung(id):
    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        # Ambil data baru dari form
        nama_gunung = request.form['nama_gunung']
        lokasi = request.form['lokasi']
        ketinggian = request.form['ketinggian']
        status = request.form['status_pendakian']
        deskripsi = request.form['deskripsi']
        sejarah = request.form['sejarah']
        estimasi_waktu = request.form['estimasi_waktu']
        kuota_harian = request.form['kuota_harian']
        
        try:
            cur.execute("""
                UPDATE gunung SET 
                nama_gunung=%s, lokasi=%s, ketinggian=%s, status_pendakian=%s, 
                deskripsi=%s, sejarah=%s, estimasi_waktu=%s, kuota_harian=%s
                WHERE gunung_id=%s
            """, (nama_gunung, lokasi, ketinggian, status, deskripsi, sejarah, estimasi_waktu, kuota_harian, id))
            mysql.connection.commit()
            flash(f'Data Gunung {nama_gunung} berhasil diperbarui!', 'success')
            return redirect(url_for('gunung'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Gagal memperbarui gunung: {str(e)}', 'danger')
        finally:
            cur.close()

    # GET request
    cur.execute("SELECT * FROM gunung WHERE gunung_id = %s", [id])
    gunung_data = cur.fetchone()
    cur.close()
    
    if not gunung_data:
        flash('Data gunung tidak ditemukan.', 'danger')
        return redirect(url_for('gunung'))
        
    return render_template('admin/edit_gunung.html',
                           gunung=gunung_data,
                           active_page='gunung')

# DELETE (Proses Hapus)
@app.route('/admin/gunung/hapus/<int:id>', methods=['POST'])
@admin_required
def hapus_gunung(id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM gunung WHERE gunung_id = %s", [id])
        mysql.connection.commit()
        flash('Data gunung berhasil dihapus.', 'success')
    except Exception as e:
        mysql.connection.rollback()
        # Cek jika error karena foreign key
        if '1451' in str(e):
            flash('Gagal menghapus gunung. Data ini terhubung dengan data lain (misal: tiket atau jalur).', 'danger')
        else:
            flash(f'Gagal menghapus gunung: {str(e)}', 'danger')
    finally:
        cur.close()
    
    return redirect(url_for('gunung'))

# -------------------------------------------------------------------------
# === 2. RUTE BARU UNTUK PEMESANAN (USER BIASA) ===

@app.route('/pemesanan/tiket/<int:jalur_id>', methods=['GET'])
@login_required
def pemesanan_tiket(jalur_id):
    cur = mysql.connection.cursor()
    
    try:
        # 1. Ambil data tiket, jalur, dan gunung yang sesuai
        cur.execute("""
            SELECT 
                t.tiket_id, t.harga, t.kuota_harian, t.tanggal_berlaku,
                j.jalur_id, j.nama_jalur, g.gunung_id, g.nama_gunung
            FROM tiket t
            JOIN jalur_pendakian j ON t.jalur_id = j.jalur_id
            JOIN gunung g ON j.gunung_id = g.gunung_id
            WHERE t.jalur_id = %s
            ORDER BY t.tanggal_berlaku DESC LIMIT 1
        """, [jalur_id])
        tiket_data = cur.fetchone()
        
        if not tiket_data:
            flash("Tidak ada tiket yang tersedia untuk jalur ini.", "danger")
            return redirect(url_for('user_dashboard'))

        # 2. Ambil data peralatan sewa
        cur.execute("SELECT * FROM peralatan_sewa WHERE stok > 0 ORDER BY nama_peralatan")
        peralatan_list = cur.fetchall()
        
        # 3. Ambil data porter yang tersedia di gunung terkait
        cur.execute("SELECT * FROM porter WHERE gunung_id = %s AND status = 'tersedia'", [tiket_data['gunung_id']])
        porter_list = cur.fetchall()
        
    except Exception as e:
        flash(f"Error saat mengambil data pemesanan: {e}", "danger")
        return redirect(url_for('user_dashboard'))
    finally:
        cur.close()
    
    return render_template('user/pemesanan_tiket.html',
                           tiket=tiket_data,
                           peralatan_list=peralatan_list,
                           porter_list=porter_list,
                           active_page='home')

@app.route('/pemesanan/submit', methods=['POST'])
@login_required
def submit_pemesanan():
    user_id = session['user_id']
    tiket_id = request.form.get('tiket_id', type=int)
    jumlah_pendaki = request.form.get('jumlah_pendaki', type=int)
    
    # Data Sewa Peralatan
    peralatan_ids = request.form.getlist('peralatan_id[]')
    jumlah_peralatan = request.form.getlist('jumlah_peralatan[]')
    
    # Data Sewa Porter
    porter_id = request.form.get('porter_id', type=int)
    lama_sewa_hari = request.form.get('lama_sewa_hari', type=int)

    if not tiket_id or jumlah_pendaki is None or jumlah_pendaki < 1:
        flash('Data tiket atau jumlah pendaki tidak valid.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    cur = mysql.connection.cursor()
    total_bayar = 0
    jalur_id_for_redirect = None
    
    try:
        # A. Cek ketersediaan dan harga tiket
        cur.execute("SELECT harga, kuota_harian, jalur_id FROM tiket WHERE tiket_id = %s", [tiket_id])
        tiket_info = cur.fetchone()
        
        if not tiket_info:
            raise Exception("Tiket tidak ditemukan.")
            
        if jumlah_pendaki > tiket_info['kuota_harian']:
            raise Exception(f"Jumlah pendaki melebihi kuota harian yang tersedia ({tiket_info['kuota_harian']} orang).")

        jalur_id_for_redirect = tiket_info['jalur_id']
        
        # B. Hitung biaya tiket
        biaya_tiket = tiket_info['harga'] * jumlah_pendaki
        total_bayar += biaya_tiket
        
        # C. Insert ke tabel pemesanan
        cur.execute("INSERT INTO pemesanan (user_id, tiket_id, tanggal_pesan, status) VALUES (%s, %s, NOW(), 'menunggu')",
                    (user_id, tiket_id))
        pemesanan_id = cur.lastrowid
        
        # D. Insert Data Pendaki (Simulasi untuk 1 pendaki utama / ketua rombongan)
        # ⚠️ CATATAN: Anda harus memodifikasi ini untuk mengambil NIK, tgl_lahir, dll. dari form
        nama_pendaki = session['nama']
        cur.execute("""
            INSERT INTO pendaki (pemesanan_id, nama_pendaki, nik, tgl_lahir, jenis_kelamin, kontak_darurat)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (pemesanan_id, nama_pendaki, '0', '2000-01-01', 'Laki', session.get('no_hp', '0')))

        
        # E. Proses Sewa Peralatan
        # Asumsi lama sewa = lama sewa porter. Jika porter tidak disewa, lama sewa harus 1 hari (minimal).
        lama_sewa_peralatan = lama_sewa_hari if lama_sewa_hari and lama_sewa_hari > 0 else 1 

        for i, alat_id_str in enumerate(peralatan_ids):
            try:
                alat_id = int(alat_id_str)
                jumlah = int(jumlah_peralatan[i])
            except ValueError:
                # Lewati jika ada data yang tidak valid
                continue 

            if jumlah > 0:
                cur.execute("SELECT harga_sewa, stok, nama_peralatan FROM peralatan_sewa WHERE peralatan_id = %s", [alat_id])
                alat_info = cur.fetchone()
                
                if not alat_info:
                     raise Exception("Peralatan tidak ditemukan.")
                if jumlah > alat_info['stok']:
                     raise Exception(f"Stok peralatan '{alat_info['nama_peralatan']}' tidak cukup. Tersedia: {alat_info['stok']}")
                    
                subtotal = alat_info['harga_sewa'] * jumlah * lama_sewa_peralatan
                total_bayar += subtotal
                
                cur.execute("INSERT INTO detail_sewa (pemesanan_id, peralatan_id, jumlah, subtotal) VALUES (%s, %s, %s, %s)",
                            (pemesanan_id, alat_id, jumlah, subtotal))
                # Kurangi stok
                cur.execute("UPDATE peralatan_sewa SET stok = stok - %s WHERE peralatan_id = %s", (jumlah, alat_id))
        
        # F. Proses Sewa Porter
        if porter_id and lama_sewa_hari and lama_sewa_hari > 0:
            cur.execute("SELECT harga_per_hari, status FROM porter WHERE porter_id = %s", [porter_id])
            porter_info = cur.fetchone()
            
            if not porter_info or porter_info['status'] != 'tersedia':
                raise Exception("Porter tidak tersedia atau tidak valid.")
                
            total_biaya_porter = porter_info['harga_per_hari'] * lama_sewa_hari
            total_bayar += total_biaya_porter
            
            cur.execute("INSERT INTO sewa_porter (pemesanan_id, porter_id, lama_sewa_hari, total_biaya) VALUES (%s, %s, %s, %s)",
                        (pemesanan_id, porter_id, lama_sewa_hari, total_biaya_porter))
            # Ubah status porter
            cur.execute("UPDATE porter SET status = 'sedang bertugas' WHERE porter_id = %s", [porter_id])

        # G. Update total pembayaran di tabel pembayaran (status 'menunggu')
        cur.execute("""
            INSERT INTO pembayaran (pemesanan_id, metode_bayar, jumlah, tanggal_bayar, status_bayar) 
            VALUES (%s, 'transfer', %s, NOW(), 'menunggu')
        """, (pemesanan_id, total_bayar))
        
        mysql.connection.commit()
        flash(f'Pemesanan Tiket dan layanan berhasil! Total yang harus dibayar: Rp {total_bayar:,.0f}. Segera lakukan pembayaran.', 'success')
        
        return redirect(url_for('user_dashboard')) 
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Pemesanan Gagal: {str(e)}', 'danger')
        
        if jalur_id_for_redirect:
             return redirect(url_for('pemesanan_tiket', jalur_id=jalur_id_for_redirect))
        return redirect(url_for('user_dashboard'))
    finally:
        cur.close()

# -------------------------------------------------------------------------
# === 3. RUTE BARU UNTUK ADMIN - DATA MASTER PORTER (CRUD) ===

@app.route('/admin/porter')
@admin_required
def porter():
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

@app.route('/admin/porter/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_porter():
    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        gunung_id = request.form['gunung_id']
        nama_porter = request.form['nama_porter']
        umur = request.form['umur']
        pengalaman = request.form['pengalaman_tahun']
        kontak = request.form['kontak']
        status = request.form['status']
        harga = request.form['harga_per_hari']
        
        try:
            cur.execute("""
                INSERT INTO porter (gunung_id, nama_porter, umur, pengalaman_tahun, kontak, status, harga_per_hari) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (gunung_id, nama_porter, umur, pengalaman, kontak, status, harga))
            mysql.connection.commit()
            flash(f'Porter {nama_porter} berhasil ditambahkan!', 'success')
            return redirect(url_for('porter'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Gagal menambah porter: {str(e)}', 'danger')
        finally:
            cur.close()
            
    # GET request: Ambil daftar gunung untuk dropdown
    cur.execute("SELECT gunung_id, nama_gunung FROM gunung ORDER BY nama_gunung")
    gunung_list = cur.fetchall()
    cur.close()
            
    return render_template('admin/tambah_porter.html',
                           gunung_list=gunung_list,
                           active_page='porter')

@app.route('/admin/porter/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_porter(id):
    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        gunung_id = request.form['gunung_id']
        nama_porter = request.form['nama_porter']
        umur = request.form['umur']
        pengalaman = request.form['pengalaman_tahun']
        kontak = request.form['kontak']
        status = request.form['status']
        harga = request.form['harga_per_hari']
        
        try:
            cur.execute("""
                UPDATE porter SET 
                gunung_id=%s, nama_porter=%s, umur=%s, pengalaman_tahun=%s, kontak=%s, status=%s, harga_per_hari=%s
                WHERE porter_id=%s
            """, (gunung_id, nama_porter, umur, pengalaman, kontak, status, harga, id))
            mysql.connection.commit()
            flash(f'Data Porter {nama_porter} berhasil diperbarui!', 'success')
            return redirect(url_for('porter'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Gagal memperbarui porter: {str(e)}', 'danger')
        finally:
            cur.close()

    # GET request
    cur.execute("SELECT * FROM porter WHERE porter_id = %s", [id])
    porter_data = cur.fetchone()
    cur.execute("SELECT gunung_id, nama_gunung FROM gunung ORDER BY nama_gunung")
    gunung_list = cur.fetchall()
    cur.close()
    
    if not porter_data:
        flash('Data porter tidak ditemukan.', 'danger')
        return redirect(url_for('porter'))
        
    return render_template('admin/edit_porter.html',
                           porter=porter_data,
                           gunung_list=gunung_list,
                           active_page='porter')

@app.route('/admin/porter/hapus/<int:id>', methods=['POST'])
@admin_required
def hapus_porter(id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM porter WHERE porter_id = %s", [id])
        mysql.connection.commit()
        flash('Data porter berhasil dihapus.', 'success')
    except Exception as e:
        mysql.connection.rollback()
        if '1451' in str(e):
            flash('Gagal menghapus porter. Data ini sudah terhubung dengan data pemesanan/sewa porter.', 'danger')
        else:
            flash(f'Gagal menghapus porter: {str(e)}', 'danger')
    finally:
        cur.close()
    
    return redirect(url_for('porter'))

# -------------------------------------------------------------------------
# === 4. RUTE BARU UNTUK ADMIN - DATA MASTER PERALATAN SEWA (CRUD) ===

@app.route('/admin/peralatan')
@admin_required
def peralatan():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM peralatan_sewa ORDER BY nama_peralatan")
    peralatan_list = cur.fetchall()
    cur.close()
    return render_template('admin/peralatan.html',
                           peralatan_list=peralatan_list,
                           active_page='peralatan')

@app.route('/admin/peralatan/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_peralatan():
    if request.method == 'POST':
        nama_peralatan = request.form['nama_peralatan']
        harga_sewa = request.form['harga_sewa']
        stok = request.form['stok']
        
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO peralatan_sewa (nama_peralatan, harga_sewa, stok) 
                VALUES (%s, %s, %s)
            """, (nama_peralatan, harga_sewa, stok))
            mysql.connection.commit()
            flash(f'Peralatan {nama_peralatan} berhasil ditambahkan!', 'success')
            return redirect(url_for('peralatan'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Gagal menambah peralatan: {str(e)}', 'danger')
        finally:
            cur.close()
            
    return render_template('admin/tambah_peralatan.html', active_page='peralatan')

@app.route('/admin/peralatan/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_peralatan(id):
    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        nama_peralatan = request.form['nama_peralatan']
        harga_sewa = request.form['harga_sewa']
        stok = request.form['stok']
        
        try:
            cur.execute("""
                UPDATE peralatan_sewa SET 
                nama_peralatan=%s, harga_sewa=%s, stok=%s
                WHERE peralatan_id=%s
            """, (nama_peralatan, harga_sewa, stok, id))
            mysql.connection.commit()
            flash(f'Data Peralatan {nama_peralatan} berhasil diperbarui!', 'success')
            return redirect(url_for('peralatan'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Gagal memperbarui peralatan: {str(e)}', 'danger')
        finally:
            cur.close()

    # GET request
    cur.execute("SELECT * FROM peralatan_sewa WHERE peralatan_id = %s", [id])
    peralatan_data = cur.fetchone()
    cur.close()
    
    if not peralatan_data:
        flash('Data peralatan tidak ditemukan.', 'danger')
        return redirect(url_for('peralatan'))
        
    return render_template('admin/edit_peralatan.html',
                           peralatan=peralatan_data,
                           active_page='peralatan')

@app.route('/admin/peralatan/hapus/<int:id>', methods=['POST'])
@admin_required
def hapus_peralatan(id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM peralatan_sewa WHERE peralatan_id = %s", [id])
        mysql.connection.commit()
        flash('Data peralatan berhasil dihapus.', 'success')
    except Exception as e:
        mysql.connection.rollback()
        if '1451' in str(e):
            flash('Gagal menghapus peralatan. Data ini sudah terhubung dengan data pemesanan/detail sewa.', 'danger')
        else:
            flash(f'Gagal menghapus peralatan: {str(e)}', 'danger')
    finally:
        cur.close()
    
    return redirect(url_for('peralatan'))

# Load API key dari .env
load_dotenv()
WEATHER_KEY = os.getenv("OPENWEATHER_KEY")

# Fungsi ambil cuaca berdasarkan nama gunung
def get_weather_by_coord(lat, lon, lang):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": WEATHER_KEY,
        "units": "metric",
        "lang": lang
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            d = r.json()
            return {
                "suhu": d["main"]["temp"],
                "kondisi": d["weather"][0]["description"].title(),
                "angin": d["wind"]["speed"],
                "kelembapan": d["main"]["humidity"],
                "error": False
            }
    except Exception as e:
        return {"error": True, "msg": str(e)}

    return {"error": True, "msg": "Gagal ambil data cuaca"}

def get_coord_from_name(nama):
    """Cari koordinat berdasarkan nama gunung jika lat/lon belum ada di DB"""
    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": nama,
        "limit": 1,
        "appid": WEATHER_KEY
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data:
                return data[0]["lat"], data[0]["lon"]
    except:
        pass
    return None, None


# 1. API Cuaca Gunung berdasarkan ID Database
@app.route("/api/cuaca/gunung/<int:id>")
@login_required
def api_weather_gunung(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT nama_gunung, lat, lon FROM gunung WHERE gunung_id = %s", [id])
    g = cur.fetchone()
    cur.close()

    if not g:
        return jsonify({"error": True, "msg": "Gunung tidak ditemukan"})

    lang = session.get("lang", "id")

    # Jika koordinat ada di DB pakai itu
    if g["lat"] and g["lon"]:
        cuaca = get_weather_by_coord(g["lat"], g["lon"], lang)
        return jsonify(cuaca)

    # Jika koordinat kosong → cari dulu dari Geocoding API
    geo_url = "https://api.openweathermap.org/geo/1.0/direct"
    params = {"q": g["nama_gunung"], "limit": 1, "appid": WEATHER_KEY}

    try:
        r = requests.get(geo_url, params=params, timeout=10)
        if r.status_code == 200 and r.json():
            lat = r.json()[0]["lat"]
            lon = r.json()[0]["lon"]

            # Simpan ke DB biar request berikutnya tidak error
            cur2 = mysql.connection.cursor()
            cur2.execute("UPDATE gunung SET lat=%s, lon=%s WHERE gunung_id=%s", (lat, lon, id))
            mysql.connection.commit()
            cur2.close()

            cuaca = get_weather_by_coord(lat, lon, lang)
            return jsonify(cuaca)
        return jsonify({"error": True, "msg": "Koordinat tidak ditemukan"})
    except Exception as e:
        return jsonify({"error": True, "msg": str(e)})

# 2. Ubah Bahasa #########

# ... (Inisialisasi app dan fitur lain seperti login_manager, dll.) ...

# DAFTAR BAHASA YANG DIDUKUNG
SUPPORTED_LANGS = ['id', 'en', 'ar', 'zh']
app.config['BABEL_DEFAULT_LOCALE'] = 'id'


# 1. Fungsi Penentu Bahasa (Locale Selector)
def get_locale():
    """Mengambil bahasa aktif dari session atau browser."""
    if 'lang' in session and session['lang'] in SUPPORTED_LANGS:
        return session['lang']
    return request.accept_languages.best_match(SUPPORTED_LANGS)

# 2. Inisialisasi Babel
babel = Babel(app, locale_selector=get_locale)

# ... (Lanjutkan dengan kode koneksi database atau setup lainnya) ...
# 3. Middleware Penentu Arah Teks (RTL/LTR)
@app.before_request
def before_request():
    """Menetapkan kode bahasa dan arah teks (dir) sebelum setiap permintaan."""
    lang_code = get_locale()
    
    # Simpan kode bahasa di g (global context)
    g.lang_code = lang_code
    
    # Menentukan arah: 'rtl' (Right-to-Left) hanya untuk Arab, lainnya 'ltr'
    g.dir = 'rtl' if lang_code == 'ar' else 'ltr'
    
    # Pastikan session juga menyimpan kode bahasa
    if 'lang' not in session or session['lang'] != lang_code:
        session['lang'] = lang_code


# 4. Route Pengubah Bahasa (Ini kode kamu yang dimodifikasi)
# @login_required hanya contoh, hilangkan jika tidak menggunakan Flask-Login
@app.route("/ubah-bahasa/<lang>")
# @login_required 
def ubah_bahasa(lang):
    if lang in SUPPORTED_LANGS:
        session['lang'] = lang
    # Redirect ke halaman sebelumnya, yang akan otomatis memuat ulang dengan bahasa baru
    return redirect(request.referrer or url_for('user_dashboard'))

# 3. Endpoint untuk Dark Mode (tidak simpan di DB, hanya sebagai API trigger)################
@app.route("/dark-mode-toggle")
@login_required
def dark_mode_toggle():
    return jsonify({"status": "Dark mode dikontrol frontend lewat JS localStorage"})

# 4. Halaman Pusat Bantuan
@app.route("/bantuan")
@login_required
def bantuan():
    return render_template("user/bantuan.html", active_page="bantuan")

# 5. API Pusat Bantuan (JSON)
@app.route("/api/bantuan")
@login_required
def api_bantuan():
    return jsonify({
        "app": "Projek Informasi Gunung",
        "fitur": [
            "Lihat detail gunung",
            "Pesan tiket",
            "Sewa peralatan",
            "Sewa porter",
            "Lihat cuaca gunung",
            "Mode gelap",
            "Ganti bahasa",
            "Support center"
        ],
        "kontak": "Silakan gunakan menu Pusat Bantuan di aplikasi",
        "faq": [
            {"q": "Kenapa tiket tidak bisa di klik?", "a": "Status gunung masih ditutup atau kuota habis"},
            {"q": "Kenapa cuaca tidak muncul?", "a": "API Key belum aktif atau nama gunung tidak terdaftar di OpenWeather"},
            {"q": "Bisa refund tiket?", "a": "Bisa, silakan hubungi admin melalui Pusat Bantuan"}
        ]
    })

if __name__ == '__main__':
    app.run(debug=True)
    