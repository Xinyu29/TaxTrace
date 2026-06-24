from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db
import os

def create_app():
    app = Flask(__name__, static_folder='../frontend', static_url_path='')
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
        return jsonify({'status': 'ok', 'api_key_set': bool(Config.ANTHROPIC_API_KEY)})
    
    @app.route('/')
    def serve_index():
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory(app.static_folder, path)
    
    with app.app_context():
        db.create_all()
        from data.init_db import seed_data
        seed_data(db)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)