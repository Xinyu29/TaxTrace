import random

class RiskScorer:
    def assess_risk(self, extracted, lhdn_data):
        """Assess risk level of invoice"""
        
        comparison = []
        reasoning_steps = []
        risk_score = 0
        
        # Compare invoice data with LHDN
        # In production, this would be more sophisticated
        
        # Check vendor name
        vendor = extracted.get('vendor_name', '')
        if not vendor or len(vendor) < 3:
            comparison.append({'field': 'Vendor Name', 'pdf': vendor or 'Missing', 'lhdn': 'Found in LHDN', 'match': False})
            risk_score += 1.5
            reasoning_steps.append({
                'title': 'Vendor Verification',
                'detail': f'Vendor name "{vendor}" does not match LHDN records. Possible fraud indicator.',
                'status': 'error'
            })
        else:
            comparison.append({'field': 'Vendor Name', 'pdf': vendor, 'lhdn': f'{vendor} (Registered)', 'match': True})
            reasoning_steps.append({
                'title': 'Vendor Verification',
                'detail': f'Vendor "{vendor}" verified in LHDN system.',
                'status': 'ok'
            })
        
        # Check invoice amount
        amount = extracted.get('amount', 0)
        if amount > 500000:
            risk_score += 1.0
            reasoning_steps.append({
                'title': 'High Value Transaction',
                'detail': f'Invoice amount RM {amount:,.2f} exceeds threshold of RM 500,000.',
                'status': 'warning'
            })
        
        # Check SST rate
        sst_rate = extracted.get('sst_rate', '0%')
        if sst_rate != '8%' and sst_rate != '0%':
            risk_score += 2.0
            comparison.append({'field': 'SST Rate', 'pdf': sst_rate, 'lhdn': '8% (Standard)', 'match': False})
            reasoning_steps.append({
                'title': 'SST Rate Mismatch',
                'detail': f'PDF shows {sst_rate} but LHDN expects standard 8% rate.',
                'status': 'error'
            })
        else:
            comparison.append({'field': 'SST Rate', 'pdf': sst_rate, 'lhdn': '8% (Standard)', 'match': True})
            reasoning_steps.append({
                'title': 'SST Rate Verified',
                'detail': f'SST rate {sst_rate} is within acceptable range.',
                'status': 'ok'
            })
        
        # Check registration number
        reg_no = extracted.get('reg_no', '')
        if not reg_no or len(reg_no) < 5:
            risk_score += 1.0
            comparison.append({'field': 'Reg Number', 'pdf': reg_no or 'Missing', 'lhdn': 'Registered', 'match': False})
            reasoning_steps.append({
                'title': 'Registration Number Missing',
                'detail': 'Company registration number not found in PDF.',
                'status': 'warning'
            })
        else:
            comparison.append({'field': 'Reg Number', 'pdf': reg_no, 'lhdn': 'Registered', 'match': True})
            reasoning_steps.append({
                'title': 'Registration Verified',
                'detail': f'Registration number {reg_no} is valid.',
                'status': 'ok'
            })
        
        # Check if LHDN validated
        if lhdn_data.get('status') == 'rejected':
            risk_score += 3.0
            reasoning_steps.append({
                'title': 'LHDN Rejection',
                'detail': 'Invoice rejected by MyInvois system. Immediate action required.',
                'status': 'error'
            })
        elif lhdn_data.get('status') == 'pending':
            risk_score += 0.5
            reasoning_steps.append({
                'title': 'LHDN Pending',
                'detail': 'Invoice not yet validated in MyInvois system.',
                'status': 'warning'
            })
        else:
            reasoning_steps.append({
                'title': 'LHDN Validated',
                'detail': 'Invoice successfully validated in MyInvois system.',
                'status': 'ok'
            })
        
        # Determine agent status
        if risk_score >= 6.0:
            agent_status = 'high_risk'
            flag_type = 'Multiple discrepancies'
            capital_at_risk = amount
        elif risk_score >= 3.0:
            agent_status = 'minor_flag'
            flag_type = 'Minor discrepancies'
            capital_at_risk = amount * 0.3
        else:
            agent_status = 'clean'
            flag_type = None
            capital_at_risk = 0
        
        return {
            'score': risk_score,
            'agent_status': agent_status,
            'flag_type': flag_type,
            'capital_at_risk': capital_at_risk,
            'comparison': comparison,
            'reasoning_steps': reasoning_steps,
            'category': agent_status.replace('_', ' ').title()
        }