from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, '..')

def create_app():
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
    print("Static folder resolved to:", app.static_folder)
    print("index.html exists there:", os.path.exists(os.path.join(app.static_folder, 'index.html')))
    app.config.from_object(Config)
    
    db.init_app(app)
    CORS(app, origins=Config.CORS_ORIGINS)
    
    # Register routes
    from routes.dashboard import dashboard_bp
    from routes.invoices import invoices_bp
    from routes.discrepancies import discrepancies_bp
    from routes.comms import comms_bp
    from routes.analytics import analytics_bp
    from routes.audit import audit_bp
    from routes.upload import upload_bp
    
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(discrepancies_bp)
    app.register_blueprint(comms_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(upload_bp)
    
    @app.route('/api/health')
    def health():
        return jsonify({
            'status': 'ok', 
            'api_key_set': bool(Config.ANTHROPIC_API_KEY or getattr(Config, 'GEMINI_API_KEY', False))
        })
    
    @app.route('/')
    def serve_index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        # Try multiple locations
        # 1. Try frontend folder
        frontend_path = os.path.join(app.static_folder, 'frontend', path)
        if os.path.exists(frontend_path):
            return send_from_directory(os.path.join(app.static_folder, 'frontend'), path)
        
        # 2. Try root folder
        root_path = os.path.join(app.static_folder, path)
        if os.path.exists(root_path):
            return send_from_directory(app.static_folder, path)
        
        # 3. Try assets folder
        assets_path = os.path.join(app.static_folder, 'assets', path)
        if os.path.exists(assets_path):
            return send_from_directory(os.path.join(app.static_folder, 'assets'), path)
        
        return jsonify({'error': 'File not found'}), 404
    
    # ── Add CORB-Fixing Headers ──────────────────────────────────────────────
    
    @app.after_request
    def after_request(response):
        # Allow all origins for development
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, Accept, X-Requested-With')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        
        # Prevent CORB by allowing cross-origin responses to be read
        response.headers.add('Cross-Origin-Resource-Policy', 'cross-origin')
        response.headers.add('Cross-Origin-Opener-Policy', 'same-origin-allow-popups')
        response.headers.add('Cross-Origin-Embedder-Policy', 'unsafe-none')
        
        # Force correct content-type for JSON responses
        if response.content_type and 'application/json' in response.content_type:
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
        
        return response
    
    with app.app_context():
        db.create_all()
        from data.init_db import seed_data
        seed_data(db)
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = getattr(Config, 'PORT', 3000)
    debug = getattr(Config, 'DEBUG', True)
    app.run(host='0.0.0.0', port=port, debug=debug)