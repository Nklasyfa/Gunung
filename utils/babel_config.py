from flask import g

def get_locale():
    """Tentukan locale/bahasa yang digunakan"""
    # Prioritas: session > cookies > default (id)
    return g.get('lang_code', 'id')

def before_request_handler():
    """Handler sebelum request diproses"""
    from flask import session
    # Set language code ke dalam g object untuk digunakan di template
    g.lang_code = session.get('language', 'id')
