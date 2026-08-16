# ======================================================
# ScamShield Backend – Server
# ------------------------------------------------------
# Author: Ayesha Habib
# Description:
#   Main FastAPI application that handles scam detection,
#   database connections, and API endpoints.
#   ML model trained on 5,574 real SMS messages from the
#   UCI SMS Spam Collection dataset.
#   Supports: text, URL, phone, email, and file uploads.
#   Layer 4: Azure AI Language sentiment + entity analysis.
# ======================================================

from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import io
import logging
import pickle
import re
import uuid
import urllib.request
import httpx
import numpy as np
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Azure AI Language credentials
AZURE_LANGUAGE_KEY = os.environ.get('AZURE_LANGUAGE_KEY', '')
AZURE_LANGUAGE_ENDPOINT = os.environ.get('AZURE_LANGUAGE_ENDPOINT', '')

# Paths for saving the trained model
MODEL_PATH = ROOT_DIR / "ml_model.pkl"
VECTORIZER_PATH = ROOT_DIR / "vectorizer.pkl"

# Create the main app
app = FastAPI(title="ScamShield API", description="Hybrid fraud detection system with Azure AI")
api_router = APIRouter(prefix="/api")

# Global ML model variables
ml_model = None
vectorizer = None

# ======================================================
# Pydantic Models
# ======================================================

class ScanRequest(BaseModel):
    content: str
    scan_type: Optional[str] = None

class ScanResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    scan_type: str
    risk_score: int
    label: str
    guidance: str
    triggers: List[str]
    explanation: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HistoryItem(BaseModel):
    id: str
    content: str
    scan_type: str
    risk_score: int
    label: str
    guidance: str
    triggers: List[str]
    explanation: str = ""
    timestamp: datetime

# ======================================================
# Rule-based Detection Patterns
# ======================================================

SCAM_PATTERNS = {
    'urgency': [
        r'urgent|immediate|expire|expires|within \d+ hours?',
        r'act now|limited time|hurry|final notice',
        r'suspend|blocked|frozen|terminate',
    ],
    'lottery': [
        r'congratulations|winner|won.*prize|lottery|jackpot',
        r'claim.*\$[\d,]+|claim.*prize|claim.*reward',
        r'inheritance|beneficiary|million dollars?',
        r'you.*won.*\$|selected.*winner',
    ],
    'otp_phishing': [
        r'verification code|otp|one.time.password',
        r'code.*\d{4,6}|pin.*\d{4,6}',
        r'authenticate|verify.*account',
    ],
    'financial': [
        r'bank.*details|credit.*card|account.*number',
        r'ssn|social.*security|tax.*refund',
        r'bitcoin|crypto|investment.*opportunity',
    ],
    'authority': [
        r'irs|fbi|police|government|court',
        r'legal.*action|warrant|arrest',
        r'immigration|deportation|fine',
    ],
    'suspicious_links': [
        r'bit\.ly|tinyurl|t\.co|goo\.gl',
        r'click.*here|download.*now|open.*link',
    ],
    'email_phishing': [
        r'dear (customer|user|account holder|valued member)',
        r'your account has been|we have detected|unusual activity',
        r'confirm your (identity|account|email|password|details)',
        r'update your (billing|payment|account) information',
        r'your (password|account) (will expire|has been compromised)',
        r'click the link below|follow the link|access your account',
    ],
}

EXPLANATION_MAP = {
    'urgency': 'Uses urgency tactics to pressure you into acting without thinking.',
    'lottery': 'Claims you won a prize or lottery you never entered — a classic scam.',
    'otp_phishing': 'Asks for verification codes or PINs — legitimate services never do this.',
    'financial': 'Requests sensitive financial information like bank details or SSN.',
    'authority': 'Impersonates government or law enforcement to create fear.',
    'suspicious_links': 'Contains shortened or suspicious links that hide the real destination.',
    'email_phishing': 'Uses phishing language common in fake emails impersonating banks or services.',
    'azure': 'Azure AI Language detected negative sentiment and suspicious entity patterns.',
}

# ======================================================
# Detection Helpers
# ======================================================

