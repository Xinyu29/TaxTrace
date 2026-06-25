import uuid
import random
from datetime import datetime, timedelta
import json
from services.risk_scorer import RiskScorer
from services.lhdn_validator import LHDNValidator

vendors = [
    'Matahari Trading Sdn Bhd',
    'Kencana Engineering (M) Sdn Bhd',
    'Sentosa Supplies Sdn Bhd',
    'Bina Jaya Construction Sdn Bhd',
    'Tropical Food Industries Sdn Bhd',
    'Sinar Jaya Manufacturing Sdn Bhd',
    'Kuala Lumpur Trading Co.',
    'Palm Oil Refinery Sdn Bhd',
    'Tech Solutions Asia Sdn Bhd',
    'HealthCare Pharma Sdn Bhd'
]

# Known good and bad vendors for deterministic testing
KNOWN_GOOD = ['Matahari Trading Sdn Bhd', 'Kencana Engineering (M) Sdn Bhd', 'Sentosa Supplies Sdn Bhd']
KNOWN_BAD = ['Fraudulent Company Sdn Bhd', 'Suspicious Trading Co', 'Ghost Supplier Enterprise']

def seed_data(db):
    from models import Invoice, AuditLog, Communication
    
    if Invoice.query.count() > 0:
        print("Data already seeded")
        return
    
    print("Seeding 30 days of mock data with REAL risk scoring...")
    today = datetime.utcnow()
    
    # Initialize validators for consistent scoring
    lhdn_validator = LHDNValidator()
    risk_scorer = RiskScorer()
    
    for day in range(30):
        date = today - timedelta(days=day)
        num_invoices = random.randint(3, 8)
        
        for _ in range(num_invoices):
            vendor = random.choice(vendors)
            
            # For demo consistency, ensure some known good/bad vendors
            if random.random() < 0.1:  # 10% chance of suspicious vendor
                vendor = random.choice(KNOWN_BAD)
            elif random.random() < 0.3:  # 30% chance of known good
                vendor = random.choice(KNOWN_GOOD)
            
            # Generate invoice data with more realistic patterns
            amount = random.randint(1000, 200000)
            
            # Sometimes create obvious issues for demo purposes
            # 20% chance of invalid SST rate
            if random.random() < 0.2:
                sst_rate = random.choice(['3%', '10%', '12%'])  # Invalid rates
            else:
                sst_rate = random.choice(['0%', '8%', '6%'])
            
            invoice_no = f'INV-{date.strftime("%Y%m")}-{random.randint(100, 999)}'
            
            # 20% chance of missing registration number
            if random.random() < 0.2:
                reg_no = ''
            else:
                reg_no = f'REG-{random.randint(100000, 999999)}'
            
            # Create extracted data structure
            extracted_data = {
                'vendor_name': vendor,
                'invoice_no': invoice_no,
                'invoice_date': date.strftime('%Y-%m-%d'),
                'amount': amount,
                'sst_rate': sst_rate,
                'reg_no': reg_no,
                'sst_id': f'SST-{random.randint(1000, 9999)}' if random.random() > 0.3 else '',
                'address': f'{random.randint(1, 999)} Jalan {random.choice(["Kuala", "Petaling", "Setia"])}'
            }
            
            # Use REAL validation and risk scoring (NOT random!)
            lhdn_result = lhdn_validator.validate_invoice(extracted_data)
            risk_result = risk_scorer.assess_risk(extracted_data, lhdn_result)
            
            # Create invoice with REAL scored data
            invoice = Invoice(
                id=str(uuid.uuid4())[:8],
                vendor=vendor,
                invoice_no=invoice_no,
                amount=amount,
                sst_rate=sst_rate,
                sst_amount=amount * 0.08 if sst_rate == '8%' else 0,
                invoice_date=date.strftime('%Y-%m-%d'),
                reg_no=reg_no,
                lhdn_status=lhdn_result.get('status', 'pending'),
                lhdn_response=json.dumps(lhdn_result),
                agent_status=risk_result.get('agent_status', 'clean'),
                flag_type=risk_result.get('flag_type'),
                risk_score=risk_result.get('score', 0),
                capital_at_risk=risk_result.get('capital_at_risk', 0),
                extracted_data=json.dumps(extracted_data),
                comparison_data=json.dumps(risk_result.get('comparison', [])),
                reasoning_steps=json.dumps(risk_result.get('reasoning_steps', [])),
                created_at=date,
                updated_at=date
            )
            db.session.add(invoice)
            
            # Generate a communication for flagged invoices
            if invoice.agent_status in ['minor_flag', 'high_risk']:
                # Create communication
                comm = Communication(
                    invoice_id=invoice.id,
                    vendor=vendor,
                    invoice_no=invoice_no,
                    date=date + timedelta(hours=random.randint(1, 48)),
                    type='resolution',
                    sent=random.choice([True, False]),
                    response=random.choice(['pending', 'awaiting', 'resolved']),
                    subject=f'Invoice {invoice_no} — LHDN Compliance Discrepancy Notice',
                    body=f'''Dear Finance Team,

RE: Invoice {invoice_no} - Compliance Discrepancy Notice

We have identified the following discrepancies in the invoice from {vendor} (RM {amount:,.2f}):

• {invoice.flag_type or "Multiple discrepancies"}

Action Required:
1. Please review the discrepancies and verify with the vendor
2. Request corrected invoice if necessary
3. Update records before payment processing

This is an automated notification from TaxTrace AI.

Best regards,
TaxTrace AI Audit System''',
                    to_email=f'finance@{vendor.lower().replace(" ", "")}.com.my'
                )
                db.session.add(comm)
    
    db.session.commit()
    print(f"Seeded {Invoice.query.count()} invoices with real risk scoring")