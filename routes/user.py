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

@user_bp.route('/pemesanan/tiket/<int:jalur_id>', methods=['GET'])
@login_required
def pemesanan_tiket(jalur_id):
    mysql = current_app.mysql
    cur = mysql.connection.cursor()
    
    try:
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
            return redirect(url_for('user.user_dashboard'))

        cur.execute("SELECT * FROM peralatan_sewa WHERE stok > 0 ORDER BY nama_peralatan")
        peralatan_list = cur.fetchall()
        
        cur.execute("SELECT * FROM porter WHERE gunung_id = %s AND status = 'tersedia'", [tiket_data['gunung_id']])
        porter_list = cur.fetchall()
        
    except Exception as e:
        flash(f"Error saat mengambil data pemesanan: {e}", "danger")
        return redirect(url_for('user.user_dashboard'))
    finally:
        cur.close()
    
    return render_template('user/pemesanan_tiket.html',
                           tiket=tiket_data,
                           peralatan_list=peralatan_list,
                           porter_list=porter_list,
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
