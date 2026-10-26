import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path, override=True)

# ============================================================
# 4 Separate API Keys for 4 different Fraud Detection Models
# Set these in your .env file
# ============================================================

# Model 1: Text / Social Media Message Analysis
TEXT_ANALYZER_API_KEY = os.getenv("TEXT_ANALYZER_API_KEY", "")

# Model 2: URL / Link Analysis
URL_ANALYZER_API_KEY = os.getenv("URL_ANALYZER_API_KEY", "")

# Model 3: Image / Screenshot Analysis
IMAGE_ANALYZER_API_KEY = os.getenv("IMAGE_ANALYZER_API_KEY", "")

# Model 4: QR Code Analysis
QR_ANALYZER_API_KEY = os.getenv("QR_ANALYZER_API_KEY", "")

# Model 5: Audio / Call Recording Fraud Analysis
AUDIO_ANALYZER_API_KEY = os.getenv("AUDIO_ANALYZER_API_KEY") or os.getenv("TEXT_ANALYZER_API_KEY", "")

# Flask config
SECRET_KEY = os.getenv("SECRET_KEY", "fraudshield-ultra-secret-key-2024")
DEBUG = os.getenv("DEBUG", "True") == "True"
DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///fraudshield.db")

import warnings
try:
    from requests.exceptions import RequestsDependencyWarning
    warnings.filterwarnings("ignore", category=RequestsDependencyWarning)
except Exception:
    pass

# Gemini model settings
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
GEMINI_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-3.1-flash-lite")
GEMINI_AUDIO_MODEL = os.getenv("GEMINI_AUDIO_MODEL", "gemini-2.5-flash")

# Upload settings
UPLOAD_FOLDER = "uploads"
MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB
ALLOWED_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "bmp", "webp", "pdf",
    "mp3", "wav", "m4a", "ogg", "aac", "flac", "webm", "wma", "opus"
}

# Risk thresholds
RISK_THRESHOLDS = {
    "CRITICAL": 85,
    "HIGH": 65,
    "MEDIUM": 40,
    "LOW": 0,
}

SCAM_TYPES = [
    "Phishing Attack",
    "Financial Scam",
    "Identity Theft",
    "Fake Authority",
    "Lottery / Prize Scam",
    "Investment Fraud",
    "Romance Scam",
    "Tech Support Scam",
    "Employment Scam",
    "AI-Generated Fake",
    "Malware / Ransomware",
    "Counterfeit Document",
    "Digital Arrest Scam",
    "Vishing / Phone Scam",
    "Customs Parcel Scam",
    "AI Voice Clone Extortion",
    "No Fraud Detected",
]
