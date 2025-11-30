from flask import Blueprint, jsonify, current_app

api_bp = Blueprint('api', __name__)

@api_bp.route('/cuaca/gunung/<int:gunung_id>')
def get_cuaca_gunung(gunung_id):
    """API endpoint untuk mendapatkan data cuaca gunung"""
    try:
        # Mock data - bisa diganti dengan API cuaca nyata
        cuaca_data = {
            'suhu': 15,
            'kondisi': 'Cerah',
            'angin': 8
        }
        return jsonify(cuaca_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
