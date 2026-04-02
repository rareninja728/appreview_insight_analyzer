import os
import logging
from dotenv import load_dotenv

load_dotenv()

_logger = logging.getLogger("INDmoney-Config")

# ── API Connectivity (Step 1) ─────────────────────────────
# Local fallback: http://localhost:8080
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080").rstrip("/")

# ── Groq LLM ──────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# ── App Identifiers ───────────────────────────────────────
APPLE_APP_ID = os.getenv("APPLE_APP_ID", "1450178837")
GOOGLE_PACKAGE = os.getenv("GOOGLE_PACKAGE", "in.indwealth")

# ── Email Configuration (Step 4) ──────────────────────────
SENDER_EMAIL = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
EMAIL_ADDRESS = SENDER_EMAIL # Default recipient to sender
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))

# Soft validation — warn instead of crashing at import time.
# Hard asserts here would cause a silent AssertionError that kills GitHub Actions
# within 20–30s before any diagnostic output is shown.
if not GROQ_API_KEY:
    _logger.warning("WARNING: GROQ_API_KEY is not set. LLM calls will fail.")
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
