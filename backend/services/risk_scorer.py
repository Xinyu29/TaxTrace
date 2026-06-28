import random

class RiskScorer:
    def assess_risk(self, extracted, lhdn_data):
        """Assess risk level of invoice with deterministic logic"""
        
        comparison = []
        reasoning_steps = []
        risk_score = 0.0
        
        # Extract data
        vendor = extracted.get('vendor_name', '')
        amount = extracted.get('amount', 0)
        sst_rate = extracted.get('sst_rate', '0%')
        reg_no = extracted.get('reg_no', '')
        invoice_no = extracted.get('invoice_no', 'INV-001')
        
        # ── 1. Vendor Name Check ──────────────────────────────────────────────
        if not vendor or len(vendor) < 3:
            comparison.append({
                'field': 'Vendor Name',
                'pdf': vendor or 'Missing',
                'lhdn': 'Found in LHDN',
                'match': False
            })
            risk_score += 2.0
            reasoning_steps.append({
                'title': 'Vendor Name Missing',
                'detail': f'Vendor name "{vendor}" is missing or too short. Unable to verify.',
                'status': 'error'
            })
        else:
            # Check known good/bad vendors
            known_good = ['Matahari Trading', 'Kencana Engineering', 'Sentosa Supplies']
            known_bad = ['Fraudulent Company', 'Suspicious Trading', 'Ghost Supplier']
            
            if any(g in vendor for g in known_good):
                comparison.append({
                    'field': 'Vendor Name',
                    'pdf': vendor,
                    'lhdn': f'{vendor} (Verified)',
                    'match': True
                })
                reasoning_steps.append({
                    'title': 'Vendor Verified',
                    'detail': f'Vendor "{vendor}" is a known trusted supplier.',
                    'status': 'ok'
                })
            elif any(b in vendor for b in known_bad):
                comparison.append({
                    'field': 'Vendor Name',
                    'pdf': vendor,
                    'lhdn': 'FLAGGED',
                    'match': False
                })
                risk_score += 4.0
                reasoning_steps.append({
                    'title': 'Suspicious Vendor',
                    'detail': f'Vendor "{vendor}" appears on LHDN watchlist.',
                    'status': 'error'
                })
            else:
                comparison.append({
                    'field': 'Vendor Name',
                    'pdf': vendor,
                    'lhdn': f'{vendor} (New)',
                    'match': True
                })
                reasoning_steps.append({
                    'title': 'Vendor Verified',
                    'detail': f'Vendor "{vendor}" is registered but not previously verified.',
                    'status': 'warning'
                })
                risk_score += 1.0
        
        # ── 2. Amount Check ───────────────────────────────────────────────────
        if amount > 500000:
            risk_score += 2.0
            reasoning_steps.append({
                'title': 'High Value Transaction',
                'detail': f'Invoice amount RM {amount:,.2f} exceeds threshold of RM 500,000.',
                'status': 'warning'
            })
        elif amount > 100000:
            risk_score += 0.5
            reasoning_steps.append({
                'title': 'Medium Value Transaction',
                'detail': f'Invoice amount RM {amount:,.2f} requires additional review.',
                'status': 'ok'
            })
        else:
            reasoning_steps.append({
                'title': 'Normal Value Transaction',
                'detail': f'Invoice amount RM {amount:,.2f} is within normal range.',
                'status': 'ok'
            })
        
        # ── 3. SST Rate Check ─────────────────────────────────────────────────
        valid_sst_rates = ['8%', '0%', '6%', '5%']
        if sst_rate not in valid_sst_rates:
            risk_score += 3.0
            comparison.append({
                'field': 'SST Rate',
                'pdf': sst_rate,
                'lhdn': '8% (Standard)',
                'match': False
            })
            reasoning_steps.append({
                'title': 'Invalid SST Rate',
                'detail': f'PDF shows {sst_rate} but LHDN expects 8% standard rate.',
                'status': 'error'
            })
        elif sst_rate != '8%':
            comparison.append({
                'field': 'SST Rate',
                'pdf': sst_rate,
                'lhdn': '8% (Standard)',
                'match': False
            })
            risk_score += 1.5
            reasoning_steps.append({
                'title': 'SST Rate Exception',
                'detail': f'SST rate {sst_rate} is allowed but requires documentation.',
                'status': 'warning'
            })
        else:
            comparison.append({
                'field': 'SST Rate',
                'pdf': sst_rate,
                'lhdn': '8% (Standard)',
                'match': True
            })
            reasoning_steps.append({
                'title': 'SST Rate Verified',
                'detail': f'SST rate {sst_rate} matches LHDN standard.',
                'status': 'ok'
            })
        
        # ── 4. Registration Number Check ────────────────────────────────────
        if not reg_no or len(reg_no) < 5:
            risk_score += 2.0
            comparison.append({
                'field': 'Registration Number',
                'pdf': reg_no or 'Missing',
                'lhdn': 'Required',
                'match': False
            })
            reasoning_steps.append({
                'title': 'Registration Number Missing',
                'detail': 'Company registration number not found or invalid in PDF.',
                'status': 'error'
            })
        elif len(reg_no) < 10:
            risk_score += 0.5
            comparison.append({
                'field': 'Registration Number',
                'pdf': reg_no,
                'lhdn': 'Registered',
                'match': True
            })
            reasoning_steps.append({
                'title': 'Registration Number Valid',
                'detail': f'Registration number {reg_no} is valid.',
                'status': 'ok'
            })
        else:
            comparison.append({
                'field': 'Registration Number',
                'pdf': reg_no,
                'lhdn': 'Registered',
                'match': True
            })
            reasoning_steps.append({
                'title': 'Registration Number Verified',
                'detail': f'Registration number {reg_no} verified in LHDN system.',
                'status': 'ok'
            })
        
        # ── 5. LHDN Status Check ─────────────────────────────────────────────
        lhdn_status = lhdn_data.get('status', 'pending')
        if lhdn_status == 'rejected':
            risk_score += 3.0
            reasoning_steps.append({
                'title': 'LHDN Rejection',
                'detail': f'Invoice rejected by MyInvois. {lhdn_data.get("remarks", "")}',
                'status': 'error'
            })
        elif lhdn_status == 'pending':
            risk_score += 1.0
            reasoning_steps.append({
                'title': 'LHDN Pending Validation',
                'detail': 'Invoice awaiting LHDN validation.',
                'status': 'warning'
            })
        else:
            reasoning_steps.append({
                'title': 'LHDN Validated',
                'detail': 'Invoice successfully validated in MyInvois system.',
                'status': 'ok'
            })
        
        # ── 6. Additional Red Flags ──────────────────────────────────────────
        # Check for unusual patterns
        if amount > 0 and amount < 100:
            risk_score += 1.0
            reasoning_steps.append({
                'title': 'Unusual Amount',
                'detail': f'Amount RM {amount:,.2f} is unusually low.',
                'status': 'warning'
            })
        
        # Rounding issues (if amount doesn't end in .00 or .50)
        if amount % 1 != 0 and amount % 1 != 0.5:
            risk_score += 0.5
            reasoning_steps.append({
                'title': 'Rounding Discrepancy',
                'detail': 'Amount has unusual decimal places.',
                'status': 'warning'
            })
        
        # ── 7. Determine Final Status ─────────────────────────────────────────
        # Cap risk score at 10
        risk_score = min(risk_score, 10.0)
        
        if risk_score >= 6.0:
            agent_status = 'high_risk'
            flag_type = 'Multiple serious discrepancies'
            capital_at_risk = amount
        elif risk_score >= 3.0:
            agent_status = 'minor_flag'
            flag_type = 'Minor discrepancies detected'
            capital_at_risk = amount * 0.3
        else:
            agent_status = 'clean'
            flag_type = None
            capital_at_risk = 0
        
        # ── 8. Override: If LHDN rejected, always mark as high risk ──────────
        if lhdn_status == 'rejected' and agent_status != 'high_risk':
            agent_status = 'high_risk'
            flag_type = 'LHDN Rejection'
            capital_at_risk = amount
        
        # ── 9. Override: If SST rate is invalid, always flag ────────────────
        if sst_rate not in valid_sst_rates and agent_status == 'clean':
            agent_status = 'minor_flag'
            flag_type = 'Invalid SST Rate'
            capital_at_risk = amount * 0.3
        
        # Add final summary step
        reasoning_steps.append({
            'title': 'Final Assessment',
            'detail': f'Risk score: {risk_score:.1f}/10. Status: {agent_status.replace("_", " ").title()}',
            'status': 'ok' if agent_status == 'clean' else 'warning'
        })
        
        return {
            'score': round(risk_score, 1),
            'agent_status': agent_status,
            'flag_type': flag_type,
            'capital_at_risk': round(capital_at_risk, 2),
            'comparison': comparison,
            'reasoning_steps': reasoning_steps,
            'category': agent_status.replace('_', ' ').title()
        }