from flask import Blueprint, jsonify, request
from models import db, Invoice, AuditLog
from datetime import datetime

invoices_bp = Blueprint('invoices', __name__, url_prefix='/api/invoices')

@invoices_bp.route('', methods=['GET'])
def get_invoices():
    invoices = Invoice.query.order_by(Invoice.created_at.desc()).limit(100).all()
    return jsonify({
        'invoices': [i.to_dict() for i in invoices]
    })

@invoices_bp.route('/<invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404
    
    return jsonify({
        **invoice.to_dict(),
        'extracted': invoice.get_extracted(),
        'comparison': invoice.get_comparison(),
        'reasoning': invoice.get_reasoning()
    })

@invoices_bp.route('/<invoice_id>/action', methods=['POST'])
def take_action(invoice_id):
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404
    
    data = request.get_json()
    action = data.get('action')
    
    if action not in ['send_comms', 'hold', 'approve']:
        return jsonify({'error': 'Invalid action'}), 400
    
    # Log the action
    log = AuditLog(
        agent='user',
        invoice_id=invoice_id,
        action=action,
        result='ok',
        result_label='Action recorded',
        details=f'User took action: {action}'
    )
    db.session.add(log)
    
    if action == 'approve':
        invoice.agent_status = 'clean'
        invoice.flag_type = None
    
    db.session.commit()
    
    return jsonify({'status': 'success', 'action': action})