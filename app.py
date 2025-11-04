import os 
from flask import Flask, get_flashed_messages, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from config import Config


APP_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(APP_ROOT, 'static')
TEMPLATE_FOLDER = os.path.join(APP_ROOT, 'templates')


app = Flask(__name__,
            template_folder=TEMPLATE_FOLDER,
            static_folder=STATIC_FOLDER)


app.config.from_object(Config)

app.secret_key = 'super_secret_key_anda' 

mysql = MySQL(app)

# LOGIN: Halaman Login 
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
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

# REGISTER: Halaman Registrasi
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
            # Query CREATE (INSERT) data user
            cur.execute("INSERT INTO user (email, password, nama, no_hp, alamat) VALUES (%s, %s, %s, %s, %s)",
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
            
    return render_template('login.html', show_register=True)

# READ: Halaman Home (Dashboard) 
@app.route('/home')
def home():
    if 'user_id' not in session:
        flash('Anda perlu login terlebih dahulu.', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    
    # 1. Query READ data User
    cur.execute("SELECT user_id, email, nama, no_hp, alamat FROM user WHERE user_id = %s", [user_id])
    user_data = cur.fetchone()
    
    # 2. Query READ data Gunung (untuk ditampilkan di Home)
    try:
        cur.execute("SELECT gunung_id, nama_gunung, lokasi, status_pendakian FROM gunung LIMIT 5")
        gunung_list = cur.fetchall()
    except Exception as e:
        gunung_list = [] 
        print(f"Error mengambil data gunung: {e}") 
    
    cur.close()

    flashed_messages = [{'category': category, 'message': message} for category, message in get_flashed_messages(with_categories=True)]
        
    return render_template('home.html',
                           user=user_data,
                           messages=flashed_messages,
                           gunung_list=gunung_list)

# --- UPDATE: Mengedit Profil Pengguna ---
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
            session['nama'] = nama 
            flash('Profil berhasil diperbarui!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Pembaruan Profil Gagal: {str(e)}', 'danger')
            return redirect(url_for('edit_profile'))
    
    # GET request: Ambil data user untuk ditampilkan di form edit
    cur.execute("SELECT user_id, email, nama, no_hp, alamat FROM user WHERE user_id = %s", [user_id])
    user_data = cur.fetchone()
    cur.close()
    
    return render_template('edit_profile.html', user=user_data)


# DELETE: Menghapus Akun Pengguna 
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

# LOGOUT: Halaman Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('nama', None)
    flash('Anda telah berhasil keluar.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)