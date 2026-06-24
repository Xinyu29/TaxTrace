"""
TaxTrace AI — Backend Server
==============================
WOW Feature: Real PDF Upload → Full AI Agent Pipeline
  1. Upload vendor invoice PDF
  2. Claude vision extracts all fields (vendor, SST, amounts, reg no, address)
  3. Auto cross-validates against mock LHDN MyInvois JSON
  4. Risk scoring engine categorises the discrepancy
  5. Bilingual (EN/BM) resolution email drafted
  6. All steps streamed back live via SSE so the frontend shows a live agent trace

Run:
    ANTHROPIC_API_KEY=sk-... python server.py
"""

import os, io, json, re, base64, uuid, time
from datetime import datetime
from typing import Optional

import anthropic
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import PyPDF2

# ── App setup ────────────────────────────────────────────────────────────────

app = FastAPI(title="TaxTrace AI", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
client = anthropic.Anthropic(api_key=ANTHROPIC_KEY) if ANTHROPIC_KEY else None

# ── Mock LHDN MyInvois database ───────────────────────────────────────────────
# In production this would call the real LHDN API

LHDN_DB = {
    "1234567-A": {
        "legal_name": "Matahari Trading (M) Sdn Bhd",
        "sst_id": "B12-3456-78901234",
        "sst_rate": "0%",
        "sst_class": "E3 exemption",
        "address": None,          # no SSM physical record → ghost supplier signal
        "lhdn_status": "validated",
        "tin": "C1234567890",
    },
    "7654321-B": {
        "legal_name": "Buildcon (M) Sdn Bhd",
        "sst_id": "B98-7654-32109876",
        "sst_rate": "6%",
        "sst_class": "Standard rated",
        "address": "Lot 12, Jalan Industri 3, Shah Alam, Selangor",
        "lhdn_status": "rejected",
        "tin": "C9876543210",
    },
    "1122334-C": {
        "legal_name": "Apex Roofing Plt",
        "sst_id": "B11-2233-44556677",
        "sst_rate": "0%",
        "sst_class": "E1 exemption",
        "address": "No 5, Jalan Kilang, Petaling Jaya, Selangor",
        "lhdn_status": "pending",
        "tin": "C1122334455",
    },
    # Fallback for demo invoices without a reg no
    "DEMO": {
        "legal_name": "Demo Vendor Sdn Bhd",
        "sst_id": "B00-0000-00000000",
        "sst_rate": "6%",
        "sst_class": "Standard rated",
        "address": "No 1, Jalan Demo, Kuala Lumpur",
        "lhdn_status": "validated",
        "tin": "C0000000000",
    },
}

# ── In-memory stores ──────────────────────────────────────────────────────────

INVOICES = [
    {"id":"INV-001","vendor":"Matahari Trading Sdn Bhd","invoice_no":"MT-2026-0891","amount":128000.00,"sst_rate":"8%","lhdn_status":"validated","agent_status":"high_risk","flag_type":"Ghost supplier flag","capital_at_risk":128000.00,"risk_score":9.1,"date":"2026-06-23","status":"blocked"},
    {"id":"INV-002","vendor":"Buildcon Sdn Bhd","invoice_no":"BC-2026-1122","amount":82400.00,"sst_rate":"6%","lhdn_status":"rejected","agent_status":"high_risk","flag_type":"Entity name mismatch","capital_at_risk":82400.00,"risk_score":8.4,"date":"2026-06-22","status":"blocked"},
    {"id":"INV-003","vendor":"Apex Roofing Plt","invoice_no":"AR-2026-0077","amount":61700.00,"sst_rate":"8%","lhdn_status":"pending","agent_status":"high_risk","flag_type":"SST rate invalid","capital_at_risk":61700.00,"risk_score":7.8,"date":"2026-06-22","status":"pending_review"},
    {"id":"INV-004","vendor":"K&F Supplies Bhd","invoice_no":"KF-2026-3301","amount":34500.00,"sst_rate":"6%","lhdn_status":"pending","agent_status":"minor_flag","flag_type":"Tax code mismatch","capital_at_risk":34500.00,"risk_score":5.2,"date":"2026-06-21","status":"pending_review"},
    {"id":"INV-005","vendor":"SteelMax Plt","invoice_no":"SM-2026-0543","amount":1200.00,"sst_rate":"6%","lhdn_status":"validated","agent_status":"minor_flag","flag_type":"Rounding ±RM0.02","capital_at_risk":0.02,"risk_score":1.5,"date":"2026-06-21","status":"auto_cleared"},
    {"id":"INV-006","vendor":"Global Steel Bhd","invoice_no":"GS-2026-2290","amount":210500.00,"sst_rate":"6%","lhdn_status":"validated","agent_status":"clean","flag_type":None,"capital_at_risk":0,"risk_score":0.2,"date":"2026-06-20","status":"approved"},
    {"id":"INV-007","vendor":"Reka Jaya Plt","invoice_no":"RJ-2026-0410","amount":17800.00,"sst_rate":"0%","lhdn_status":"validated","agent_status":"clean","flag_type":None,"capital_at_risk":0,"risk_score":0.1,"date":"2026-06-20","status":"approved"},
]

DISCREPANCIES = {
    "INV-001": {
        "invoice_id":"INV-001","vendor":"Matahari Trading Sdn Bhd","invoice_no":"MT-2026-0891","amount":128000.00,"risk_score":9.1,"risk_category":"Ghost supplier flag","capital_at_risk":128000.00,
        "reasoning_steps":[
            {"status":"ok","title":"Step 1 — Document ingested","detail":"PDF extracted: vendor name \"Matahari Trading Sdn Bhd\", Reg. No. 1234567-A, SST ID: B12-3456-78901234, Amount RM 128,000, SST 8%."},
            {"status":"ok","title":"Step 2 — LHDN XML retrieved","detail":"MyInvois JSON validated record shows entity \"Matahari Trading (M) Sdn Bhd\", Reg. No. 1234567-A, SST: 0% exemption (class E3)."},
            {"status":"error","title":"Step 3 — Entity name mismatch detected","detail":"PDF omits \"(M)\" suffix. Registration number matches, but legal entity name diverges. Cross-referencing SSM database: \"(M)\" indicates a different incorporation class."},
            {"status":"error","title":"Step 4 — SST rate conflict","detail":"PDF claims 8% SST totalling RM 9,481.48. LHDN record grants E3 exemption (0%). Potential fraudulent SST collection of RM 9,481.48."},
            {"status":"error","title":"Step 5 — Ghost supplier pattern matched","detail":"Vendor address \"Lot 7, Jalan Industri, Klang\" returns zero physical presence in SSM records. Flagged as potential shell entity. Payment blocked pending human approval."},
        ],
        "comparison":[
            {"field":"Legal entity name","pdf":"Matahari Trading Sdn Bhd","lhdn":"Matahari Trading (M) Sdn Bhd","match":False},
            {"field":"SST rate (Line 1)","pdf":"8%","lhdn":"0% (E3 exemption)","match":False},
            {"field":"SST amount charged","pdf":"RM 9,481.48","lhdn":"RM 0.00","match":False},
            {"field":"Registration number","pdf":"1234567-A ✓","lhdn":"1234567-A ✓","match":True},
            {"field":"Physical address (SSM)","pdf":"Lot 7, Jalan Industri, Klang","lhdn":"No record found","match":False},
        ]
    }
}

AUDIT_LOG = [
    {"timestamp":"2026-06-23 09:41:02","agent":"Risk eval","invoice":"MT-2026-0891","action":"Ghost supplier pattern match","result":"high_risk","result_label":"High-risk flagged"},
    {"timestamp":"2026-06-23 09:40:58","agent":"Parser","invoice":"MT-2026-0891","action":"SST rate extracted: 8%","result":"warning","result_label":"Mismatch vs LHDN 0%"},
    {"timestamp":"2026-06-23 09:40:51","agent":"Ingest","invoice":"MT-2026-0891","action":"PDF received from mailbox","result":"ok","result_label":"Parsed OK"},
    {"timestamp":"2026-06-23 09:38:12","agent":"Comms","invoice":"BC-2026-1122","action":"Resolution email drafted + sent","result":"ok","result_label":"Delivered"},
    {"timestamp":"2026-06-23 09:37:44","agent":"Risk eval","invoice":"BC-2026-1122","action":"Entity name divergence scored","result":"high_risk","result_label":"Score 8.4 / 10"},
    {"timestamp":"2026-06-23 09:22:03","agent":"Human","invoice":"KF-2026-3201","action":"Finance director override — approve","result":"ok","result_label":"Payment released"},
    {"timestamp":"2026-06-23 09:18:30","agent":"Parser","invoice":"GS-2026-2290","action":"Full cross-validation vs LHDN JSON","result":"ok","result_label":"Clean — no flags"},
    {"timestamp":"2026-06-22 16:52:11","agent":"Comms","invoice":"AR-2026-0077","action":"Corrected invoice received from vendor","result":"ok","result_label":"Resolved"},
    {"timestamp":"2026-06-22 14:30:05","agent":"Risk eval","invoice":"SM-2026-0543","action":"Rounding difference ±RM 0.02 detected","result":"warning","result_label":"Minor — auto-cleared"},
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def log(agent: str, invoice: str, action: str, result: str, label: str):
    AUDIT_LOG.insert(0, {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "agent": agent, "invoice": invoice,
        "action": action, "result": result, "result_label": label,
    })

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract raw text from a PDF file."""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text.strip()
    except Exception as e:
        return f"[PDF extraction error: {e}]"

def lhdn_lookup(reg_no: str) -> dict:
    """Mock LHDN MyInvois API lookup by company registration number."""
    clean = reg_no.strip().upper()
    return LHDN_DB.get(clean, LHDN_DB["DEMO"])

def compute_risk(extracted: dict, lhdn: dict) -> dict:
    """
    Deterministic risk scoring matrix.
    Returns score 0-10, category, and list of mismatches.
    """
    score = 0.0
    mismatches = []
    comparison = []

    # ── Entity name check ──────────────────────────────────────────────────
    pdf_name  = extracted.get("vendor_name", "").strip()
    lhdn_name = lhdn.get("legal_name", "").strip()
    name_match = pdf_name.lower() == lhdn_name.lower()
    comparison.append({"field": "Legal entity name", "pdf": pdf_name, "lhdn": lhdn_name, "match": name_match})
    if not name_match:
        score += 3.5
        mismatches.append(f"Entity name: PDF says '{pdf_name}', LHDN says '{lhdn_name}'")

    # ── SST rate check ─────────────────────────────────────────────────────
    pdf_sst  = extracted.get("sst_rate", "").strip()
    lhdn_sst = lhdn.get("sst_rate", "").strip()
    sst_match = pdf_sst == lhdn_sst
    comparison.append({"field": "SST rate", "pdf": pdf_sst, "lhdn": f"{lhdn_sst} ({lhdn.get('sst_class','')})", "match": sst_match})
    if not sst_match:
        score += 3.0
        mismatches.append(f"SST rate: PDF {pdf_sst} vs LHDN {lhdn_sst} ({lhdn.get('sst_class','')})")

    # ── SST amount rounding ────────────────────────────────────────────────
    try:
        pdf_amount  = float(str(extracted.get("amount", 0)).replace(",",""))
        pdf_sst_pct = float(pdf_sst.replace("%","")) / 100
        lhdn_sst_pct= float(lhdn_sst.replace("%","")) / 100
        expected_tax = round(pdf_amount * lhdn_sst_pct, 2)
        charged_tax  = round(pdf_amount * pdf_sst_pct, 2)
        tax_diff     = abs(charged_tax - expected_tax)
        if tax_diff > 0.10:
            score += min(tax_diff / pdf_amount * 50, 2.0)   # cap at +2
            mismatches.append(f"SST amount: charged RM {charged_tax:,.2f}, should be RM {expected_tax:,.2f} (diff RM {tax_diff:,.2f})")
            comparison.append({"field": "SST amount", "pdf": f"RM {charged_tax:,.2f}", "lhdn": f"RM {expected_tax:,.2f}", "match": False})
        elif tax_diff > 0:
            score += 0.2
            comparison.append({"field": "SST amount", "pdf": f"RM {charged_tax:,.2f}", "lhdn": f"RM {expected_tax:,.2f}", "match": True})
        else:
            comparison.append({"field": "SST amount", "pdf": f"RM {charged_tax:,.2f}", "lhdn": f"RM {expected_tax:,.2f}", "match": True})
    except Exception:
        pass

    # ── Registration number ────────────────────────────────────────────────
    pdf_reg  = extracted.get("reg_no", "")
    comparison.append({"field": "Registration number", "pdf": pdf_reg or "Not found", "lhdn": extracted.get("reg_no", ""), "match": bool(pdf_reg)})

    # ── Ghost supplier: no physical address in SSM ─────────────────────────
    has_address = bool(lhdn.get("address"))
    comparison.append({"field": "Physical address (SSM)", "pdf": extracted.get("address", "Not stated"), "lhdn": lhdn.get("address") or "No record found", "match": has_address})
    if not has_address:
        score += 2.0
        mismatches.append("Ghost supplier: no physical address found in SSM records")

    # ── LHDN portal status ─────────────────────────────────────────────────
    if lhdn.get("lhdn_status") == "rejected":
        score += 1.5

    score = round(min(score, 10.0), 1)

    # ── Categorise ─────────────────────────────────────────────────────────
    if not has_address and score >= 7:
        category = "Ghost Supplier Flag"
        agent_status = "high_risk"
    elif not name_match and score >= 6:
        category = "Entity Name Mismatch"
        agent_status = "high_risk"
    elif not sst_match and score >= 4:
        category = "SST Rate Invalid"
        agent_status = "high_risk"
    elif score >= 3:
        category = "Tax Code Mismatch"
        agent_status = "minor_flag"
    elif score > 0:
        category = "Minor Rounding Difference"
        agent_status = "minor_flag"
    else:
        category = "Clean"
        agent_status = "clean"

    # Capital at risk = full invoice amount for high risk, 0 for clean
    cap_risk = float(str(extracted.get("amount", 0)).replace(",","")) if agent_status == "high_risk" else 0.0

    return {
        "score": score,
        "category": category,
        "agent_status": agent_status,
        "mismatches": mismatches,
        "comparison": comparison,
        "capital_at_risk": cap_risk,
        "recommended_action": (
            "block_payment" if agent_status == "high_risk" else
            "request_correction" if agent_status == "minor_flag" else
            "auto_approve"
        ),
    }

# ── WOW Feature: Full AI Agent Pipeline (SSE streaming) ──────────────────────

async def run_pipeline_stream(pdf_bytes: bytes, filename: str):
    """
    Generator that yields SSE events as the agent pipeline runs.
    Each event: data: <json>\n\n
    """
    inv_id = f"INV-{uuid.uuid4().hex[:6].upper()}"

    def event(step: int, status: str, title: str, detail: str, data: dict = None):
        payload = {
            "step": step, "status": status,
            "title": title, "detail": detail,
            **(data or {})
        }
        return f"data: {json.dumps(payload)}\n\n"

    # ── STEP 1: Ingest ───────────────────────────────────────────────────────
    yield event(1, "running", "Step 1 — Ingesting invoice PDF", f"Reading {filename}…")
    time.sleep(0.4)

    raw_text = extract_text_from_pdf(pdf_bytes)
    if not raw_text or len(raw_text) < 20:
        yield event(1, "error", "Step 1 — Ingest failed", "Could not extract text from PDF. Is it a scanned image?")
        return

    yield event(1, "done", "Step 1 — PDF ingested", f"Extracted {len(raw_text)} characters of invoice text.", {"raw_preview": raw_text[:400]})

    # ── STEP 2: AI extraction ────────────────────────────────────────────────
    yield event(2, "running", "Step 2 — Claude extracting invoice fields", "Parsing vendor name, Reg. No., SST rate, amounts, address…")

    if not client:
        yield event(2, "error", "Step 2 — No API key", "Set ANTHROPIC_API_KEY environment variable to enable AI extraction.")
        return

    extraction_prompt = f"""You are a Malaysian e-invoicing compliance parser.
Extract the following fields from this vendor invoice text. Return ONLY valid JSON.

Invoice text:
\"\"\"
{raw_text[:3000]}
\"\"\"

Return this exact JSON (use null if not found):
{{
  "vendor_name": "string",
  "invoice_no": "string",
  "invoice_date": "string",
  "reg_no": "string - company registration number (e.g. 1234567-A)",
  "sst_id": "string - SST registration ID",
  "amount": "string - total amount before SST",
  "sst_rate": "string - e.g. 6% or 0%",
  "sst_amount": "string",
  "total_amount": "string",
  "address": "string - vendor's physical address",
  "email": "string"
}}"""

    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            messages=[{"role":"user","content": extraction_prompt}]
        )
        raw = resp.content[0].text.strip()
        raw = re.sub(r"```json|```","", raw).strip()
        extracted = json.loads(raw)
    except Exception as e:
        yield event(2, "error", "Step 2 — Extraction failed", str(e))
        return

    yield event(2, "done", "Step 2 — Fields extracted by Claude",
        f"Vendor: {extracted.get('vendor_name')} | Reg: {extracted.get('reg_no')} | SST: {extracted.get('sst_rate')} | Amount: RM {extracted.get('amount')}",
        {"extracted": extracted})

    # ── STEP 3: LHDN lookup ──────────────────────────────────────────────────
    yield event(3, "running", "Step 3 — Querying LHDN MyInvois database", f"Looking up Reg. No. {extracted.get('reg_no','?')}…")
    time.sleep(0.5)

    reg_no = extracted.get("reg_no") or "DEMO"
    lhdn = lhdn_lookup(reg_no)

    yield event(3, "done", "Step 3 — LHDN record retrieved",
        f"LHDN entity: {lhdn['legal_name']} | SST class: {lhdn['sst_class']} | Portal status: {lhdn['lhdn_status']}",
        {"lhdn": lhdn})

    # ── STEP 4: Risk scoring ─────────────────────────────────────────────────
    yield event(4, "running", "Step 4 — Running deterministic risk scoring matrix", "Comparing 5 compliance vectors…")
    time.sleep(0.3)

    risk = compute_risk(extracted, lhdn)

    status_label = {"high_risk":"error","minor_flag":"warning","clean":"done"}.get(risk["agent_status"],"done")
    yield event(4, status_label,
        f"Step 4 — Risk scored: {risk['category']} ({risk['score']}/10)",
        " | ".join(risk["mismatches"]) if risk["mismatches"] else "No mismatches found.",
        {"risk": risk})

    # ── STEP 5: AI email draft ───────────────────────────────────────────────
    if risk["agent_status"] != "clean":
        yield event(5, "running", "Step 5 — Drafting bilingual resolution email", "Claude composing English + Bahasa Malaysia notice…")

        email_prompt = f"""You are TaxTrace AI, a compliance engine for Chin Hin Group Bhd Malaysia.
Draft a professional bilingual (English then Bahasa Malaysia) vendor notice email.

Invoice details:
- Vendor: {extracted.get('vendor_name')}
- Invoice No: {extracted.get('invoice_no')}
- Total Amount: RM {extracted.get('total_amount') or extracted.get('amount')}
- Issues found: {', '.join(risk['mismatches'])}
- LHDN registered name: {lhdn['legal_name']}
- SST class should be: {lhdn['sst_class']}

Requirements:
- Professional, factual tone
- Cite exact discrepancies with field-level specifics
- Request corrected e-invoice via MyInvois portal within 3 business days
- Include placeholder [SECURE_UPLOAD_LINK]
- English first, then Bahasa Malaysia summary (3-4 sentences)
- Sign off: TaxTrace AI Compliance Engine / On behalf of Chin Hin Group Bhd Finance Department
- Return ONLY the email body, no subject line, no markdown"""

        try:
            email_resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1200,
                messages=[{"role":"user","content": email_prompt}]
            )
            email_body = email_resp.content[0].text.strip()
        except Exception as e:
            email_body = f"[Email drafting failed: {e}]"

        subject = f"Invoice {extracted.get('invoice_no','?')} — LHDN Compliance Discrepancy Notice / Notis Pematuhan LHDN"
        vendor_slug = (extracted.get("vendor_name","vendor") or "vendor").lower().replace(" ","")[:14]

        yield event(5, "done", "Step 5 — Bilingual email drafted",
            "Ready for Finance Director approval before sending.",
            {"email": {"subject": subject, "to": f"finance@{vendor_slug}.com.my", "cc": "procurement@chinhingroup.com", "body": email_body}})
    else:
        yield event(5, "done", "Step 5 — No email needed", "Invoice is fully compliant. Auto-approving.")

    # ── STEP 6: Save result ──────────────────────────────────────────────────
    new_inv = {
        "id": inv_id,
        "vendor": extracted.get("vendor_name","Unknown"),
        "invoice_no": extracted.get("invoice_no","—"),
        "amount": float(str(extracted.get("amount",0)).replace(",","")),
        "sst_rate": extracted.get("sst_rate","—"),
        "lhdn_status": lhdn.get("lhdn_status","unknown"),
        "agent_status": risk["agent_status"],
        "flag_type": risk["category"] if risk["agent_status"] != "clean" else None,
        "capital_at_risk": risk["capital_at_risk"],
        "risk_score": risk["score"],
        "date": datetime.now().strftime("%Y-%m-%d"),
        "status": "blocked" if risk["agent_status"] == "high_risk" else "pending_review" if risk["agent_status"] == "minor_flag" else "approved",
    }
    INVOICES.insert(0, new_inv)

    DISCREPANCIES[inv_id] = {
        "invoice_id": inv_id,
        "vendor": extracted.get("vendor_name"),
        "invoice_no": extracted.get("invoice_no"),
        "amount": float(str(extracted.get("amount",0)).replace(",","")),
        "risk_score": risk["score"],
        "risk_category": risk["category"],
        "capital_at_risk": risk["capital_at_risk"],
        "comparison": risk["comparison"],
        "reasoning_steps": [
            {"status":"ok","title":"Step 1 — PDF ingested","detail":f"Extracted {len(raw_text)} chars from {filename}"},
            {"status":"ok","title":"Step 2 — Claude field extraction","detail":f"Vendor: {extracted.get('vendor_name')} | SST: {extracted.get('sst_rate')} | Amount: {extracted.get('amount')}"},
            {"status":"ok","title":"Step 3 — LHDN lookup","detail":f"Matched Reg. {reg_no} → {lhdn['legal_name']} ({lhdn['sst_class']})"},
            *[{"status":"error","title":f"Mismatch — {m.split(':')[0]}","detail":m} for m in risk["mismatches"]],
        ],
    }

    log("Pipeline","new upload","Full AI pipeline completed", risk["agent_status"], f"{risk['category']} — Score {risk['score']}")

    yield event(6, "complete", "Pipeline complete ✓",
        f"Invoice {inv_id} processed. Risk: {risk['category']} ({risk['score']}/10). Status: {new_inv['status']}",
        {"invoice_id": inv_id, "summary": risk})


# ── REST endpoints ────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "api_key_set": bool(ANTHROPIC_KEY), "version": "2.0.0"}

@app.get("/api/dashboard")
def get_dashboard():
    total   = len(INVOICES)
    flagged = sum(1 for i in INVOICES if i["agent_status"] != "clean")
    high    = sum(1 for i in INVOICES if i["agent_status"] == "high_risk")
    capital = sum(i["capital_at_risk"] for i in INVOICES)
    return {
        "invoices_today": total,
        "flags_raised": flagged,
        "high_risk": high,
        "capital_at_risk": round(capital, 2),
        "compliance_rate": round(((total - flagged) / total) * 100, 1) if total else 0,
        "agent_status": "running",
        "last_run": "live",
        "weekly_trend": [
            {"week":"W1","clean":78,"minor":14,"high_risk":8},
            {"week":"W2","clean":82,"minor":11,"high_risk":7},
            {"week":"W3","clean":79,"minor":15,"high_risk":6},
            {"week":"W4","clean":85,"minor":10,"high_risk":5},
            {"week":"W5","clean":88,"minor":9,"high_risk":6},
            {"week":"W6","clean":total-flagged,"minor":flagged-high,"high_risk":high},
        ],
        "discrepancy_types":[
            {"type":"SST rate error","count":38},{"type":"Entity name","count":27},
            {"type":"Tax code","count":18},{"type":"Rounding","count":12},{"type":"Other","count":5},
        ],
        "top_vendors_at_risk":[
            {"vendor":"Matahari Trading","amount":128000,"level":"high"},
            {"vendor":"Buildcon Sdn Bhd","amount":82400,"level":"high"},
            {"vendor":"Apex Roofing","amount":61700,"level":"high"},
            {"vendor":"K&F Supplies","amount":34500,"level":"minor"},
            {"vendor":"Prime Const.","amount":12000,"level":"minor"},
            {"vendor":"Synergy Elec.","amount":9500,"level":"minor"},
            {"vendor":"SteelMax Plt","amount":1200,"level":"minor"},
            {"vendor":"Reka Jaya Plt","amount":800,"level":"minor"},
        ],
    }

@app.get("/api/invoices")
def list_invoices():
    return {"invoices": INVOICES, "total": len(INVOICES)}

@app.get("/api/invoices/{inv_id}")
def get_invoice(inv_id: str):
    inv = next((i for i in INVOICES if i["id"] == inv_id), None)
    if not inv: raise HTTPException(404, "Not found")
    return {**inv, "detail": DISCREPANCIES.get(inv_id, {})}

@app.post("/api/invoices/{inv_id}/action")
def invoice_action(inv_id: str, payload: dict):
    inv = next((i for i in INVOICES if i["id"] == inv_id), None)
    if not inv: raise HTTPException(404, "Not found")
    action = payload.get("action")
    if action not in ["approve","hold","send_comms"]: raise HTTPException(400, "Invalid action")
    inv["status"] = {"approve":"approved","hold":"blocked","send_comms":"pending_review"}[action]
    log("Human", inv["invoice_no"], f"Finance officer: {action}", "ok", f"Status → {inv['status']}")
    return {"success": True, "new_status": inv["status"]}

@app.get("/api/discrepancies")
def list_discrepancies():
    flagged = [i for i in INVOICES if i["agent_status"] != "clean"]
    return {"discrepancies": flagged, "total": len(flagged)}

@app.get("/api/discrepancies/{inv_id}")
def get_discrepancy(inv_id: str):
    d = DISCREPANCIES.get(inv_id)
    if not d: raise HTTPException(404, "Not found")
    return d

@app.get("/api/analytics")
def get_analytics():
    return {
        "compliance_rate_mtd": 84.3,
        "avg_resolution_days": 1.8,
        "sst_recovered": 91400,
        "lhdn_rejections_avoided": 38,
        "monthly_trend":[
            {"month":"Jan","rate":76.2},{"month":"Feb","rate":78.5},
            {"month":"Mar","rate":80.1},{"month":"Apr","rate":81.4},
            {"month":"May","rate":83.0},{"month":"Jun","rate":84.3},
        ],
    }

@app.get("/api/audit-log")
def get_audit_log():
    return {"logs": AUDIT_LOG, "total": len(AUDIT_LOG)}

@app.get("/api/comms")
def get_comms():
    return {"history":[
        {"date":"2026-06-23","invoice":"MT-2026-0891","vendor":"Matahari Trading Sdn Bhd","type":"Ghost supplier","sent":True,"response":"pending"},
        {"date":"2026-06-22","invoice":"BC-2026-1122","vendor":"Buildcon Sdn Bhd","type":"Entity mismatch","sent":True,"response":"awaiting"},
        {"date":"2026-06-20","invoice":"AR-2026-0077","vendor":"Apex Roofing Plt","type":"SST rate","sent":True,"response":"resolved"},
        {"date":"2026-06-19","invoice":"KF-2026-3201","vendor":"K&F Supplies Bhd","type":"Tax code","sent":True,"response":"resolved"},
    ]}

@app.post("/api/draft-email")
async def draft_email(payload: dict):
    if not client: raise HTTPException(503, "ANTHROPIC_API_KEY not set")
    vendor   = payload.get("vendor","Vendor")
    inv_no   = payload.get("invoice_no","INV-XXX")
    amount   = payload.get("amount", 0)
    issues   = payload.get("issues", ["Compliance discrepancy"])
    prompt = f"""Draft a professional bilingual (English then Bahasa Malaysia) compliance notice email.
Vendor: {vendor} | Invoice: {inv_no} | Amount: RM {amount:,.2f}
Issues: {', '.join(issues)}
Sender: Chin Hin Group Bhd Finance Department (TaxTrace AI)
Request corrected e-invoice via MyInvois within 3 business days.
Include placeholder [SECURE_UPLOAD_LINK]. Return email body only."""
    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=1000, messages=[{"role":"user","content":prompt}])
    body = resp.content[0].text.strip()
    log("Comms", inv_no, "Resolution email drafted via API", "ok", "Draft ready")
    return {"subject":f"Invoice {inv_no} — Compliance Discrepancy / Notis Pematuhan","to":f"finance@{vendor[:10].lower().replace(' ','')}.com.my","cc":"procurement@chinhingroup.com","body":body}

@app.post("/api/analyze")
async def analyze_invoice(payload: dict):
    """Structured AI analysis for the live analyzer page."""
    if not client: raise HTTPException(503, "ANTHROPIC_API_KEY not set")
    prompt = f"""You are TaxTrace AI. Analyze this invoice cross-validation and return JSON risk assessment.
PDF entity: {payload.get('pdf_entity')} | LHDN entity: {payload.get('lhdn_entity')}
PDF SST: {payload.get('pdf_sst_rate')} | LHDN SST: {payload.get('lhdn_sst_rate')}
Amount: RM {payload.get('amount',0):,.2f} | Address verified: {payload.get('address_verified')}

Return ONLY JSON:
{{"risk_score":<0-10>,"risk_category":"<category>","capital_at_risk":<RM>,"agent_status":"<clean|minor_flag|high_risk>","summary":"<2 sentences>","recommended_action":"<action>","reasoning":["step1","step2","step3"]}}"""
    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=800, messages=[{"role":"user","content":prompt}])
    text = re.sub(r"```json|```","", resp.content[0].text).strip()
    result = json.loads(text)
    log("AI Analyzer", payload.get("invoice_no","manual"), "AI risk analysis", result.get("agent_status","ok"), f"{result.get('risk_category')} — {result.get('risk_score')}/10")
    return result

# ── WOW FEATURE endpoint: Upload PDF → stream SSE pipeline ───────────────────

@app.post("/api/upload-invoice")
async def upload_invoice(file: UploadFile = File(...)):
    """
    THE WOW FEATURE.
    POST a vendor invoice PDF → returns SSE stream of the full AI agent pipeline.
    Each event is a JSON object describing the current pipeline step.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")
    pdf_bytes = await file.read()
    if len(pdf_bytes) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 10 MB)")

    return StreamingResponse(
        run_pipeline_stream(pdf_bytes, file.filename),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )

# ── Serve the frontend HTML directly ─────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        with open(html_path) as f:
            return f.read()
    return HTMLResponse("<h1>TaxTrace AI API running. Place index.html alongside server.py.</h1>")

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*55)
    print("  TaxTrace AI — Backend Server v2.0")
    print("="*55)
    if not ANTHROPIC_KEY:
        print("  ⚠  ANTHROPIC_API_KEY not set — AI features disabled")
        print("     Set it: export ANTHROPIC_API_KEY=sk-ant-...")
    else:
        print("  ✓  Anthropic API key detected")
    print("  ✓  Server starting at http://localhost:8000")
    print("  ✓  Open http://localhost:8000 in your browser")
    print("="*55 + "\n")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)