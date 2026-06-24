from flask import Blueprint, jsonify, request
from models import db, Communication, Invoice
from datetime import datetime

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
    
    # Generate a draft email
    issues_text = '\n'.join([f'• {issue}' for issue in issues])
    
    body = f"""Dear Finance Team,

RE: Invoice {invoice_no} - Compliance Discrepancy Notice

We have identified the following discrepancies in the invoice from {vendor} (RM {amount:,.2f}):

{issues_text}

Action Required:
1. Please review the discrepancies and verify with the vendor
2. Request corrected invoice if necessary
3. Update records before payment processing

This is an automated notification from TaxTrace AI. Please respond within 48 hours.

Best regards,
TaxTrace AI Audit System
"""
    
    return jsonify({
        'to': f'finance@{vendor.lower().replace(" ", "")}.com.my',
        'subject': f'Invoice {invoice_no} — LHDN Compliance Discrepancy Notice',
        'body': body
    })

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