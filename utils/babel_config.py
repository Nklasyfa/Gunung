from flask import g, session

def get_locale():
    """Tentukan locale/bahasa yang digunakan"""
    return g.get('lang_code', 'id')

def before_request_handler():
    """Handler sebelum request diproses"""
    g.lang_code = session.get('language', 'id')
