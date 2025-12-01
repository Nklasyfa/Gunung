import os
from flask import Flask, g, redirect, url_for
from flask_mysqldb import MySQL
from flask_babel import Babel
from config import Config
from routes.auth import auth_bp
from routes.user import user_bp
from routes.admin import admin_bp
from routes.api import api_bp
from utils.babel_config import get_locale, before_request_handler

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(APP_ROOT, 'static')
TEMPLATE_FOLDER = os.path.join(APP_ROOT, 'templates')

# Inisialisasi Flask App
app = Flask(__name__,
            template_folder=TEMPLATE_FOLDER,
            static_folder=STATIC_FOLDER)

app.config.from_object(Config)
app.secret_key = 'super_secret_key_anda'

# Inisialisasi MySQL
mysql = MySQL(app)

# Inisialisasi Babel
babel = Babel(app, locale_selector=get_locale)

# Register Before Request Handler
app.before_request(before_request_handler)

# Root route - redirect to login
@app.route('/')
def index():
    return redirect(url_for('auth.login'))

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(api_bp, url_prefix='/api')

# Inject mysql ke dalam app context agar bisa diakses di blueprint
app.mysql = mysql

@admin_bp.route('/punish')
def punish_list():
    ...

@admin_bp.route('/punish/add', methods=['GET', 'POST'])
def punish_add():
    ...


if __name__ == '__main__':
    app.run(debug=True)
