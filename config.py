# config.py

class Config:
    # Menggunakan konfigurasi yang umum untuk MySQL/MariaDB
    MYSQL_HOST = 'localhost' # Ganti jika database ada di server lain
    MYSQL_USER = 'root'      # Ganti dengan username database Anda
    MYSQL_PASSWORD = '' # Ganti dengan password database Anda
    MYSQL_DB = 'pemesanan_tiket_gunung' # Nama database
    MYSQL_CURSORCLASS = 'DictCursor' # Untuk mendapatkan hasil query sebagai dictionary