# 🛡️ ScamShield

**AI-powered scam detection for SMS messages, URLs, phone numbers, emails, and files.**

ScamShield uses a four-layer hybrid detection engine to identify scams in real time — combining rule-based pattern matching, a blacklist database, a machine learning model trained on 5,574 real SMS messages, and Azure AI Language sentiment analysis.

**[Live Demo →](https://scam-shield-beta.vercel.app)**

---

## Why ScamShield

Scam messages targeting students and newcomers are increasingly sophisticated. Existing tools require apps or subscriptions. ScamShield is free, instant, and works on any device — paste a message, URL, email, or upload a file and get a risk score in under 200ms.

---

## Features

- **Four-layer detection** — rules + blacklist + ML + Azure AI, combined into a single risk score (0–100)
- **Five scan types** — SMS/text, URL, phone number, email, and file upload (.txt, .eml, .csv, .msg, .pdf)
- **PDF support** — upload and scan PDF documents for scam content
- **Scam explanations** — human-readable explanation of why content was flagged
- **Auto-detection** — automatically identifies whether input is a message, URL, or phone number
- **Scan history** — stores and retrieves the last 10 scans
- **Live statistics** — tracks total scans, safe/suspicious/dangerous breakdown
- **97.2% ML accuracy** — model trained on the UCI SMS Spam Collection dataset (5,574 messages)
- **Azure AI Language** — Layer 4 uses sentiment analysis to detect threatening tone

---

## Architecture

```
User Input (text / URL / phone / email / file)
    │
    ▼
┌──────────────────────────────────────────────┐
│              FastAPI Backend                 │
│                                              │
│  ┌──────────┐  ┌────────────┐               │
│  │  Rule    │  │ Blacklist  │               │
│  │ Engine   │  │ (MongoDB)  │               │
│  │ (regex)  │  │            │               │
│  └────┬─────┘  └─────┬──────┘               │
│       │               │                      │
│       ▼               ▼                      │
│  ┌──────────────────────────────────────┐   │
│  │        ML Model (scikit-learn)       │   │
│  │   TF-IDF + Logistic Regression       │   │
│  │   Trained: 5,574 SMS messages        │   │
│  └──────────────────┬───────────────────┘   │
│                     │                        │
│                     ▼                        │
│  ┌──────────────────────────────────────┐   │
│  │        Azure AI Language             │   │
│  │   Sentiment Analysis (Layer 4)       │   │
│  │   Detects threatening tone & intent  │   │
│  └──────────────────┬───────────────────┘   │
│                     │                        │
│              Risk Score (0–100)              │
└──────────────────────────────────────────────┘
    │
    ▼
React Frontend (Vercel)
```

**Detection layers:**
| Layer | Method | Max Score |
|---|---|---|
| Rule Engine | Regex patterns across 7 scam categories | 70 |
| Blacklist | MongoDB lookup of known scam domains/numbers/phrases | 50 |
| ML Layer | TF-IDF vectorizer + Logistic Regression | 40 |
| Azure AI | Sentiment analysis — threatening tone detection | 30 |

Final score = sum of all layers, capped at 100.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.11 |
| Database | MongoDB Atlas (Motor async driver) |
| ML | scikit-learn (TF-IDF + Logistic Regression) |
| Cloud AI | Azure AI Language (sentiment analysis) |
| File Processing | PyPDF2 (PDF text extraction) |
| Frontend | React, React Router |
| Backend Deploy | Render |
| Frontend Deploy | Vercel |

---

## Local Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:
```
MONGO_URL=your_mongodb_connection_string
DB_NAME=scamshield
AZURE_LANGUAGE_KEY=your_azure_key
AZURE_LANGUAGE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
```

```bash
uvicorn server:app --reload
```

### Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env`:
```
REACT_APP_API_BASE_URL=http://localhost:8000/api
```

```bash
npm start
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/scan` | Scan text, URL, phone, or email content |
| POST | `/api/scan/file` | Scan an uploaded file (.txt, .eml, .csv, .msg, .pdf) |
| GET | `/api/history` | Retrieve last 10 scan results |
| GET | `/api/stats` | Get aggregate scan statistics |
| GET | `/api/health` | Health check + model and Azure status |

### Example request

```bash
curl -X POST https://scamshield-fi4v.onrender.com/api/scan \
  -H "Content-Type: application/json" \
  -d '{"content": "URGENT: Your account will be suspended in 24 hours!"}'
```

### Example response

```json
{
  "id": "abc123",
  "content": "URGENT: Your account will be suspended in 24 hours!",
  "scan_type": "text",
  "risk_score": 85,
  "label": "🔴 Dangerous",
  "guidance": "This content is highly likely to be a scam.",
  "explanation": "Uses urgency tactics to pressure you into acting without thinking.",
  "triggers": ["Rule: urgency", "AI: suspicious_language_patterns", "Azure: high_negative_sentiment"],
  "timestamp": "2026-01-01T00:00:00Z"
}
```

---

## ML Model Details

- **Dataset:** UCI SMS Spam Collection (5,574 messages — 747 spam, 4,827 ham)
- **Vectorizer:** TF-IDF (3,000 features, English stopwords removed)
- **Classifier:** Logistic Regression
- **Train/test split:** 80/20
- **Test accuracy:** 97.22%
- **Model persistence:** Saved to disk on first run, loaded on subsequent restarts

---

## Azure AI Integration

ScamShield uses **Azure AI Language** as a fourth detection layer:
- **Service:** Azure AI Language (Text Analytics)
- **Feature:** Sentiment Analysis with opinion mining
- **Logic:** High negative sentiment (>70%) adds up to 30 points to the risk score
- **Pricing tier:** F0 (Free — 5,000 transactions/month)

This integration demonstrates Microsoft Azure ecosystem experience and adds a cloud AI signal on top of the local ML model.

---

## Author

**Ayesha Habib** — University of Manitoba  
[GitHub](https://github.com/ayesha1145) | [Live Demo](https://scam-shield-beta.vercel.app)
