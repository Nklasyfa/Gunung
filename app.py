import os 
from flask import Flask, get_flashed_messages, render_template, request, redirect, url_for, session, flash # pyright: ignore[reportMissingImports]
from flask_mysqldb import MySQL
from config import Config
from functools import wraps # Penting untuk decorator

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
        cur.execute("SELECT gunung_id, nama_gunung, lokasi, status_pendakian FROM gunung WHERE status_pendakian = 'Dibuka' LIMIT 5")
        gunung_list = cur.fetchall()
    except Exception as e:
        gunung_list = [] 
        print(f"Error mengambil data gunung: {e}") 
    cur.close()
        
    return render_template('user/dashboard.html',
                           gunung_list=gunung_list,
                           user_nama=session.get('nama'),
                           active_page='home') # Kirim active_page

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
    
    return render_template('user/edit_profile.html',
                           user=user_data,
                           active_page='edit_profile')

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
    # Bisa diisi statistik jumlah user, jumlah gunung, dll.
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
        nama_gunung = request.form['nama_gunung']
        lokasi = request.form['lokasi']
        status = request.form['status_pendakian']
        deskripsi = request.form['deskripsi']
        
        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO gunung (nama_gunung, lokasi, status_pendakian, deskripsi) VALUES (%s, %s, %s, %s)",
                        (nama_gunung, lokasi, status, deskripsi))
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
        nama_gunung = request.form['nama_gunung']
        lokasi = request.form['lokasi']
        status = request.form['status_pendakian']
        deskripsi = request.form['deskripsi']
        
        try:
            cur.execute("""
                UPDATE gunung SET nama_gunung=%s, lokasi=%s, status_pendakian=%s, deskripsi=%s
                WHERE gunung_id=%s
            """, (nama_gunung, lokasi, status, deskripsi, id))
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

# --- END OF DATA MASTER ---

if __name__ == '__main__':
    app.run(debug=True)