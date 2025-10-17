"""
config.py — Centralized configuration for the ScamShield backend.
Loads environment variables for MongoDB, secret keys, and version info.
"""

import os
from dotenv import load_dotenv

# Load variables from .env if available
load_dotenv()

# Core settings
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "scamshield")
SECRET_KEY = os.getenv("SECRET_KEY", "default-secret")
API_VERSION = os.getenv("API_VERSION", "v1")

def get_settings():
    """Return settings as a dictionary for debugging or dependency injection."""
    return {
        "MONGO_URL": MONGO_URL,
        "DB_NAME": DB_NAME,
        "SECRET_KEY": SECRET_KEY,
        "API_VERSION": API_VERSION,
    }