def detect_input_type(content: str) -> str:
    content = content.strip()
    phone_pattern = r'^[\+]?[1-9]?[\-\.\s]?\(?[0-9]{3}\)?[\-\.\s]?[0-9]{3}[\-\.\s]?[0-9]{4,6}$'
    if re.match(phone_pattern, content) or content.replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
        return 'phone'
    url_pattern = r'^https?://|^www\.|\.com$|\.org$|\.net$'
    if re.search(url_pattern, content, re.IGNORECASE):
        return 'url'
    email_patterns = [
        r'subject:|from:|to:|dear (customer|user|sir|madam)',
        r'unsubscribe|click here to|your account|sincerely|regards',
    ]
    if any(re.search(p, content.lower()) for p in email_patterns):
        return 'email'
    return 'text'

def apply_rule_layer(content: str, scan_type: str) -> tuple:
    score = 0
    triggers = []
    content_lower = content.lower()

    for category, patterns in SCAM_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, content_lower):
                if category in ['urgency', 'authority']:
                    score += 30
                elif category in ['lottery', 'financial']:
                    score += 35
                elif category in ['otp_phishing', 'suspicious_links']:
                    score += 25
                elif category == 'email_phishing':
                    score += 30
                triggers.append(f"Rule: {category}")
                break

    if scan_type == 'phone':
        scam_number_patterns = [
            r'^(000|111|222|333|444|666|777|888|999)[-\s]?\d{3}[-\s]?\d{4}$',
            r'^\+1[-\s]?900[-\s]?\d{3}[-\s]?\d{4}$',
            r'^\d{4,6}$',
            r'^\d{11,}$',
        ]
        for pattern in scam_number_patterns:
            if re.search(pattern, content.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')):
                score += 20
                triggers.append("Rule: suspicious_number_pattern")
                break

    elif scan_type == 'url':
        content_clean = content.lower().strip()
        suspicious_url_patterns = [
            r'^https?://[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}',
            r'[a-z0-9]{20,}\.',
            r'[0-9]{10,}\.',
        ]
        legitimate_domains = ['google.com', 'microsoft.com', 'apple.com', 'amazon.com',
                              'facebook.com', 'youtube.com', 'wikipedia.org', 'github.com']
        is_legitimate = any(domain in content_clean for domain in legitimate_domains)
        if not is_legitimate:
            for pattern in suspicious_url_patterns:
                if re.search(pattern, content_clean):
                    score += 25
                    triggers.append("Rule: suspicious_url_pattern")
                    break

    return min(score, 70), triggers

async def apply_blacklist_layer(content: str, scan_type: str) -> tuple:
    score = 0
    triggers = []
    try:
        if scan_type == 'phone':
            blocked = await db.blocked_numbers.find_one({"number": content})
            if blocked:
                score += 50
                triggers.append("Blacklist: known_scam_number")
        elif scan_type == 'url':
            domain_match = re.search(r'://([^/]+)', content)
            if domain_match:
                domain = domain_match.group(1).lower()
                legitimate_domains = [
                    'google.com', 'microsoft.com', 'apple.com', 'amazon.com',
                    'facebook.com', 'youtube.com', 'wikipedia.org', 'github.com',
                    'linkedin.com', 'twitter.com', 'instagram.com', 'reddit.com'
                ]
                is_legitimate = any(legit_domain in domain for legit_domain in legitimate_domains)
                if not is_legitimate:
                    blocked = await db.blocked_domains.find_one({"domain": domain})
                    if blocked:
                        score += 50
                        triggers.append("Blacklist: known_scam_domain")
        else:
            blocked_messages = await db.blocked_messages.find().to_list(100)
            for blocked_msg in blocked_messages:
                if blocked_msg['pattern'].lower() in content.lower():
                    score += 50
                    triggers.append("Blacklist: known_scam_message")
                    break
    except Exception as e:
        logging.error(f"Blacklist check error: {e}")
    return score, triggers

def apply_ai_layer(content: str) -> tuple:
    global ml_model, vectorizer
    if ml_model is None or vectorizer is None:
        return 0, []
    try:
        content_vector = vectorizer.transform([content])
        proba = ml_model.predict_proba(content_vector)[0]
        scam_probability = proba[1] if len(proba) > 1 else 0
        ai_score = int(scam_probability * 40)
        triggers = []
        if ai_score > 20:
            triggers.append("AI: suspicious_language_patterns")
        return ai_score, triggers
    except Exception as e:
        logging.error(f"AI layer error: {e}")
        return 0, []

async def apply_azure_layer(content: str) -> tuple:
    """
    Layer 4: Azure AI Language
    Uses sentiment analysis to detect negative/threatening tone
    and key phrase extraction to identify scam-related entities.
    """
    if not AZURE_LANGUAGE_KEY or not AZURE_LANGUAGE_ENDPOINT:
        return 0, []

    score = 0
    triggers = []

    try:
        url = f"{AZURE_LANGUAGE_ENDPOINT}language/:analyze-text?api-version=2023-04-01"
        headers = {
            "Ocp-Apim-Subscription-Key": AZURE_LANGUAGE_KEY,
            "Content-Type": "application/json"
        }

        # Truncate content to 5000 chars (Azure limit)
        content_truncated = content[:5000]

        payload = {
            "kind": "SentimentAnalysis",
            "parameters": {
                "modelVersion": "latest",
                "opinionMining": True
            },
            "analysisInput": {
                "documents": [
                    {"id": "1", "language": "en", "text": content_truncated}
                ]
            }
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            data = response.json()
            documents = data.get("results", {}).get("documents", [])

            if documents:
                doc = documents[0]
                sentiment = doc.get("sentiment", "neutral")
                confidence = doc.get("confidenceScores", {})

                negative_score = confidence.get("negative", 0)
                positive_score = confidence.get("positive", 0)

                # High negative sentiment is a scam signal
                if sentiment == "negative" and negative_score > 0.7:
                    score += 20
                    triggers.append("Azure: high_negative_sentiment")

                # Very low positive with high negative
                if negative_score > 0.8 and positive_score < 0.1:
                    score += 10
                    triggers.append("Azure: threatening_tone_detected")

                logging.info(f"Azure sentiment: {sentiment}, negative: {negative_score:.2f}")

    except Exception as e:
        logging.warning(f"Azure layer error (non-critical): {e}")

    return min(score, 30), triggers

def calculate_final_score_and_label(rule_score: int, blacklist_score: int, ai_score: int, azure_score: int = 0) -> tuple:
    total_score = min(rule_score + blacklist_score + ai_score + azure_score, 100)
    if total_score <= 30:
        label = "🟢 Safe"
        guidance = "This content appears safe. No significant risk indicators detected."
    elif total_score <= 70:
        label = "🟡 Suspicious"
        guidance = "This content shows some warning signs. Exercise caution and verify authenticity before taking any action."
    else:
        label = "🔴 Dangerous"
        guidance = "This content is highly likely to be a scam. Do not share personal information, click links, or send money."
    return total_score, label, guidance

def build_explanation(triggers: List[str]) -> str:
    explanations = []
    for trigger in triggers:
        for key, explanation in EXPLANATION_MAP.items():
            if key in trigger.lower():
                if explanation not in explanations:
                    explanations.append(explanation)
    if not explanations:
        return "No specific scam patterns detected."
    return " ".join(explanations)

async def run_scan(content: str, scan_type: Optional[str] = None) -> ScanResult:
    content = content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    detected_type = scan_type or detect_input_type(content)

    # Run all four detection layers
    rule_score, rule_triggers = apply_rule_layer(content, detected_type)
    blacklist_score, blacklist_triggers = await apply_blacklist_layer(content, detected_type)
    ai_score, ai_triggers = apply_ai_layer(content)
    azure_score, azure_triggers = await apply_azure_layer(content)

    total_score, label, guidance = calculate_final_score_and_label(
        rule_score, blacklist_score, ai_score, azure_score
    )

    all_triggers = rule_triggers + blacklist_triggers + ai_triggers + azure_triggers
    explanation = build_explanation(all_triggers)

    result = ScanResult(
        content=content[:500],
        scan_type=detected_type,
        risk_score=total_score,
        label=label,
        guidance=guidance,
        triggers=all_triggers,
        explanation=explanation,
    )

    try:
        await db.scan_history.insert_one(result.dict())
    except Exception as e:
        logging.error(f"Failed to store scan history: {e}")

    return result

# ======================================================
# ML Model
# ======================================================

async def initialize_ml_model():
    global ml_model, vectorizer

    if MODEL_PATH.exists() and VECTORIZER_PATH.exists():
        try:
            with open(MODEL_PATH, 'rb') as f:
                ml_model = pickle.load(f)
            with open(VECTORIZER_PATH, 'rb') as f:
                vectorizer = pickle.load(f)
            logging.info("ML model loaded from disk.")
            return
        except Exception as e:
            logging.warning(f"Could not load saved model, retraining: {e}")

    try:
        dataset_url = "https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv"
        dataset_path = ROOT_DIR / "sms_spam.tsv"

        if not dataset_path.exists():
            logging.info("Downloading SMS Spam dataset...")
            urllib.request.urlretrieve(dataset_url, dataset_path)

        texts = []
        labels = []
        with open(dataset_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    label, text = parts
                    labels.append(1 if label == 'spam' else 0)
                    texts.append(text)

        logging.info(f"Loaded {len(texts)} messages ({sum(labels)} spam, {len(labels)-sum(labels)} ham)")

        X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42)

        vectorizer = TfidfVectorizer(max_features=3000, stop_words='english')
        X_train_vec = vectorizer.fit_transform(X_train)
        X_test_vec = vectorizer.transform(X_test)

        ml_model = LogisticRegression(random_state=42, max_iter=1000)
        ml_model.fit(X_train_vec, y_train)

        y_pred = ml_model.predict(X_test_vec)
        accuracy = accuracy_score(y_test, y_pred)
        logging.info(f"ML model trained. Test accuracy: {accuracy:.2%}")

        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(ml_model, f)
        with open(VECTORIZER_PATH, 'wb') as f:
            pickle.dump(vectorizer, f)
        logging.info("ML model saved to disk.")

    except Exception as e:
        logging.error(f"Failed to initialize ML model: {e}")
        ml_model = None
        vectorizer = None

# ======================================================
# Database Seeding
# ======================================================

async def seed_database():
    try:
        domains_to_seed = [
            {"domain": "bit.ly", "reason": "URL shortener often used in scams"},
            {"domain": "scam-bank-verify.com", "reason": "Phishing domain"},
            {"domain": "fake-lottery.net", "reason": "Lottery scam domain"},
            {"domain": "urgent-account-verify.org", "reason": "Account verification scam"},
            {"domain": "claim-inheritance.biz", "reason": "Inheritance scam domain"},
            {"domain": "irs-tax-urgent.com", "reason": "Fake IRS domain"},
        ]
        for domain_data in domains_to_seed:
            existing = await db.blocked_domains.find_one({"domain": domain_data["domain"]})
            if not existing:
                await db.blocked_domains.insert_one(domain_data)

        numbers_to_seed = [
            {"number": "555-0123", "reason": "Known scam number"},
            {"number": "1-800-SCAM-1", "reason": "Fake support number"},
            {"number": "+1-555-000-0000", "reason": "Common scam pattern"},
            {"number": "123-456-7890", "reason": "Test scam number"},
        ]
        for number_data in numbers_to_seed:
            existing = await db.blocked_numbers.find_one({"number": number_data["number"]})
            if not existing:
                await db.blocked_numbers.insert_one(number_data)

        messages_to_seed = [
            {"pattern": "congratulations you have won", "reason": "Lottery scam pattern"},
            {"pattern": "urgent account verification", "reason": "Phishing pattern"},
            {"pattern": "click here to claim", "reason": "Malicious link pattern"},
            {"pattern": "suspended within 24 hours", "reason": "Urgency scam pattern"},
            {"pattern": "final notice", "reason": "Fake authority pattern"},
        ]
        for message_data in messages_to_seed:
            existing = await db.blocked_messages.find_one({"pattern": message_data["pattern"]})
            if not existing:
                await db.blocked_messages.insert_one(message_data)

        logging.info("Database seeded successfully")
    except Exception as e:
        logging.error(f"Database seeding error: {e}")

# ======================================================
# API Endpoints
# ======================================================

@api_router.post("/scan", response_model=ScanResult)
async def scan_content(request: ScanRequest):
    try:
        return await run_scan(request.content, request.scan_type)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Scan error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during scan")

@api_router.post("/scan/file", response_model=ScanResult)
async def scan_file(file: UploadFile = File(...)):
    try:
        allowed_extensions = ['.txt', '.eml', '.csv', '.msg', '.pdf']
        file_ext = os.path.splitext(file.filename or '')[1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: .txt, .eml, .csv, .msg, .pdf"
            )

        content_bytes = await file.read()

        if len(content_bytes) > 1_000_000:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 1MB.")

        if file_ext == '.pdf':
            try:
                from PyPDF2 import PdfReader
                pdf_reader = PdfReader(io.BytesIO(content_bytes))
                content = ""
                for page in pdf_reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        content += extracted + "\n"
                content = content.strip()
                if not content:
                    raise HTTPException(status_code=400, detail="Could not extract text from PDF. The PDF may be scanned or image-based.")
            except HTTPException:
                raise
            except Exception as e:
                logging.error(f"PDF extraction error: {e}")
                raise HTTPException(status_code=400, detail="Could not read PDF file.")
        elif file_ext == '.eml':
            try:
                content = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                content = content_bytes.decode('latin-1')
            lines = content.split('\n')
            body_lines = []
            in_body = False
            subject = ""
            for line in lines:
                if line.lower().startswith('subject:'):
                    subject = line[8:].strip()
                if line.strip() == '' and not in_body:
                    in_body = True
                    continue
                if in_body:
                    body_lines.append(line)
            body = '\n'.join(body_lines).strip()
            content = f"{subject}\n{body}" if subject else body
        else:
            try:
                content = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                content = content_bytes.decode('latin-1')

        content = content[:2000].strip()

        if not content:
            raise HTTPException(status_code=400, detail="Could not extract text from file.")

        scan_type = 'email' if file_ext == '.eml' else None
        return await run_scan(content, scan_type)

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"File scan error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process file.")

@api_router.get("/history", response_model=List[HistoryItem])
async def get_scan_history():
    try:
        history = await db.scan_history.find().sort("timestamp", -1).limit(10).to_list(10)
        results = []
        for item in history:
            if 'explanation' not in item:
                item['explanation'] = ""
            results.append(HistoryItem(**item))
        return results
    except Exception as e:
        logging.error(f"History retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve scan history")

@api_router.get("/stats")
async def get_stats():
    try:
        total_scans = await db.scan_history.count_documents({})
        safe_scans = await db.scan_history.count_documents({"label": "🟢 Safe"})
        suspicious_scans = await db.scan_history.count_documents({"label": "🟡 Suspicious"})
        dangerous_scans = await db.scan_history.count_documents({"label": "🔴 Dangerous"})
        return {
            "total_scans": total_scans,
            "safe_scans": safe_scans,
            "suspicious_scans": suspicious_scans,
            "dangerous_scans": dangerous_scans
        }
    except Exception as e:
        logging.error(f"Stats retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "ml_model_loaded": ml_model is not None,
        "training_data": "UCI SMS Spam Collection (5,574 messages)",
        "detection_layers": 4,
        "azure_ai_enabled": bool(AZURE_LANGUAGE_KEY),
        "supported_scan_types": ["text", "url", "phone", "email", "file"],
        "supported_file_types": [".txt", ".eml", ".csv", ".msg", ".pdf"]
    }

# ======================================================
# App Setup
# ======================================================

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await initialize_ml_model()
    await seed_database()
    if AZURE_LANGUAGE_KEY:
        logging.info("Azure AI Language integration enabled.")
    else:
        logging.warning("Azure AI Language key not set — Layer 4 disabled.")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
