from flask import Blueprint, jsonify, request
from models import db, Communication, Invoice
from datetime import datetime
from services.ai_engine import AIEngine

comms_bp = Blueprint('comms', __name__, url_prefix='/api/comms')

@comms_bp.route('', methods=['GET'])
def get_comms():
    comms = Communication.query.order_by(Communication.date.desc()).limit(50).all()
    return jsonify({
        'history': [c.to_dict() for c in comms]
    })

@comms_bp.route('/draft', methods=['POST'])
def draft_email():
    data = request.get_json()
    vendor = data.get('vendor', 'Vendor')
    invoice_no = data.get('invoice_no', 'INV-001')
    amount = data.get('amount', 0)
    issues = data.get('issues', [])
    
    # Use AI engine to draft email
    ai_engine = AIEngine()
    extracted = {
        'vendor_name': vendor,
        'invoice_no': invoice_no,
        'amount': amount
    }
    email = ai_engine.draft_email(extracted, issues)
    
    invoice_id = data.get('invoice_id')
    if invoice_id:
        comm = Communication(
            invoice_id=invoice_id,
            vendor=vendor,
            invoice_no=invoice_no,
            type='resolution',
            sent=False,
            response='pending',
            subject=email.get('subject', ''),
            body=email.get('body', ''),
            to_email=email.get('to', '')
        )
        db.session.add(comm)
        db.session.commit()
    
    return jsonify(email)

@comms_bp.route('/send', methods=['POST'])
def send_comms():
    data = request.get_json()
    
    comm = Communication(
        invoice_id=data.get('invoice_id'),
        vendor=data.get('vendor', 'Unknown'),
        invoice_no=data.get('invoice_no', 'INV-001'),
        type=data.get('type', 'resolution'),
        sent=True,
        response='awaiting',
        subject=data.get('subject', ''),
        body=data.get('body', ''),
        to_email=data.get('to', '')
    )
    db.session.add(comm)
    db.session.commit()
    
    return jsonify({'status': 'sent', 'id': comm.id})