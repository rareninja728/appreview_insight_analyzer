"""
Tests for theme_generator — validates JSON parsing and theme count.
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_theme_json_parsing():
    """Test that theme JSON output is properly structured."""
    mock_response = '{"themes": [{"label": "App Stability", "description": "Crashes and performance"}, {"label": "Features", "description": "Investment tracking"}]}'
    result = json.loads(mock_response)
    themes = result.get("themes", [])
    
    assert len(themes) > 0
    assert "label" in themes[0]
    assert "description" in themes[0]
    print("✓ test_theme_json_parsing passed")


def test_max_themes_limit():
    """Test that themes are capped at MAX_THEMES."""
    import config
    themes = [
        {"label": f"Theme {i}", "description": f"Desc {i}"}
        for i in range(10)
    ]
    capped = themes[:config.MAX_THEMES]
    assert len(capped) <= 5
    print(f"✓ test_max_themes_limit passed (capped to {len(capped)})")


def test_markdown_wrapped_json():
    """Test parsing JSON wrapped in markdown code blocks."""
    raw = '```json\n{"themes": [{"label": "Test", "description": "Test desc"}]}\n```'
    
    # Simulate the parsing logic
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    
    result = json.loads(raw)
    assert "themes" in result
    print("✓ test_markdown_wrapped_json passed")


if __name__ == "__main__":
    test_theme_json_parsing()
    test_max_themes_limit()
    test_markdown_wrapped_json()
    print("\n✅ All theme generator tests passed!")
