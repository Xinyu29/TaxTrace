import uuid
import random
from datetime import datetime, timedelta
import json

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

flag_types = ['SST rate mismatch', 'Entity name mismatch', 'Tax code error', 'Rounding discrepancy']
statuses = ['clean', 'clean', 'clean', 'minor_flag', 'high_risk']

def seed_data(db):
    from models import Invoice, AuditLog, Communication
    
    if Invoice.query.count() > 0:
        print("Data already seeded")
        return
    
    print("Seeding 30 days of mock data...")
    today = datetime.utcnow()
    
    for day in range(30):
        date = today - timedelta(days=day)
        num_invoices = random.randint(3, 8)
        
        for _ in range(num_invoices):
            vendor = random.choice(vendors)
            status = random.choice(statuses)
            amount = random.randint(1000, 200000)
            
            invoice = Invoice(
                id=str(uuid.uuid4())[:8],
                vendor=vendor,
                invoice_no=f'INV-{date.strftime("%Y%m")}-{random.randint(100, 999)}',
                amount=amount,
                sst_rate=random.choice(['0%', '8%', '6%']),
                sst_amount=amount * 0.08 if random.random() > 0.3 else 0,
                invoice_date=date.strftime('%Y-%m-%d'),
                reg_no=f'REG-{random.randint(100000, 999999)}' if random.random() > 0.2 else '',
                lhdn_status=random.choice(['validated', 'validated', 'validated', 'pending', 'rejected']),
                agent_status=status,
                flag_type=random.choice(flag_types) if status != 'clean' else None,
                risk_score=random.uniform(0, 10),
                capital_at_risk=amount if status == 'high_risk' else (amount * 0.3 if status == 'minor_flag' else 0),
                extracted_data=json.dumps({'vendor_name': vendor, 'amount': amount}),
                created_at=date,
                updated_at=date
            )
            db.session.add(invoice)
    
    db.session.commit()
    print(f"Seeded {Invoice.query.count()} invoices")