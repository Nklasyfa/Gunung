from routes.auth import auth_bp
from routes.user import user_bp
from routes.admin import admin_bp
from routes.api import api_bp

__all__ = ['auth_bp', 'user_bp', 'admin_bp', 'api_bp']
