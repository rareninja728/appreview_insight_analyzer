import os
import logging
from dotenv import load_dotenv

load_dotenv()

_logger = logging.getLogger("INDmoney-Config")

# ── API Connectivity (Step 1) ─────────────────────────────
# Local fallback: http://localhost:8080
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080").rstrip("/")

# ── Groq LLM ──────────────────────────────────────────────
# Strip whitespace so a secret saved with accidental spaces/newlines is caught
GROQ_API_KEY = (os.getenv("GROQ_API_KEY") or "").strip() or None
GROQ_MODEL = (os.getenv("GROQ_MODEL") or "llama-3.1-8b-instant").strip()

# ── App Identifiers ───────────────────────────────────────
APPLE_APP_ID = os.getenv("APPLE_APP_ID", "1450178837")
GOOGLE_PACKAGE = os.getenv("GOOGLE_PACKAGE", "in.indwealth")

# ── Email Configuration (Step 4) ──────────────────────────
SENDER_EMAIL = (os.getenv("EMAIL_ADDRESS") or "").strip() or None
EMAIL_APP_PASSWORD = (os.getenv("EMAIL_APP_PASSWORD") or "").strip() or None
EMAIL_ADDRESS = SENDER_EMAIL  # Default recipient to sender
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))

# Validation — warn for email keys, hard-fail for GROQ_API_KEY since sending
# a blank Bearer token causes a cryptic LocalProtocolError deep in httpx/h11.
if not GROQ_API_KEY:
    raise RuntimeError(
        "\n\n❌ GROQ_API_KEY is not set, empty, or contains only whitespace.\n"
        "   • Locally  : add GROQ_API_KEY=gsk_... to your .env file\n"
        "   • GitHub   : Settings → Secrets and variables → Actions\n"
        "                Delete the existing GROQ_API_KEY secret and re-create it.\n"
        "                Make sure there are NO spaces/newlines around the key value.\n"
        "   • Get a key: https://console.groq.com\n"
    )
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
