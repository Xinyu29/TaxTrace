from flask import Blueprint, jsonify
from models import db, Invoice, Communication

discrepancies_bp = Blueprint('discrepancies', __name__, url_prefix='/api/discrepancies')

@discrepancies_bp.route('', methods=['GET'])
def get_discrepancies():
    discrepancies = Invoice.query.filter(
        Invoice.agent_status.in_(['minor_flag', 'high_risk'])
    ).order_by(Invoice.risk_score.desc()).all()
    
    return jsonify({
        'discrepancies': [i.to_dict() for i in discrepancies]
    })

@discrepancies_bp.route('/<invoice_id>', methods=['GET'])
def get_discrepancy(invoice_id):
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return jsonify({'error': 'Not found'}), 404
    
    comparison = invoice.get_comparison() or []
    reasoning = invoice.get_reasoning() or []
    
    # Determine risk category
    if invoice.risk_score >= 6.0:
        risk_category = 'High-risk'
    elif invoice.risk_score >= 3.0:
        risk_category = 'Moderate risk'
    else:
        risk_category = 'Low risk'
    
    # Get the email from communications
    comm = Communication.query.filter_by(invoice_id=invoice_id).first()
    email = None
    if comm:
        email = {
            'to': comm.to_email,
            'subject': comm.subject,
            'body': comm.body
        }
    else:
        # Generate a default email if none exists
        from services.ai_engine import AIEngine
        ai_engine = AIEngine()
        extracted = invoice.get_extracted() or {}
        issues = [c.get('field') for c in comparison if not c.get('match', True)]
        email_data = ai_engine.draft_email(extracted, issues)
        email = {
            'to': email_data.get('to', f'finance@{invoice.vendor.lower().replace(" ", "")}.com.my'),
            'subject': email_data.get('subject', f'Invoice {invoice.invoice_no} — LHDN Compliance Discrepancy Notice'),
            'body': email_data.get('body', '')
        }
    
    return jsonify({
        'id': invoice.id,
        'vendor': invoice.vendor,
        'invoice_no': invoice.invoice_no,
        'amount': invoice.amount,
        'risk_score': invoice.risk_score,
        'risk_category': risk_category,
        'capital_at_risk': invoice.capital_at_risk,
        'agent_status': invoice.agent_status,
        'comparison': comparison,
        'reasoning_steps': reasoning,
        'email': email  # Always include email
    })