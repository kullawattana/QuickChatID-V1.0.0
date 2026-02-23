"""
KYC Dashboard Application
Web interface for viewing and managing KYC verification records
"""

import os
from flask import Flask, render_template, jsonify, request, send_from_directory
from pathlib import Path

# Import database
from database import KYCRepository, init_db

app = Flask(__name__,
            template_folder='dashboard/templates',
            static_folder='dashboard/static')
app.json.ensure_ascii = False

# Initialize database
init_db()


@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/statistics')
def get_statistics():
    """Get KYC statistics"""
    try:
        stats = KYCRepository.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/verifications')
def get_verifications():
    """Get all KYC verification records"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        status = request.args.get('status', None)

        records = KYCRepository.get_all_records(
            limit=limit,
            offset=offset,
            status=status
        )

        return jsonify([record.to_dict() for record in records])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/verifications/<int:record_id>')
def get_verification(record_id):
    """Get specific KYC verification record"""
    try:
        record = KYCRepository.get_by_id(record_id)
        if record:
            return jsonify(record.to_dict())
        return jsonify({'error': 'Record not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/verifications/user/<user_id>')
def get_user_verification(user_id):
    """Get most recent KYC record for specific user"""
    try:
        record = KYCRepository.get_by_user_id(user_id)
        if record:
            return jsonify(record.to_dict())
        return jsonify({'error': 'Record not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search/id_number/<id_number>')
def search_by_id_number(id_number):
    """Search by Thai ID number"""
    try:
        record = KYCRepository.search_by_id_number(id_number)
        if record:
            return jsonify(record.to_dict())
        return jsonify({'error': 'Record not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search/name')
def search_by_name():
    """Search by name"""
    try:
        name = request.args.get('name', '')
        if not name:
            return jsonify({'error': 'Name parameter required'}), 400

        records = KYCRepository.search_by_name(name)
        return jsonify([record.to_dict() for record in records])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/verifications/<int:record_id>', methods=['DELETE'])
def delete_verification(record_id):
    """Delete KYC verification record"""
    try:
        success = KYCRepository.delete_record(record_id)
        if success:
            return jsonify({'message': 'Record deleted successfully'})
        return jsonify({'error': 'Record not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'KYC Dashboard',
        'database': 'connected'
    })


if __name__ == '__main__':
    PORT = 5002  # Use different port from LINE Bot (5001) and ADK (8000)

    print("=" * 60)
    print("KYC Dashboard Server")
    print("=" * 60)
    print(f"✓ Database initialized")
    print(f"✓ Dashboard UI: http://localhost:{PORT}/")
    print(f"✓ API endpoints:")
    print(f"  - GET  /api/statistics")
    print(f"  - GET  /api/verifications")
    print(f"  - GET  /api/verifications/<id>")
    print(f"  - GET  /api/verifications/user/<user_id>")
    print(f"  - GET  /api/search/id_number/<id_number>")
    print(f"  - GET  /api/search/name?name=<name>")
    print(f"  - DELETE /api/verifications/<id>")
    print("=" * 60)
    print(f"\n🚀 Starting server on http://0.0.0.0:{PORT}")
    print("=" * 60)

    app.run(host='0.0.0.0', port=PORT, debug=True)
