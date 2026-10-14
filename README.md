# FraudShield

AI-powered fraud detection system for Text, URLs, Images & QR codes with React frontend and Flask API backend.

## Project Structure

```
Fraud_Model/
├── backend/                  # Flask REST API backend (port 5000)
│   ├── app.py                # Main Flask API endpoints
│   ├── config.py             # App configuration & risk thresholds
│   ├── requirements.txt      # Python dependencies
│   ├── .env                  # Your 4 Gemini API keys
│   ├── models/               # 4 AI detection models
│   │   ├── __init__.py
│   │   ├── text_analyzer.py  # Model 01: Text & social messages
│   │   ├── url_analyzer.py   # Model 02: URLs & web links
│   │   ├── image_analyzer.py # Model 03: Images & documents
│   │   └── qr_analyzer.py    # Model 04: QR codes
│   └── utils/                # Backend utilities
│       ├── __init__.py
│       ├── database.py       # SQLite database & record storage
│       ├── pdf_generator.py  # Branded PDF report export
│       └── risk_scorer.py    # Risk level & verdict calculations
│
└── frontend/                 # React (Vite) single-page app (port 3000)
    ├── vite.config.js        # Vite config with API proxy to port 5000
    ├── package.json          # Node dependencies
    └── src/
        ├── App.jsx           # App routes & layout
        ├── index.css         # Dark theme & bento grid styling
        ├── api/client.js     # Axios API client
        ├── context/          # Toast notification provider
        ├── components/       # Navbar, LoadingOverlay, RiskGauge, FileDropZone
        └── pages/            # LandingPage, AnalyzePage, ResultsPage, HistoryPage
```

---

## Getting Started

### 1. Set Your Gemini API Keys

Edit `backend/.env` with your 4 Gemini API keys:

```env
TEXT_ANALYZER_API_KEY=your_gemini_api_key_1
URL_ANALYZER_API_KEY=your_gemini_api_key_2
IMAGE_ANALYZER_API_KEY=your_gemini_api_key_3
QR_ANALYZER_API_KEY=your_gemini_api_key_4
SECRET_KEY=fraudshield-super-secret-key-change-in-production
DEBUG=True
```

### 2. Install Dependencies

**Backend (Python):**
```powershell
cd e:\Fraud_Model\backend
pip install -r requirements.txt
```

**Frontend (React/Node):**
```powershell
cd e:\Fraud_Model\frontend
npm install
```

### 3. Run the Application

**Terminal 1 — Flask API (port 5000):**
```powershell
cd e:\Fraud_Model\backend
python app.py
```

**Terminal 2 — React Dev Server (port 3000):**
```powershell
cd e:\Fraud_Model\frontend
npm run dev
```

Visit **http://localhost:3000** in your browser.

---

## API Endpoints (`/api/*`)

| Endpoint | Method | Input | Description |
|---|---|---|---|
| `/api/analyze/text` | `POST` | JSON `{ message }` | Analyzes text / social media messages |
| `/api/analyze/url` | `POST` | JSON `{ url }` | Analyzes URLs for phishing & threats |
| `/api/analyze/image` | `POST` | Multipart `file` | Analyzes images & documents via Vision AI |
| `/api/analyze/qr` | `POST` | Multipart `file` | Decodes & analyzes QR codes |
| `/api/analysis/<id>` | `GET` | — | Retrieves full analysis by ID |
| `/api/history` | `GET` | — | Lists past analysis records & stats |
| `/api/stats` | `GET` | — | Summary statistics (fraud vs clean) |
| `/api/report/<id>` | `GET` | — | Generates & downloads PDF report |
