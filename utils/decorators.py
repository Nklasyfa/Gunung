from functools import wraps
from flask import redirect, url_for, session, flash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Anda perlu login terlebih dahulu.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Anda perlu login terlebih dahulu.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            flash('Halaman ini hanya bisa diakses oleh Admin!', 'danger')
            return redirect(url_for('user.user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function
