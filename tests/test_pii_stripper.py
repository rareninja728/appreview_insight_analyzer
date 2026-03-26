"""
Tests for pii_stripper module.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ingestion.pii_stripper import strip_pii, strip_pii_from_reviews


def test_email_redaction():
    text = "Contact me at john.doe@gmail.com for help"
    result = strip_pii(text)
    assert "@" not in result
    assert "REDACTED" in result
    print("✓ test_email_redaction passed")


def test_phone_redaction():
    text = "Call me at +91-9876543210 or 08012345678"
    result = strip_pii(text)
    assert "9876543210" not in result
    assert "REDACTED" in result
    print("✓ test_phone_redaction passed")


def test_aadhaar_redaction():
    text = "My Aadhaar is 1234 5678 9012"
    result = strip_pii(text)
    assert "1234 5678 9012" not in result
    assert "REDACTED" in result
    print("✓ test_aadhaar_redaction passed")


def test_pan_redaction():
    text = "PAN card ABCDE1234F please verify"
    result = strip_pii(text)
    assert "ABCDE1234F" not in result
    assert "REDACTED" in result
    print("✓ test_pan_redaction passed")


def test_clean_text_unchanged():
    text = "Great app! Love the mutual fund tracking feature."
    result = strip_pii(text)
    assert result == text
    print("✓ test_clean_text_unchanged passed")


def test_strip_pii_from_reviews():
    reviews = [
        {"source": "google", "rating": 3, "title": "Test", "text": "Email me at test@test.com", "author": "John"},
        {"source": "apple", "rating": 5, "title": "Great", "text": "No PII here", "userName": "Jane"},
    ]
    result = strip_pii_from_reviews(reviews)
    assert len(result) == 2
    assert "author" not in result[0]
    assert "userName" not in result[1]
    assert "@" not in result[0].get("text", "")
    print("✓ test_strip_pii_from_reviews passed")


if __name__ == "__main__":
    test_email_redaction()
    test_phone_redaction()
    test_aadhaar_redaction()
    test_pan_redaction()
    test_clean_text_unchanged()
    test_strip_pii_from_reviews()
    print("\n✅ All PII stripper tests passed!")
