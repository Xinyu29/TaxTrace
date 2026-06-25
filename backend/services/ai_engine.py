import os
import json
import PyPDF2
import re
from datetime import datetime

class AIEngine:
    def __init__(self):
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        self.gemini_api_key = os.environ.get('GEMINI_API_KEY')
        
    def extract_invoice(self, file):
        text = ""
        try:
            # Read PDF text
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            
            if not text.strip():
                print("No text extracted from PDF")
                return self._extract_with_regex("")
            
            # Try Gemini first if available
            if self.gemini_api_key:
                try:
                    return self._extract_with_gemini(text)
                except Exception as e:
                    print(f"Gemini API error: {e}")
                    # Fall through to Claude or regex
            
            # Try Claude if available
            if self.api_key:
                try:
                    return self._extract_with_claude(text)
                except Exception as e:
                    print(f"Claude API error: {e}")
                    return self._extract_with_regex(text)
            else:
                return self._extract_with_regex(text)
        except Exception as e:
            print(f"Extraction error: {e}")
            return self._extract_with_regex(text)
    
    def _extract_with_gemini(self, text):
        """Use Google Gemini API for extraction"""
        import google.generativeai as genai
        
        genai.configure(api_key=self.gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = """Extract the following fields from this invoice text. 
        Return ONLY a JSON object with these exact keys:
        vendor_name, invoice_no, invoice_date, reg_no, sst_id, amount, sst_rate, address
        
        IMPORTANT: 
        - Return ONLY valid JSON, no markdown, no code fences, no preamble
        - If a field is not found, use null
        - amount should be a number (not string)
        
        Invoice text:
        """ + text[:4000]
        
        try:
            response = model.generate_content(prompt)
            raw_text = response.text.strip()
            
            # Clean markdown code fences if present
            if raw_text.startswith('```'):
                raw_text = raw_text.strip('`')
                if raw_text.startswith('json'):
                    raw_text = raw_text[4:].strip()
            
            result = json.loads(raw_text)
            # Ensure all keys exist
            required_keys = ['vendor_name', 'invoice_no', 'invoice_date', 'reg_no', 'sst_id', 'amount', 'sst_rate', 'address']
            for key in required_keys:
                if key not in result:
                    result[key] = None
            return result
        except Exception as e:
            print(f"Gemini parse error: {e}")
            raise
    
    def _extract_with_claude(self, text):
        """Use Claude API for extraction"""
        import anthropic
        
        client = anthropic.Anthropic(api_key=self.api_key)
        
        prompt = """Extract the following fields from this invoice text. 
        Return ONLY a JSON object with these exact keys:
        vendor_name, invoice_no, invoice_date, reg_no, sst_id, amount, sst_rate, address
        
        IMPORTANT: 
        - Return ONLY valid JSON, no markdown, no code fences, no preamble
        - If a field is not found, use null
        - amount should be a number (not string)
        
        Invoice text:
        """ + text[:4000]
        
        try:
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            raw_text = response.content[0].text.strip()
            
            # Clean markdown code fences if present
            if raw_text.startswith('```'):
                raw_text = raw_text.strip('`')
                if raw_text.startswith('json'):
                    raw_text = raw_text[4:].strip()
            
            result = json.loads(raw_text)
            # Ensure all keys exist
            required_keys = ['vendor_name', 'invoice_no', 'invoice_date', 'reg_no', 'sst_id', 'amount', 'sst_rate', 'address']
            for key in required_keys:
                if key not in result:
                    result[key] = None
            return result
        except Exception as e:
            print(f"Claude parse error: {e}")
            raise
    
    def _extract_with_regex(self, text):
        """Fallback: Extract using regex patterns"""
        result = {
            'vendor_name': None,
            'invoice_no': None,
            'invoice_date': None,
            'reg_no': None,
            'sst_id': None,
            'amount': None,
            'sst_rate': None,
            'address': None
        }
        
        if not text:
            return result
        
        # Vendor name
        vendor_match = re.search(r'(?:Vendor|Supplier|From|Company):\s*(.+?)(?:\n|$)', text, re.I)
        if vendor_match:
            result['vendor_name'] = vendor_match.group(1).strip()
        
        # Invoice number
        inv_match = re.search(r'(?:Invoice|INV|No|#)[\s:]*([A-Z0-9\-]+)', text, re.I)
        if inv_match:
            result['invoice_no'] = inv_match.group(1).strip()
        else:
            result['invoice_no'] = f'INV-{datetime.now().strftime("%Y%m%d")}-001'
        
        # Date
        date_match = re.search(r'(?:Date|Issued|Invoice Date)[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', text, re.I)
        if date_match:
            result['invoice_date'] = date_match.group(1).strip()
        else:
            result['invoice_date'] = datetime.now().strftime('%Y-%m-%d')
        
        # Amount
        amount_match = re.search(r'(?:Total|Amount|Sum)[\s:]*[RM$]?\s*([\d,]+\.?\d*)', text, re.I)
        if amount_match:
            try:
                result['amount'] = float(amount_match.group(1).replace(',', ''))
            except:
                result['amount'] = 0.0
        else:
            result['amount'] = 0.0
        
        # SST rate
        sst_match = re.search(r'SST\s*(?:Rate)?\s*[:]?\s*(\d+)%', text, re.I)
        if sst_match:
            result['sst_rate'] = f"{sst_match.group(1)}%"
        else:
            result['sst_rate'] = '0%'
        
        # Registration number
        reg_match = re.search(r'(?:Reg|Registration|Company).*?(?:No|Number)[\s:]*([A-Z0-9\-]+)', text, re.I)
        if reg_match:
            result['reg_no'] = reg_match.group(1).strip()
        
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