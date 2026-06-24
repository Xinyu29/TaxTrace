import os
import json
import requests
from datetime import datetime

class LHDNValidator:
    def __init__(self):
        self.api_url = os.environ.get('LHDN_API_URL', 'https://api.myinvois.hasil.gov.my/v1')
        self.api_key = os.environ.get('LHDN_API_KEY')
    
    def validate_invoice(self, extracted):
        """Validate invoice against LHDN MyInvois system"""
        
        # For demo, return mock validation data
        # In production, this would call the actual LHDN API
        
        invoice_no = extracted.get('invoice_no', 'INV-001')
        vendor = extracted.get('vendor_name', 'Unknown')
        
        # Simulate validation response
        # Randomly mark some as validated, some as rejected
        import random
        statuses = ['validated', 'validated', 'validated', 'pending', 'rejected']
        
        return {
            'status': random.choice(statuses),
            'invoice_no': invoice_no,
            'vendor': vendor,
            'validated_at': datetime.utcnow().isoformat(),
            'reference': f'LHDN-{datetime.now().strftime("%Y%m")}-{random.randint(1000, 9999)}',
            'remarks': 'Validation completed' if status != 'rejected' else 'Tax code mismatch'
        }