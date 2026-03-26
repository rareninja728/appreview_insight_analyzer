"""
Centralized configuration for INDmoney Review Pulse.
Loads environment variables and defines project-wide constants.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Groq LLM ──────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.1-8b-instant"

# ── App Identifiers ───────────────────────────────────────
APPLE_APP_ID = "1450178837"          # INDmoney on App Store
GOOGLE_PACKAGE = "in.indwealth"      # INDmoney on Play Store

# ── Email ─────────────────────────────────────────────────
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

# ── Analysis Settings ─────────────────────────────────────
MAX_THEMES = 5
NOTE_MAX_WORDS = 250
WEEKS_BACK = 1

# ── Paths ─────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
WEEKLY_NOTES_DIR = os.path.join(BASE_DIR, "outputs", "weekly_notes")
EMAIL_DRAFTS_DIR = os.path.join(BASE_DIR, "outputs", "email_drafts")

# Ensure directories exist
for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, WEEKLY_NOTES_DIR, EMAIL_DRAFTS_DIR]:
    os.makedirs(d, exist_ok=True)
