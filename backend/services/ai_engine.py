import os
import json
import PyPDF2
import re
from datetime import datetime

class AIEngine:
    def __init__(self):
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        
    def extract_invoice(self, file):
        """Extract invoice data from PDF using Claude or fallback to regex"""
        try:
            # Read PDF text
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            # If we have Claude API key, use it
            if self.api_key:
                return self._extract_with_claude(text)
            else:
                return self._extract_with_regex(text)
        except Exception as e:
            print(f"Extraction error: {e}")
            return self._extract_with_regex(text)
    
    def _extract_with_claude(self, text):
        """Use Claude API for extraction"""
        import anthropic
        
        client = anthropic.Anthropic(api_key=self.api_key)
        
        prompt = f"""Extract the following fields from this invoice text. Return ONLY a JSON object with these keys:
        vendor_name, invoice_no, invoice_date, reg_no, sst_id, amount, sst_rate, address
        
        Invoice text:
        {text[:4000]}
        
        Return valid JSON only."""
        
        try:
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse the response
            result = json.loads(response.content[0].text)
            return result
        except Exception as e:
            print(f"Claude API error: {e}")
            return self._extract_with_regex(text)
    
    def _extract_with_regex(self, text):
        """Fallback: Extract using regex patterns"""
        result = {}
        
        # Vendor name
        vendor_match = re.search(r'(?:Vendor|Supplier|From|Company):\s*(.+?)(?:\n|$)', text, re.I)
        result['vendor_name'] = vendor_match.group(1).strip() if vendor_match else 'Unknown Vendor'
        
        # Invoice number
        inv_match = re.search(r'(?:Invoice|INV|No|#)[\s:]*([A-Z0-9\-]+)', text, re.I)
        result['invoice_no'] = inv_match.group(1).strip() if inv_match else f'INV-{datetime.now().strftime("%Y%m%d")}-001'
        
        # Date
        date_match = re.search(r'(?:Date|Issued|Invoice Date)[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', text, re.I)
        result['invoice_date'] = date_match.group(1).strip() if date_match else datetime.now().strftime('%Y-%m-%d')
        
        # Amount
        amount_match = re.search(r'(?:Total|Amount|Sum)[\s:]*[RM$]?\s*([\d,]+\.?\d*)', text, re.I)
        result['amount'] = float(amount_match.group(1).replace(',', '')) if amount_match else 0.0
        
        # SST rate
        sst_match = re.search(r'SST\s*(?:Rate)?\s*[:]?\s*(\d+)%', text, re.I)
        result['sst_rate'] = f"{sst_match.group(1)}%" if sst_match else '0%'
        
        # Registration number
        reg_match = re.search(r'(?:Reg|Registration|Company).*?(?:No|Number)[\s:]*([A-Z0-9\-]+)', text, re.I)
        result['reg_no'] = reg_match.group(1).strip() if reg_match else ''
        
        result['sst_id'] = ''
        result['address'] = ''
        
        return result
    
    def draft_email(self, extracted, issues):
        """Draft a resolution email"""
        vendor = extracted.get('vendor_name', 'Vendor')
        invoice_no = extracted.get('invoice_no', 'INV-001')
        amount = extracted.get('amount', 0)
        
        issues_text = '\n'.join([f'• {issue}' for issue in issues[:5]])
        
        body = f"""Dear Finance Team,

RE: Invoice {invoice_no} - Compliance Discrepancy Notice

We have identified the following discrepancies in the invoice from {vendor} (RM {amount:,.2f}):

{issues_text}

Action Required:
1. Please review the discrepancies and verify with the vendor
2. Request corrected invoice if necessary
3. Update records before payment processing

This is an automated notification from TaxTrace AI. Please respond within 48 hours.

Best regards,
TaxTrace AI Audit System
"""
        
        return {
            'to': f'finance@{vendor.lower().replace(" ", "")}.com.my',
            'subject': f'Invoice {invoice_no} — LHDN Compliance Discrepancy Notice',
            'body': body
        }