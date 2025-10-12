from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import re
import asyncio
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
import pickle
import numpy as np

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="ScamShield API", description="Hybrid fraud detection system")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Global ML model variables
ml_model = None
vectorizer = None

# Define Models
class ScanRequest(BaseModel):
    content: str
    scan_type: Optional[str] = None  # auto-detected if not provided

class ScanResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    scan_type: str
    risk_score: int
    label: str
    guidance: str
    triggers: List[str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HistoryItem(BaseModel):
    id: str
    content: str
    scan_type: str
    risk_score: int
    label: str
    guidance: str
    triggers: List[str]
    timestamp: datetime

# Rule-based detection patterns
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
        r'http.*suspicious|shortened.*url',
    ]
}

def detect_input_type(content: str) -> str:
    """Auto-detect the type of input content"""
    content = content.strip()
    
    # Phone number pattern
    phone_pattern = r'^[\+]?[1-9]?[\-\.\s]?\(?[0-9]{3}\)?[\-\.\s]?[0-9]{3}[\-\.\s]?[0-9]{4,6}$'
    if re.match(phone_pattern, content) or content.replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
        return 'phone'
    
    # URL pattern
    url_pattern = r'^https?://|^www\.|\.com$|\.org$|\.net$'
    if re.search(url_pattern, content, re.IGNORECASE):
        return 'url'
    
    # Default to text message
    return 'text'

def apply_rule_layer(content: str, scan_type: str) -> tuple[int, List[str]]:
    """Apply rule-based detection and return score + triggers"""
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
                triggers.append(f"Rule: {category}")
                break
    
    # Additional rules based on type
    if scan_type == 'phone':
        # Check for more specific scam number patterns (avoid false positives)
        scam_number_patterns = [
            r'^(000|111|222|333|444|666|777|888|999)[-\s]?\d{3}[-\s]?\d{4}$',  # Full repeated digits
            r'^\+1[-\s]?900[-\s]?\d{3}[-\s]?\d{4}$',  # Premium rate numbers
            r'^\d{4,6}$',  # Too short (likely fake)
            r'^\d{11,}$',  # Too long (likely fake)
        ]
        for pattern in scam_number_patterns:
            if re.search(pattern, content.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')):
                score += 20
                triggers.append("Rule: suspicious_number_pattern")
                break
    
    elif scan_type == 'url':
        # Check for suspicious URL characteristics (more specific)
        content_clean = content.lower().strip()
        suspicious_url_patterns = [
            r'^https?://[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}',  # Direct IP address
            r'[a-z0-9]{20,}\.',  # Very long random subdomain (20+ chars)
            r'[0-9]{10,}\.',  # Long numeric subdomain
        ]
        
        # Check for known legitimate domains to avoid false positives
        legitimate_domains = ['google.com', 'microsoft.com', 'apple.com', 'amazon.com', 'facebook.com', 'youtube.com', 'wikipedia.org']
        is_legitimate = any(domain in content_clean for domain in legitimate_domains)
        
        if not is_legitimate:
            for pattern in suspicious_url_patterns:
                if re.search(pattern, content_clean):
                    score += 25
                    triggers.append("Rule: suspicious_url_pattern")
                    break
    
    return min(score, 70), triggers  # Cap rule score at 70

async def apply_blacklist_layer(content: str, scan_type: str) -> tuple[int, List[str]]:
    """Check against MongoDB blacklists"""
    score = 0
    triggers = []
    
    try:
        if scan_type == 'phone':
            # Check blocked numbers
            blocked = await db.blocked_numbers.find_one({"number": content})
            if blocked:
                score += 50
                triggers.append("Blacklist: known_scam_number")
        
        elif scan_type == 'url':
            # Extract domain from URL
            domain_match = re.search(r'://([^/]+)', content)
            if domain_match:
                domain = domain_match.group(1).lower()
                
                # Skip legitimate domains
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
        
        elif scan_type == 'text':
            # Check against blocked message patterns
            blocked_messages = await db.blocked_messages.find().to_list(100)
            for blocked_msg in blocked_messages:
                if blocked_msg['pattern'].lower() in content.lower():
                    score += 50
                    triggers.append("Blacklist: known_scam_message")
                    break
    
    except Exception as e:
        logging.error(f"Blacklist check error: {e}")
    
    return score, triggers

def apply_ai_layer(content: str) -> tuple[int, List[str]]:
    """Apply ML-based detection"""
    global ml_model, vectorizer
    
    if ml_model is None or vectorizer is None:
        return 0, []
    
    try:
        # Vectorize the content
        content_vector = vectorizer.transform([content])
        
        # Get prediction probability
        proba = ml_model.predict_proba(content_vector)[0]
        scam_probability = proba[1] if len(proba) > 1 else 0
        
        # Convert probability to score (0-40 points)
        ai_score = int(scam_probability * 40)
        
        triggers = []
        if ai_score > 20:
            triggers.append("AI: suspicious_language_patterns")
        
        return ai_score, triggers
    
    except Exception as e:
        logging.error(f"AI layer error: {e}")
        return 0, []

def calculate_final_score_and_label(rule_score: int, blacklist_score: int, ai_score: int) -> tuple[int, str, str]:
    """Calculate final risk score and determine label and guidance"""
    total_score = min(rule_score + blacklist_score + ai_score, 100)
    
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

async def initialize_ml_model():
    """Initialize the ML model with training data"""
    global ml_model, vectorizer
    
    try:
        # Training data - mix of scam and legitimate messages
        training_texts = [
            # Scam examples
            "URGENT: Your account will be suspended in 24 hours. Click here to verify immediately!",
            "Congratulations! You've won $1,000,000 in our lottery. Claim your prize now!",
            "IRS Notice: You owe back taxes. Pay immediately to avoid arrest.",
            "Your bank account has been compromised. Verify your details: bit.ly/secure123",
            "Final notice: Your subscription expires today. Renew now or lose access forever!",
            "You've inherited $2.5 million from a distant relative. Contact us to claim.",
            "ALERT: Suspicious activity detected. Enter your PIN to secure your account.",
            "Limited time offer: Bitcoin investment returns 500% guaranteed!",
            "Police warrant issued. Call this number immediately to resolve: 555-SCAM",
            "Your computer is infected! Download our antivirus software now!",
            
            # Legitimate examples
            "Hi, this is a reminder about your appointment tomorrow at 2 PM.",
            "Your order has been shipped and will arrive in 2-3 business days.",
            "Thank you for your purchase. Your receipt is attached.",
            "Meeting rescheduled to Friday 10 AM. Please confirm attendance.",
            "Your subscription renews next month. No action needed.",
            "Weather alert: Rain expected this afternoon. Drive safely!",
            "Happy birthday! Hope you have a wonderful day.",
            "Your package was delivered to your front door.",
            "Reminder: Library books are due next week.",
            "New menu items available at your favorite restaurant!",
        ]
        
        # Labels (0 = legitimate, 1 = scam)
        training_labels = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  # First 10 are scams
                          0, 0, 0, 0, 0, 0, 0, 0, 0, 0]   # Last 10 are legitimate
        
        # Create and train the model
        vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        X = vectorizer.fit_transform(training_texts)
        
        ml_model = LogisticRegression(random_state=42)
        ml_model.fit(X, training_labels)
        
        logging.info("ML model initialized successfully")
    
    except Exception as e:
        logging.error(f"Failed to initialize ML model: {e}")
        ml_model = None
        vectorizer = None

