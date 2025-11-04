import os # <-- WAJIB ADA
from flask import Flask, get_flashed_messages, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from config import Config

# --- INI BAGIAN PERBAIKANNYA ---
# 1. Dapatkan path absolut (lokasi pasti) dari folder 'gunung' kamu
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
# 2. Beri tahu Flask secara EKSPLISIT di mana foldernya
STATIC_FOLDER = os.path.join(APP_ROOT, 'static')
TEMPLATE_FOLDER = os.path.join(APP_ROOT, 'templates')

# 3. Masukkan path itu saat membuat aplikasi Flask
app = Flask(__name__,
            template_folder=TEMPLATE_FOLDER,
            static_folder=STATIC_FOLDER)
# --- AKHIR PERBAIKAN ---

app.config.from_object(Config)

# Konfigurasi session key (WAJIB diatur untuk keamanan)
app.secret_key = 'super_secret_key_anda' # Ganti dengan kunci rahasia yang kuat

mysql = MySQL(app)

# --- READ: Menampilkan Form Login ---
@app.route('/', methods=['GET', 'POST'])
def login():
    # Jika sudah login, redirect ke home
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        # Mengambil data user untuk login
        result = cur.execute("SELECT user_id, email, password, nama FROM user WHERE email = %s AND password = %s", (email, password))
        
        if result > 0:
            user = cur.fetchone()
            session['user_id'] = user['user_id']
            session['nama'] = user['nama']
            flash('Login Berhasil! Selamat datang.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Email atau Password salah! Coba lagi.', 'danger')
            return render_template('login.html')

    return render_template('login.html')

# --- CREATE: Halaman Registrasi (Membuat Akun Baru) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nama = request.form['nama']
        email = request.form['email']
        password = request.form['password']
        no_hp = request.form['no_hp']
        alamat = request.form['alamat']

        cur = mysql.connection.cursor()
        try:
            # Query INSERT INTO (CREATE)
            cur.execute("INSERT INTO user (email, password, nama, no_hp, alamat) VALUES (%s, %s, %s, %s, %s)",
                        (email, password, nama, no_hp, alamat))
            mysql.connection.commit()
            flash('Registrasi Berhasil! Silakan masuk dengan akun baru Anda.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            mysql.connection.rollback()
            # Logika untuk menampilkan pesan error spesifik (misal Duplicate entry)
            error_message = 'Email sudah terdaftar. Silakan gunakan email lain atau masuk.'
            if '1062' not in str(e):
                error_message = f'Registrasi Gagal karena kesalahan sistem. ({str(e)})'
                
            flash(error_message, 'danger')
            # Jika gagal, tampilkan form register lagi
            return render_template('login.html', show_register=True) 
            
    # Mode GET: Tampilkan form registrasi
    return render_template('login.html', show_register=True)

# --- READ: Halaman Home (Dashboard) ---
@app.route('/home')
def home():
    if 'user_id' not in session:
        flash('Anda perlu login terlebih dahulu.', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    
    # 1. Query READ data user
    cur.execute("SELECT user_id, email, nama, no_hp, alamat FROM user WHERE user_id = %s", [user_id])
    user_data = cur.fetchone()
    
    # 2. Query READ data Gunung (untuk ditampilkan di Home)
    try:
        cur.execute("SELECT gunung_id, nama_gunung, lokasi, status_pendakian FROM gunung LIMIT 5")
        gunung_list = cur.fetchall()
    except Exception as e:
        gunung_list = [] # Jika tabel gunung tidak ada, jadikan list kosong
        print(f"Error mengambil data gunung: {e}") # Debug di terminal
    
    cur.close()

    # Mengambil pesan flash
    flashed_messages = [{'category': category, 'message': message} for category, message in get_flashed_messages(with_categories=True)]
        
    return render_template('home.html',
                           user=user_data,
                           messages=flashed_messages,
                           gunung_list=gunung_list)

# --- UPDATE: Mengubah Data Profil Pengguna ---
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        nama = request.form['nama']
        no_hp = request.form['no_hp']
        alamat = request.form['alamat']

        try:
            # Query UPDATE (UPDATE) data user
            cur.execute("UPDATE user SET nama=%s, no_hp=%s, alamat=%s WHERE user_id=%s",
                        (nama, no_hp, alamat, user_id))
            mysql.connection.commit()
            session['nama'] = nama # Update session dengan nama baru
            flash('Profil berhasil diperbarui!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Pembaruan Profil Gagal: {str(e)}', 'danger')
            return redirect(url_for('edit_profile'))
    
    # Mode GET: Ambil data user untuk diisi di form
    cur.execute("SELECT user_id, email, nama, no_hp, alamat FROM user WHERE user_id = %s", [user_id])
    user_data = cur.fetchone()
    cur.close()
    
    return render_template('edit_profile.html', user=user_data)


# --- DELETE: Menghapus Akun Pengguna (Logout dan Delete) ---
@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    cur = mysql.connection.cursor()

    try:
        # Query DELETE (DELETE) data user
        cur.execute("DELETE FROM user WHERE user_id = %s", [user_id])
        mysql.connection.commit()
        session.pop('user_id', None)
        session.pop('nama', None)
        flash('Akun Anda berhasil dihapus. Kami sedih melihat Anda pergi.', 'info')
        return redirect(url_for('login'))
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Gagal menghapus akun: {str(e)}', 'danger')
        return redirect(url_for('home'))

# --- Logout ---
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('nama', None)
    flash('Anda telah berhasil keluar.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)