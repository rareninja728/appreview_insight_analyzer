"""
PII Stripper — Removes personally identifiable information from review text.
Handles emails, phone numbers, Aadhaar, PAN, and usernames.
"""

import re
from typing import List, Dict


# ── PII Regex Patterns ────────────────────────────────────
_PATTERNS = [
    # Email addresses
    (r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", "[REDACTED_EMAIL]"),
    # Indian phone numbers (10 digits, optional +91/0 prefix)
    (r"(?:\+91[\-\s]?|0)?[6-9]\d{9}\b", "[REDACTED_PHONE]"),
    # International phone patterns with country code
    (r"\+\d{1,3}[\-\s]?\d{6,12}\b", "[REDACTED_PHONE]"),
    # Aadhaar-like 12-digit numbers (with optional spaces/dashes)
    (r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b", "[REDACTED_ID]"),
    # PAN card pattern (ABCDE1234F)
    (r"\b[A-Z]{5}\d{4}[A-Z]\b", "[REDACTED_PAN]"),
    # UPI IDs (user@bank)
    (r"\b[a-zA-Z0-9.]+@[a-z]{3,}\b", "[REDACTED_UPI]"),
    # Account numbers (long digit sequences, 8-18 digits)
    (r"\b\d{8,18}\b", "[REDACTED_ACCOUNT]"),
]

# ── Quality Filter Patterns (Linguistic & Character) ──────
RE_HINDI = re.compile(r'[\u0900-\u097F]')  # Devanagari range
RE_EMOJI = re.compile(
    "["
    "\U0001f600-\U0001f64f" "\U0001f300-\U0001f5ff" "\U0001f680-\U0001f6ff"
    "\U0001f1e6-\U0001f1ff" "\U00002600-\U000026ff" "\U00002700-\U000027bf"
    "\U0001f900-\U0001f9ff" "\U0001fa70-\U0001faff"
    "]+", flags=re.UNICODE
)
_COMPILED_PATTERNS = [(re.compile(p, re.IGNORECASE), r) for p, r in _PATTERNS]


def strip_pii(text: str) -> str:
    """
    Remove PII from a single text string.

    Args:
        text: Raw review text

    Returns:
        Cleaned text with PII replaced by [REDACTED_*] tags
    """
    if not text:
        return text

    cleaned = text
    for pattern, replacement in _COMPILED_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)

    return cleaned


def strip_pii_from_reviews(reviews: List[Dict]) -> List[Dict]:
    """
    Remove PII and perform quality filtering on a list of reviews.
    1. Removes author-related fields.
    2. Filters out reviews containing emojis.
    3. Filters out reviews containing Hindi (Devanagari).
    4. Filters out reviews with < 5 words.
    5. Removes 'title' as it is redundant.
    """
    author_fields = {"author", "userName", "userId", "user_name", "user_id", "authorName"}
    cleaned_reviews = []

    for review in reviews:
        raw_text = review.get("text", "")
        if not isinstance(raw_text, str):
            continue

        # Filter 1: Emoji
        if RE_EMOJI.search(raw_text):
            continue

        # Filter 2: Hindi
        if RE_HINDI.search(raw_text):
            continue

        # Filter 3: Non-English (heuristic: > 15% non-ASCII)
        non_ascii_count = sum(1 for c in raw_text if ord(c) > 127)
        if non_ascii_count > (len(raw_text) * 0.15):
            continue

        # Filter 4: Word count
        if len(raw_text.split()) < 5:
            continue

        clean = {}
        for key, value in review.items():
            if key in author_fields or key == "title":
                continue  # Drop author and title
            if key == "text":
                clean[key] = strip_pii(value)
            else:
                clean[key] = value
        cleaned_reviews.append(clean)

    print(f"[PII] Quality Filter: kept {len(cleaned_reviews)}/{len(reviews)} reviews")
    return cleaned_reviews


if __name__ == "__main__":
    # Quick test
    test_texts = [
        "Contact me at john@gmail.com or call +91-9876543210",
        "My PAN is ABCDE1234F and Aadhaar 1234 5678 9012",
        "Great app! Love the SIP tracking feature.",
        "UPI: myname@ybl, account 123456789012345",
    ]
    for t in test_texts:
        print(f"  IN:  {t}")
        print(f"  OUT: {strip_pii(t)}")
        print()