async def seed_database():
    """Seed the database with initial blacklist data"""
    try:
        # Seed blocked domains
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
        
        # Seed blocked numbers
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
        
        # Seed blocked message patterns
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

# API Endpoints
@api_router.post("/scan", response_model=ScanResult)
async def scan_content(request: ScanRequest):
    """Main scanning endpoint that applies all detection layers"""
    try:
        content = request.content.strip()
        if not content:
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        # Auto-detect input type if not provided
        scan_type = request.scan_type or detect_input_type(content)
        
        # Apply detection layers
        rule_score, rule_triggers = apply_rule_layer(content, scan_type)
        blacklist_score, blacklist_triggers = await apply_blacklist_layer(content, scan_type)
        ai_score, ai_triggers = apply_ai_layer(content)
        
        # Calculate final results
        total_score, label, guidance = calculate_final_score_and_label(
            rule_score, blacklist_score, ai_score
        )
        
        # Combine all triggers
        all_triggers = rule_triggers + blacklist_triggers + ai_triggers
        
        # Create result
        result = ScanResult(
            content=content,
            scan_type=scan_type,
            risk_score=total_score,
            label=label,
            guidance=guidance,
            triggers=all_triggers
        )
        
        # Store in history
        try:
            await db.scan_history.insert_one(result.dict())
        except Exception as e:
            logging.error(f"Failed to store scan history: {e}")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Scan error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during scan")

@api_router.get("/history", response_model=List[HistoryItem])
async def get_scan_history():
    """Get the last 10 scan results"""
    try:
        history = await db.scan_history.find().sort("timestamp", -1).limit(10).to_list(10)
        return [HistoryItem(**item) for item in history]
    except Exception as e:
        logging.error(f"History retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve scan history")

@api_router.get("/stats")
async def get_stats():
    """Get scanning statistics"""
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

# Health check endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "ml_model_loaded": ml_model is not None}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize ML model and seed database on startup"""
    await initialize_ml_model()
    await seed_database()

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close database connection on shutdown"""
    client.close()