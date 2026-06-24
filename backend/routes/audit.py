from flask import Blueprint, jsonify
from models import db, AuditLog

audit_bp = Blueprint('audit', __name__, url_prefix='/api/audit')

@audit_bp.route('', methods=['GET'])
def get_audit_log():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    return jsonify({
        'logs': [l.to_dict() for l in logs],
        'total': AuditLog.query.count()
    })