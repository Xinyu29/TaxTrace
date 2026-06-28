# TaxTrace · AI Invoice Compliance Audit System

> Built for **NexHack 2026 - Track 2: Fintech Risk & Fraud Intelligence**

> ⚡ *Turn invoices into intelligence — detect financial risk before it becomes loss.*

---

## Pitch Deck

The complete pitch deck for TaxTrace is available here:

📄 [TaxTrace Pitch Deck](https://github.com/Xinyu29/TaxTrace/blob/main/TaxTrace_PitchDeck-NexHack2026.pdf)

---

## About TaxTrace

TaxTrace is an AI-powered invoice compliance audit system designed to automate financial document verification and reduce tax compliance risks for businesses. The system uses AI agents to analyse invoices, compare supplier documents against LHDN MyInvois records, detect discrepancies, and provide intelligent risk assessments.

Built for Malaysian businesses, TaxTrace combines AI invoice extraction, automated SST validation, vendor verification, risk scoring, audit tracking, and AI-generated resolution communication — helping finance teams identify potential compliance issues before payments are processed.

---

## Key Features

* 🧾 **AI Invoice Processing Pipeline** — Upload invoice PDFs and automatically extract important financial information using AI-powered document analysis
* 🔍 **LHDN Compliance Verification** — Compare invoice details with expected tax information including SST rates, vendor details, and registration information
* ⚠️ **AI Risk Assessment Engine** — Automatically calculate invoice risk scores and classify invoices into clean, minor flag, or high-risk categories
* 📊 **Compliance Analytics Dashboard** — Real-time monitoring of invoice volume, flagged cases, capital at risk, compliance rate, and financial insights
* 🤖 **AI Agent Reasoning Chain** — Provides explainable AI decisions by showing verification steps, detected issues, and audit reasoning
* 📧 **AI Vendor Communication Assistant** — Generates professional resolution emails for invoice discrepancies and compliance issues
* 📝 **Audit Trail System** — Records AI actions, user decisions, invoice reviews, and compliance activities for transparency
* ☁️ **Cloud-Ready Backend Architecture** — Flask-based API backend with structured database models and modular service design

---

## Project Structure

```
TaxTrace/
├── backend/
│   ├── app.py                 # Flask application entry point
│   ├── config.py              # Environment and application configuration
│   ├── models.py              # Database models
│   ├── routes/
│   │   ├── dashboard.py       # Dashboard API endpoints
│   │   ├── invoices.py        # Invoice management APIs
│   │   ├── discrepancies.py   # Risk and discrepancy APIs
│   │   ├── analytics.py       # Analytics APIs
│   │   ├── audit.py           # Audit log APIs
│   │   ├── comms.py           # Communication APIs
│   │   └── upload.py          # Invoice upload pipeline
│   ├── services/
│   │   ├── ai_engine.py
│   │   ├── lhdn_validator.py
│   │   ├── risk_scorer.py
│   └── requirements.txt
├── frontend/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── index.html     
├── .env                       # API keys and environment variables
├── README.md
└── .gitignore
```

---

## Tech Stack

| Layer | Tools |
|---|---|
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Backend | Python Flask REST API |
| AI Engine | Google Gemini |
| Database | SQLite / SQLAlchemy ORM |
| Compliance | LHDN MyInvois e-Invoice validation workflow |
| API Communication | REST API + Fetch API |
| Development | Python Virtual Environment |

---

## Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js (optional for frontend development)**
- A **Google Gemini API key** or **Anthropic API key**
- Git installed

---

## 1. Clone the repository

```bash
git clone https://github.com/Xinyu29/TaxTrace.git
cd TaxTrace
```

---

## 2. Backend Setup

Navigate to backend folder:

```bash
cd backend
```

Create virtual environment:

```bash
python -m venv venv
```

Activate virtual environment:

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 3. Configure Environment Variables

Create a `.env` file inside the backend folder:

```env
GEMINI_API_KEY=your_api_key_here

DATABASE_URL=sqlite:///taxtrace.db

CORS_ORIGINS=http://127.0.0.1:3000
```

---

## 4. Run Backend Server

Start Flask backend:

```bash
python app.py
```

Backend runs at:

```
http://localhost:5000
```

---

## 5. Run Frontend

Open the frontend folder:

```bash
cd frontend
```

Run using Live Server or any static web server.

Frontend runs at:

```
http://127.0.0.1:3000
```
---

## 6. Test the AI Invoice Pipeline

To experience the full AI invoice analysis workflow, use the provided:

📄 **sample_invoice.pdf**

### How to test:
1. Open the **Upload & Analyse** page in the frontend
2. Upload the file: `sample_invoice.pdf`
3. The system will automatically:
   - Extract invoice data using AI
   - Run LHDN compliance validation
   - Generate risk score
   - Detect discrepancies
   - Produce AI reasoning + audit trail
   - Draft vendor communication email (if applicable)

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `/api/dashboard` | Retrieve compliance dashboard information |
| `/api/invoices` | Retrieve invoice processing queue |
| `/api/discrepancies` | Retrieve detected invoice discrepancies |
| `/api/analytics` | Retrieve compliance analytics data |
| `/api/audit-log` | Retrieve AI audit records |
| `/api/comms` | Retrieve communication history |
| `/api/upload-invoice` | Upload and analyse invoice PDF |
| `/api/health` | Backend health status check |

---

## AI Features

| AI Function | Purpose |
|---|---|
| **Invoice Extraction AI** | Extract vendor details, invoice numbers, amounts, SST rates, and registration information from invoice documents |
| **Compliance Risk AI** | Analyse invoice information and identify possible compliance issues |
| **AI Reasoning Agent** | Provide transparent reasoning steps behind risk classifications |
| **Communication AI** | Generate professional vendor resolution emails automatically |
| **Risk Analysis Engine** | Estimate financial exposure and identify high-risk invoices |

---

## AI Tools Used

> All AI tools used in this project are listed here.

| Tool | Purpose |
|---|---|
| **Google Gemini** | AI-powered invoice analysis, document understanding, compliance checking, risk assessment, and recommendations |
| **Claude (Anthropic)** | Used during development for code generation, debugging, architecture planning, and implementation assistance |

All AI-generated code and suggestions were reviewed, tested, and modified by the team. The team understands the system architecture, backend API flow, frontend integration, database structure, and implemented logic.

---

## Security Considerations

* 🔐 **Environment Protection** — API keys and sensitive configurations are stored using environment variables
* 🛡️ **CORS Security** — Controlled frontend-backend communication through configured CORS settings
* 📝 **Audit Transparency** — AI actions and user decisions are recorded for tracking and review
* 🔒 **Data Protection** — Sensitive files and configuration data are excluded using `.gitignore`

---

## Future Improvements

* Integration with live LHDN MyInvois API
* Advanced OCR support for complex invoice formats
* Multi-company account management
* Automated payment approval workflow
* AI fraud detection using historical invoice patterns
* Cloud deployment with scalable infrastructure

---

## License

This project was developed for educational, innovation, and hackathon purposes.