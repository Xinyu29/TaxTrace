from flask import Blueprint, jsonify
from models import db, Invoice

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
    if invoice.risk_score >= 7:
        risk_category = 'High-risk'
    elif invoice.risk_score >= 4:
        risk_category = 'Moderate risk'
    else:
        risk_category = 'Low risk'
    
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
        'reasoning_steps': reasoning
    })