import os
import logging
from dotenv import load_dotenv

load_dotenv()

_logger = logging.getLogger("INDmoney-Config")

# ── API Connectivity (Step 1) ─────────────────────────────
# Local fallback: http://localhost:8080
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080").rstrip("/")

import re

# ── Groq LLM ──────────────────────────────────────────────
def _clean_key(key_name: str):
    val = os.getenv(key_name) or ""
    # 1. Strip basic whitespace
    val = val.strip()
    # 2. Filter out common 'ghost' values from broken CI/secret setups
    if val.lower() in ["", "none", "null", "undefined", "false"]:
        return None
    # 3. Force-remove non-printable or suspicious characters (\r, zero-width spaces, etc.)
    val = re.sub(r'[^a-zA-Z0-9_\-]', '', val)
    return val or None

GROQ_API_KEY = _clean_key("GROQ_API_KEY")
GROQ_MODEL = (os.getenv("GROQ_MODEL") or "llama-3.1-8b-instant").strip()

# Safe Logging (helps us debug without exposing the key)
_logger.info(f"Loaded config. GROQ_API_KEY present: {GROQ_API_KEY is not None}")
if GROQ_API_KEY:
    _logger.info(f"GROQ_API_KEY length: {len(GROQ_API_KEY)} characters.")

# ── App Identifiers ───────────────────────────────────────
APPLE_APP_ID = os.getenv("APPLE_APP_ID", "1450178837")
GOOGLE_PACKAGE = os.getenv("GOOGLE_PACKAGE", "in.indwealth")

# ── Email Configuration (Step 4) ──────────────────────────
SENDER_EMAIL = _clean_key("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = _clean_key("EMAIL_APP_PASSWORD")
EMAIL_ADDRESS = SENDER_EMAIL  # Default recipient to sender
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))

# Validation — hard-fail for GROQ_API_KEY to prevent cryptic httpx errors
if not GROQ_API_KEY:
    raise RuntimeError(
        "\n\n❌ GROQ_API_KEY is missing, too short, or invalid.\n"
        "   • Make sure your GitHub Secret is EXACTLY the key (gsk_...)\n"
        "   • Current status: Secret detected but was empty or failed validation.\n"
    )
elif len(GROQ_API_KEY) < 20: 
    raise RuntimeError(f"❌ GROQ_API_KEY is too short ({len(GROQ_API_KEY)} chars). Valid keys start with gsk_")
if not SENDER_EMAIL:
    _logger.warning("WARNING: EMAIL_ADDRESS is not set. Emails will not send.")
if not EMAIL_APP_PASSWORD:
    _logger.warning("WARNING: EMAIL_APP_PASSWORD is not set. SMTP auth will fail.")

# ── Analysis Settings ─────────────────────────────────────
MAX_THEMES = int(os.getenv("MAX_THEMES", 5))
NOTE_MAX_WORDS = int(os.getenv("NOTE_MAX_WORDS", 250))
WEEKS_BACK = int(os.getenv("WEEKS_BACK", 1))

# ── Paths ─────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
WEEKLY_NOTES_DIR = os.path.join(BASE_DIR, "outputs", "weekly_notes")
EMAIL_DRAFTS_DIR = os.path.join(BASE_DIR, "outputs", "email_drafts")

# Ensure directories exist
for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, WEEKLY_NOTES_DIR, EMAIL_DRAFTS_DIR]:
    os.makedirs(d, exist_ok=True)
