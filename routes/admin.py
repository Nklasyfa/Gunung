from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__)

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
        status = request.form['status_pendakian']
        deskripsi = request.form['deskripsi']
        sejarah = request.form['sejarah']
        estimasi_waktu = request.form['estimasi_waktu']
        kuota_harian = request.form['kuota_harian']
        
        mysql = current_app.mysql
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO gunung (nama_gunung, lokasi, ketinggian, status_pendakian, deskripsi, sejarah, estimasi_waktu, kuota_harian) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (nama_gunung, lokasi, ketinggian, status, deskripsi, sejarah, estimasi_waktu, kuota_harian))
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
    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
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
            return redirect(url_for('admin.gunung'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Gagal memperbarui gunung: {str(e)}', 'danger')
        finally:
            cur.close()

    cur.execute("SELECT * FROM gunung WHERE gunung_id = %s", [id])
    gunung_data = cur.fetchone()
    cur.close()
    
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
