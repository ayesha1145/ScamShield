# 🛡️ ScamShield

**AI-powered scam detection for SMS messages, URLs, and phone numbers.**

ScamShield uses a three-layer hybrid detection engine to identify scams in real time — combining rule-based pattern matching, a blacklist database, and a machine learning model trained on 5,574 real SMS messages with 97.2% accuracy.

**[Live Demo →](https://scam-shield-beta.vercel.app)**

---

## Why ScamShield

Scam messages targeting students and newcomers are increasingly sophisticated. Existing tools require apps or subscriptions. ScamShield is free, instant, and works on any device — paste a message and get a risk score in under 200ms.

---

## Features

- **Three-layer detection** — rules + blacklist + ML, combined into a single risk score (0–100)
- **Auto-detection** — automatically identifies whether input is a text message, URL, or phone number
- **Scan history** — stores and retrieves the last 10 scans per session
- **Live statistics** — tracks total scans, safe/suspicious/dangerous breakdown
- **97.2% accuracy** — ML model trained on the UCI SMS Spam Collection dataset (5,574 messages)

---

## Architecture

```
User Input
    │
    ▼
┌─────────────────────────────────────┐
│           FastAPI Backend           │
│                                     │
│  ┌──────────┐  ┌────────────────┐  │
│  │  Rule    │  │   Blacklist    │  │
│  │ Engine   │  │   Database     │  │
│  │ (regex)  │  │  (MongoDB)     │  │
│  └────┬─────┘  └───────┬────────┘  │
│       │                │            │
│       ▼                ▼            │
│  ┌─────────────────────────────┐   │
│  │     ML Model (sklearn)      │   │
│  │  TF-IDF + Logistic Regression│  │
│  │  Trained: 5,574 SMS messages│   │
│  └─────────────┬───────────────┘   │
│                │                    │
│         Risk Score (0–100)          │
└─────────────────────────────────────┘
    │
    ▼
React Frontend (Vercel)
```

**Detection layers:**
| Layer | Method | Max Score |
|---|---|---|
| Rule Engine | Regex patterns (urgency, lottery, authority, etc.) | 70 |
| Blacklist | MongoDB lookup of known scam domains/numbers/phrases | 50 |
| AI Layer | TF-IDF vectorizer + Logistic Regression | 40 |

Final score = sum of all layers, capped at 100.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.11 |
| Database | MongoDB Atlas (Motor async driver) |
| ML | scikit-learn (TF-IDF + Logistic Regression) |
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
| POST | `/api/scan` | Scan a message, URL, or phone number |
| GET | `/api/history` | Retrieve last 10 scan results |
| GET | `/api/stats` | Get aggregate scan statistics |
| GET | `/api/health` | Health check + model status |

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
  "triggers": ["Rule: urgency", "AI: suspicious_language_patterns"],
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

## Author

**Ayesha Habib** — University of Manitoba
