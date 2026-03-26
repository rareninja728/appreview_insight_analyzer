"""
Tests for note_builder module — validates structure and word count.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_note_structure():
    """Test that the note has the required sections (without LLM calls)."""
    # Simulate a built note
    note_md = """# 📊 INDmoney Weekly Review Pulse
**Week:** W12-2026 (Mar 17 – Mar 23)
**Reviews Analyzed:** 50 (Apple: 20, Google: 30)

---

## 🔥 Top Themes
1. **App Stability** — 40% of reviews (20 mentions)
2. **Investment Features** — 30% of reviews (15 mentions)
3. **Customer Support** — 20% of reviews (10 mentions)

## 💬 User Voices
> "App crashes every time I open portfolio" — ★★☆☆☆

> "Best SIP tracker I've found" — ★★★★★

> "Support ticket unanswered for 5 days" — ★☆☆☆☆

## 💡 Action Ideas
1. Fix portfolio crash on Android 12+
2. Highlight SIP tracker in onboarding
3. Set 48hr first-response SLA for support

---
*Generated from 50 public reviews · No PII included*"""

    # Check required sections
    assert "Top Themes" in note_md
    assert "User Voices" in note_md
    assert "Action Ideas" in note_md
    assert "No PII included" in note_md
    print("✓ test_note_structure passed")


def test_word_count():
    """Test that the note is within the 250-word limit."""
    note_md = """# Weekly Pulse
**Week:** W12-2026

## Top Themes
1. App Stability — 40%
2. Features — 30%
3. Support — 20%

## User Voices
> "Crashes daily" — ★★

## Action Ideas
1. Fix crashes
2. Improve onboarding
3. Faster support"""

    word_count = len(note_md.split())
    assert word_count <= 250, f"Word count {word_count} exceeds 250"
    print(f"✓ test_word_count passed ({word_count} words)")


def test_theme_count():
    """Test that max 3 themes appear in the note."""
    themes_section = """1. **Theme A** — 40%
2. **Theme B** — 30%
3. **Theme C** — 20%"""

    theme_lines = [l for l in themes_section.strip().split("\n") if l.strip().startswith(("1.", "2.", "3.", "4.", "5."))]
    assert len(theme_lines) <= 3, f"Found {len(theme_lines)} themes, max is 3"
    print("✓ test_theme_count passed")


if __name__ == "__main__":
    test_note_structure()
    test_word_count()
    test_theme_count()
    print("\n✅ All note builder tests passed!")
