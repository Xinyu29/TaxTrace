from flask import Blueprint, jsonify
from models import db, Invoice
from sqlalchemy import func, and_
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('', methods=['GET'])
def get_dashboard():
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # Today's invoices
    today_invoices = Invoice.query.filter(
        Invoice.created_at >= today_start,
        Invoice.created_at <= today_end
    ).count()
    
    # Flags raised today
    flags_raised = Invoice.query.filter(
        Invoice.created_at >= today_start,
        Invoice.created_at <= today_end,
        Invoice.agent_status.in_(['minor_flag', 'high_risk'])
    ).count()
    
    # High risk today
    high_risk = Invoice.query.filter(
        Invoice.created_at >= today_start,
        Invoice.created_at <= today_end,
        Invoice.agent_status == 'high_risk'
    ).count()
    
    # Capital at risk (total amount of high-risk invoices)
    capital_at_risk = db.session.query(
        func.sum(Invoice.amount)
    ).filter(
        Invoice.agent_status == 'high_risk',
        Invoice.lhdn_status != 'validated'
    ).scalar() or 0
    
    # Top vendors at risk
    top_vendors = db.session.query(
        Invoice.vendor,
        Invoice.agent_status,
        func.sum(Invoice.amount).label('total_amount'),
        func.count(Invoice.id).label('count')
    ).filter(
        Invoice.agent_status.in_(['minor_flag', 'high_risk'])
    ).group_by(Invoice.vendor, Invoice.agent_status).order_by(
        func.sum(Invoice.amount).desc()
    ).limit(10).all()
    
    top_vendors_data = []
    for v in top_vendors:
        level = 'high' if v.agent_status == 'high_risk' else 'minor'
        top_vendors_data.append({
            'vendor': v.vendor,
            'amount': float(v.total_amount or 0),
            'level': level,
            'count': v.count
        })
    
    # Weekly trend (last 6 weeks)
    weekly_trend = []
    for i in range(5, -1, -1):
        week_start = today - timedelta(days=(i * 7) + today.weekday())
        week_end = week_start + timedelta(days=6)
        
        clean = Invoice.query.filter(
            Invoice.created_at >= week_start,
            Invoice.created_at <= week_end,
            Invoice.agent_status == 'clean'
        ).count()
        
        minor = Invoice.query.filter(
            Invoice.created_at >= week_start,
            Invoice.created_at <= week_end,
            Invoice.agent_status == 'minor_flag'
        ).count()
        
        high = Invoice.query.filter(
            Invoice.created_at >= week_start,
            Invoice.created_at <= week_end,
            Invoice.agent_status == 'high_risk'
        ).count()
        
        weekly_trend.append({
            'week': f'Week {i+1}',
            'clean': clean,
            'minor': minor,
            'high_risk': high
        })
    
    # Discrepancy types
    discrepancy_types = db.session.query(
        Invoice.flag_type,
        func.count(Invoice.id).label('count')
    ).filter(
        Invoice.flag_type.isnot(None),
        Invoice.agent_status.in_(['minor_flag', 'high_risk'])
    ).group_by(Invoice.flag_type).all()
    
    discrepancy_types_data = [
        {'type': d.flag_type or 'Unknown', 'count': d.count}
        for d in discrepancy_types
    ]
    
    # Compliance rate
    total_invoices = Invoice.query.count()
    clean_invoices = Invoice.query.filter(Invoice.agent_status == 'clean').count()
    compliance_rate = round((clean_invoices / total_invoices * 100) if total_invoices > 0 else 0, 1)
    
    return jsonify({
        'invoices_today': today_invoices,
        'flags_raised': flags_raised,
        'high_risk': high_risk,
        'capital_at_risk': float(capital_at_risk),
        'compliance_rate': compliance_rate,
        'top_vendors_at_risk': top_vendors_data,
        'weekly_trend': weekly_trend,
        'discrepancy_types': discrepancy_types_data
    })