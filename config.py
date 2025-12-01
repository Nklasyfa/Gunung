class Config:
    MYSQL_HOST = 'localhost' 
    MYSQL_USER = 'root'      
    MYSQL_PASSWORD = '' 
    MYSQL_DB = 'pemesanan_tiket_gunung' 
    MYSQL_CURSORCLASS = 'DictCursor'
    
    # Google Maps API Key
    # Dapatkan dari: https://console.cloud.google.com/
    # Pastikan API yang diaktifkan: Maps JavaScript API, Geocoding API
    GOOGLE_MAPS_API_KEY = 'YOUR_GOOGLE_MAPS_API_KEY_HERE'  # Ganti dengan API key Anda
