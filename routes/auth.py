from flask import Blueprint, render_template, request, redirect, url_for, session, flash, get_flashed_messages, current_app

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin.admin_dashboard'))
        else:
            return redirect(url_for('user.user_dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        mysql = current_app.mysql
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT user_id, email, password, nama, role FROM user WHERE email = %s AND password = %s", (email, password))
        
        if result > 0:
            user = cur.fetchone()
            session['user_id'] = user['user_id']
            session['nama'] = user['nama']
            session['role'] = user['role']
            
            flash('Login Berhasil! Selamat datang.', 'success')
            
            if user['role'] == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            else:
                return redirect(url_for('user.user_dashboard'))
        else:
            flash('Email atau Password salah! Coba lagi.', 'danger')
            cur.close()
            return render_template('login.html')
        cur.close()

    flashed_messages = get_flashed_messages(with_categories=True)
    return render_template('login.html', messages=flashed_messages)

@auth_bp.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        nama = request.form['nama']
        email = request.form['email']
        password = request.form['password']
        no_hp = request.form['no_hp']
        alamat = request.form['alamat']

        mysql = current_app.mysql
        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO user (email, password, nama, no_hp, alamat, role) VALUES (%s, %s, %s, %s, %s, 'user')",
                        (email, password, nama, no_hp, alamat))
            mysql.connection.commit()
            flash('Registrasi Berhasil! Silakan masuk dengan akun baru Anda.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            mysql.connection.rollback()
            error_message = 'Email sudah terdaftar. Silakan gunakan email lain atau masuk.'
            if '1062' not in str(e):
                error_message = f'Registrasi Gagal karena kesalahan sistem. ({str(e)})'
                
            flash(error_message, 'danger')
            return render_template('login.html', show_register=True) 
        finally:
            cur.close()
            
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Anda telah berhasil keluar.', 'success')
    return redirect(url_for('auth.login'))
