from flask import Blueprint, request, jsonify, Response
from services.ai_engine import AIEngine
from services.lhdn_validator import LHDNValidator
from services.risk_scorer import RiskScorer
from models import db, Invoice, AuditLog
import json
import uuid
from datetime import datetime

upload_bp = Blueprint('upload', __name__, url_prefix='/api/upload')

@upload_bp.route('/invoice', methods=['POST'])
def upload_invoice():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are supported'}), 400
    
    def generate():
        # Step 1: Ingest
        yield f"data: {json.dumps({'step': 1, 'status': 'running', 'title': 'Ingesting PDF', 'detail': 'Processing file: {file.filename}'})}\n\n"
        
        # Step 2: AI Extract
        yield f"data: {json.dumps({'step': 2, 'status': 'running', 'title': 'AI Extraction', 'detail': 'Claude is analysing the invoice...'})}\n\n"
        
        ai_engine = AIEngine()
        extracted = ai_engine.extract_invoice(file)
        
        if not extracted:
            yield f"data: {json.dumps({'step': 2, 'status': 'error', 'title': 'AI Extraction Failed', 'detail': 'Could not extract data from PDF'})}\n\n"
            return
        
        yield f"data: {json.dumps({'step': 2, 'status': 'done', 'title': 'AI Extraction Complete', 'detail': 'Successfully extracted invoice data', 'extracted': extracted})}\n\n"
        
        # Step 3: LHDN Lookup
        yield f"data: {json.dumps({'step': 3, 'status': 'running', 'title': 'LHDN MyInvois Lookup', 'detail': 'Validating against LHDN database...'})}\n\n"
        
        validator = LHDNValidator()
        lhdn_data = validator.validate_invoice(extracted)
        
        yield f"data: {json.dumps({'step': 3, 'status': 'done', 'title': 'LHDN Validation Complete', 'detail': 'Cross-referenced with MyInvois system'})}\n\n"
        
        # Step 4: Risk Score
        yield f"data: {json.dumps({'step': 4, 'status': 'running', 'title': 'Risk Assessment', 'detail': 'Calculating risk score...'})}\n\n"
        
        scorer = RiskScorer()
        risk_result = scorer.assess_risk(extracted, lhdn_data)
        
        comparison = risk_result.get('comparison', [])
        risk_score = risk_result.get('score', 0)
        agent_status = risk_result.get('agent_status', 'clean')
        flag_type = risk_result.get('flag_type')
        capital_at_risk = risk_result.get('capital_at_risk', 0)
        
        yield f"data: {json.dumps({'step': 4, 'status': 'done', 'title': 'Risk Assessment Complete', 'detail': f'Risk score: {risk_score:.1f}/10', 'risk': risk_result})}\n\n"
        
        # Step 5: Draft Email
        yield f"data: {json.dumps({'step': 5, 'status': 'running', 'title': 'Drafting Resolution Email', 'detail': 'AI is generating vendor communication...'})}\n\n"
        
        if agent_status in ['minor_flag', 'high_risk']:
            issues = [c.get('field') for c in comparison if not c.get('match', True)]
            email = ai_engine.draft_email(extracted, issues)
            yield f"data: {json.dumps({'step': 5, 'status': 'done', 'title': 'Email Drafted', 'detail': 'Resolution email ready for review', 'email': email})}\n\n"
        else:
            yield f"data: {json.dumps({'step': 5, 'status': 'done', 'title': 'No Email Needed', 'detail': 'Invoice is clean - no discrepancies found'})}\n\n"
        
        # Step 6: Complete - Save to database
        yield f"data: {json.dumps({'step': 6, 'status': 'running', 'title': 'Saving to Database', 'detail': 'Recording results...'})}\n\n"
        
        invoice_id = str(uuid.uuid4())[:8]
        invoice = Invoice(
            id=invoice_id,
            vendor=extracted.get('vendor_name', 'Unknown'),
            invoice_no=extracted.get('invoice_no', 'INV-001'),
            amount=extracted.get('amount', 0),
            sst_rate=extracted.get('sst_rate', '0%'),
            invoice_date=extracted.get('invoice_date'),
            reg_no=extracted.get('reg_no'),
            sst_id=extracted.get('sst_id'),
            address=extracted.get('address'),
            lhdn_status=lhdn_data.get('status', 'pending'),
            agent_status=agent_status,
            flag_type=flag_type,
            risk_score=risk_score,
            capital_at_risk=capital_at_risk,
            extracted_data=json.dumps(extracted),
            comparison_data=json.dumps(comparison),
            reasoning_steps=json.dumps(risk_result.get('reasoning_steps', []))
        )
        db.session.add(invoice)
        
        # Audit log
        audit = AuditLog(
            agent='ai_agent',
            invoice_id=invoice_id,
            action='upload_analyse',
            result=agent_status,
            result_label=agent_status.replace('_', ' ').title(),
            details=f'Risk score: {risk_score:.1f}'
        )
        db.session.add(audit)
        db.session.commit()
        
        yield f"data: {json.dumps({'step': 6, 'status': 'complete', 'title': '✅ Pipeline Complete', 'detail': f'Invoice {invoice_id} processed successfully'})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')