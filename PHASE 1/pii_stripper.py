import re
import json
import os
from typing import List, Dict

# ── PII Regex Patterns ────────────────────────────────────

# Email: Simple but effective
RE_EMAIL = r'[a-zA-Z0-9._%+-]+@ [a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

# Phone: Covers typical Indian 10-digit formats with prefixes
RE_PHONE = r'(\+91[\-\s]?)?[6789]\d{9}'

# Aadhaar: 12-digit number (XXXX XXXX XXXX or XXXXXXXXXXXX)
RE_AADHAAR = r'\d{4}[\-\s]?\d{4}[\-\s]?\d{4}'

# PAN: 5 letters, 4 digits, 1 letter (Example: ABCDE1234F)
RE_PAN = r'[A-Z]{5}[0-9]{4}[A-Z]{1}'

# UPI: Example: someone@okicici, someone@paytm, 9999999999@ybl
RE_UPI = r'[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}'

# Generic Account numbers: 9 to 18 digits (used mostly in finance/banking apps)
RE_BANK_ACC = r'\b\d{9,18}\b'

# ── Quality Filters (Linguistic & Formatting) ─────────────

# Hindi (Devanagari) range: \u0900-\u097F
RE_HINDI = re.compile(r'[\u0900-\u097F]')

# Emojis (Simplified range covering most Emoji blocks)
RE_EMOJI = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # Emoticons
    "\U0001f300-\U0001f5ff"  # Misc Symbols and Pictographs
    "\U0001f680-\U0001f6ff"  # Transport and Map Symbols
    "\U0001f1e6-\U0001f1ff"  # Regional Indicator Symbols
    "\U00002600-\U000026ff"  # Misc Symbols
    "\U00002700-\U000027bf"  # Dingbats
    "\U0001f900-\U0001f9ff"  # Supplemental Symbols and Pictographs
    "\U0001fa70-\U0001faff"  # Symbols and Pictographs Extended-A
    "]+", 
    flags=re.UNICODE
)

# ── Core Functions ──────────────────────────────────────────

def strip_pii_from_text(text: str) -> str:
    """
    Remove sensitive information (emails, phones, IDs) from a string.
    Returns the redacted string.
    """
    if not isinstance(text, str):
        return ""
    
    # Run through patterns sequentially
    text = re.sub(RE_EMAIL, "[REDACTED_EMAIL]", text)
    text = re.sub(RE_PHONE, "[REDACTED_PHONE]", text)
    text = re.sub(RE_AADHAAR, "[REDACTED_ID]", text)
    text = re.sub(RE_PAN, "[REDACTED_ID]", text)
    text = re.sub(RE_UPI, "[REDACTED_PAYMENT_ID]", text)
    
    # Redact large digit sequences like bank account numbers
    # only if they are not common dates (like 20240323)
    def redact_digits(match):
        val = match.group(0)
        # Simple heuristic to avoid redacting years/dates in some formats
        if 20000000 <= int(val) <= 20301231:
            return val
        return "[REDACTED_NUMBER]"
    
    text = re.sub(RE_BANK_ACC, redact_digits, text)

    return text

def strip_pii_from_reviews(reviews: List[Dict]) -> List[Dict]:
    """
    Apply PII stripping and quality filtering to a list of reviews.
    1. Removes author-related fields (no usernames/emails/IDs).
    2. Removes the 'title' field as it's not required.
    3. Filters out reviews with fewer than 5 words.
    4. Filters out reviews containing emojis.
    5. Filters out reviews containing Hindi (Devanagari) or other non-English scripts.
    """
    clean_reviews = []
    
    for r in reviews:
        # Clone to avoid mutating original
        new_r = r.copy()
        
        # Original text
        raw_text = new_r.get("text", "")
        if not isinstance(raw_text, str):
            continue

        # Filter 1: Check for emojis (User requested: "remove anything that is with the emoji")
        if RE_EMOJI.search(raw_text):
            continue

        # Filter 2: Check for Hindi/Devanagari (User requested: "remove anything that is written in hindi")
        if RE_HINDI.search(raw_text):
            continue

        # Filter 3: Check for general non-ASCII (Language other than English)
        # We allow common punctuation/symbols but skip heavily non-ASCII content
        # As a heuristic, if > 20% of chars are non-ASCII, it's likely not English
        non_ascii_count = sum(1 for c in raw_text if ord(c) > 127)
        if non_ascii_count > (len(raw_text) * 0.15): # 15% threshold
            continue

        # Redact text field (PII stripping)
        # Filter based on word count after potential redaction
        word_count = len(raw_text.split())
        if word_count < 5:
            continue

        new_r["text"] = strip_pii_from_text(raw_text)
        
        # Drop PII-heavy fields and not required fields like 'title'
        new_r.pop("author", None)
        new_r.pop("id", None)
        new_r.pop("userName", None)
        new_r.pop("reviewId", None)
        new_r.pop("title", None)

        clean_reviews.append(new_r)
        
    return clean_reviews

if __name__ == "__main__":
    # Test example
    test_text = "My email is test@domain.com and UPI is apurva@sbi. Aadhaar is 1234 5678 1234."
    print(f"Original: {test_text}")
    print(f"Redacted: {strip_pii_from_text(test_text)}")
