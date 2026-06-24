from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.String(36), primary_key=True)
    vendor = db.Column(db.String(200), nullable=False)
    invoice_no = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    sst_rate = db.Column(db.String(20))
    sst_amount = db.Column(db.Float)
    invoice_date = db.Column(db.String(20))
    reg_no = db.Column(db.String(50))
    sst_id = db.Column(db.String(50))
    address = db.Column(db.Text)
    lhdn_status = db.Column(db.String(20), default='pending')
    lhdn_response = db.Column(db.Text)
    agent_status = db.Column(db.String(20), default='pending')
    flag_type = db.Column(db.String(100))
    risk_score = db.Column(db.Float, default=0.0)
    capital_at_risk = db.Column(db.Float, default=0.0)
    extracted_data = db.Column(db.Text)
    comparison_data = db.Column(db.Text)
    reasoning_steps = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'vendor': self.vendor,
            'invoice_no': self.invoice_no,
            'amount': self.amount,
            'sst_rate': self.sst_rate,
            'sst_amount': self.sst_amount,
            'invoice_date': self.invoice_date,
            'reg_no': self.reg_no,
            'sst_id': self.sst_id,
            'address': self.address,
            'lhdn_status': self.lhdn_status,
            'agent_status': self.agent_status,
            'flag_type': self.flag_type,
            'risk_score': self.risk_score,
            'capital_at_risk': self.capital_at_risk,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def get_extracted(self):
        return json.loads(self.extracted_data) if self.extracted_data else None
    
    def get_comparison(self):
        return json.loads(self.comparison_data) if self.comparison_data else None
    
    def get_reasoning(self):
        return json.loads(self.reasoning_steps) if self.reasoning_steps else None

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    agent = db.Column(db.String(50), nullable=False)
    invoice_id = db.Column(db.String(36), db.ForeignKey('invoices.id'))
    action = db.Column(db.String(100), nullable=False)
    result = db.Column(db.String(20), nullable=False)
    result_label = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'agent': self.agent,
            'invoice': self.invoice_id,
            'action': self.action,
            'result': self.result,
            'result_label': self.result_label,
            'details': self.details,
        }

class Communication(db.Model):
    __tablename__ = 'communications'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.String(36), db.ForeignKey('invoices.id'))
    vendor = db.Column(db.String(200), nullable=False)
    invoice_no = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(50), nullable=False)
    sent = db.Column(db.Boolean, default=False)
    response = db.Column(db.String(50), default='pending')
    subject = db.Column(db.String(500))
    body = db.Column(db.Text)
    to_email = db.Column(db.String(200))
    
    def to_dict(self):
        return {
            'id': self.id,
            'invoice': self.invoice_id,
            'vendor': self.vendor,
            'invoice_no': self.invoice_no,
            'date': self.date.isoformat() if self.date else None,
            'type': self.type,
            'sent': self.sent,
            'response': self.response,
            'subject': self.subject,
            'body': self.body,
            'to_email': self.to_email,
        }