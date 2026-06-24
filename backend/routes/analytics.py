from flask import Blueprint, jsonify
from models import db, Invoice
from sqlalchemy import func
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('', methods=['GET'])
def get_analytics():
    # Compliance rate MTD
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    
    total_mtd = Invoice.query.filter(Invoice.created_at >= month_start).count()
    clean_mtd = Invoice.query.filter(
        Invoice.created_at >= month_start,
        Invoice.agent_status == 'clean'
    ).count()
    
    compliance_rate = round((clean_mtd / total_mtd * 100) if total_mtd > 0 else 0, 1)
    
    # Avg resolution time (simplified)
    avg_days = 2.4  # Mock value
    
    # SST recovered
    sst_recovered = db.session.query(
        func.sum(Invoice.sst_amount)
    ).filter(
        Invoice.agent_status == 'clean',
        Invoice.lhdn_status == 'validated'
    ).scalar() or 0
    
    # LHDN rejections avoided
    rejections_avoided = Invoice.query.filter(
        Invoice.agent_status == 'high_risk',
        Invoice.lhdn_status != 'validated'
    ).count()
    
    # Monthly trend (last 6 months)
    monthly_trend = []
    for i in range(5, -1, -1):
        month_date = now - timedelta(days=30 * i)
        month_name = month_date.strftime('%b')
        
        month_invoices = Invoice.query.filter(
            func.strftime('%Y-%m', Invoice.created_at) == month_date.strftime('%Y-%m')
        ).count()
        
        month_clean = Invoice.query.filter(
            func.strftime('%Y-%m', Invoice.created_at) == month_date.strftime('%Y-%m'),
            Invoice.agent_status == 'clean'
        ).count()
        
        rate = round((month_clean / month_invoices * 100) if month_invoices > 0 else 0, 1)
        
        monthly_trend.append({
            'month': month_name,
            'rate': rate
        })
    
    return jsonify({
        'compliance_rate_mtd': compliance_rate,
        'avg_resolution_days': avg_days,
        'sst_recovered': float(sst_recovered),
        'lhdn_rejections_avoided': rejections_avoided,
        'monthly_trend': monthly_trend
    })