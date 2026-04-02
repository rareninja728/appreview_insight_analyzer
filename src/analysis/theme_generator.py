"""
Theme Generator — Uses Groq LLM to discover 3–5 recurring themes from reviews.
"""

import json
import sys
import os
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import config

from groq import Groq


def _get_client() -> Groq:
    """Initialize Groq client."""
    if not config.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set. Please check your environment variables or GitHub Secrets.")
    return Groq(api_key=config.GROQ_API_KEY)


def _sample_reviews(reviews: List[Dict], max_sample: int = 100) -> List[Dict]:
    """
    Stratified sample of reviews by rating for balanced theme discovery.
    """
    import random
    random.seed(42)

    if len(reviews) <= max_sample:
        return reviews

    # Group by rating
    by_rating: Dict[int, List[Dict]] = {}
    for r in reviews:
        rating = r.get("rating", 3)
        by_rating.setdefault(rating, []).append(r)

    # Sample proportionally
    sampled = []
    for rating, group in by_rating.items():
        n = max(1, int(len(group) / len(reviews) * max_sample))
        sampled.extend(random.sample(group, min(n, len(group))))

    return sampled[:max_sample]


def generate_themes(reviews: List[Dict]) -> List[Dict]:
    """
    Pass 1 — Theme Discovery.
    Sends a sample of reviews to Groq and asks for 3–5 theme labels.

    Args:
        reviews: List of review dicts (must have 'text' key)

    Returns:
        List of theme dicts: [{"label": "...", "description": "..."}]
    """
    client = _get_client()
    sampled = _sample_reviews(reviews)

    # Build review text block
    review_lines = []
    for i, r in enumerate(sampled):
        stars = "★" * r.get("rating", 0) + "☆" * (5 - r.get("rating", 0))
        review_lines.append(f"[{i+1}] {stars} | {r.get('text', '')[:200]}")

    reviews_block = "\n".join(review_lines)

    prompt = f"""You are a senior product analyst. Analyze these app reviews for INDmoney 
(a personal finance & investment app) and identify exactly 3 to 5 recurring themes.

Each theme should be:
- A short label (2-4 words, e.g. "App Stability", "Investment Features")  
- A one-line description of what users are saying about this theme

Rules:
- Max {config.MAX_THEMES} themes
- Themes should cover the most common feedback patterns
- Combine similar topics into one theme
- Do NOT include any usernames, emails, or personal identifiers

Reviews:
{reviews_block}

Return ONLY valid JSON (no markdown, no explanation):
{{"themes": [{{"label": "Theme Label", "description": "What users say about this"}}]}}"""

    response = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500,
    )

    raw = response.choices[0].message.content.strip()

    # Parse JSON — handle possible markdown wrapping
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        result = json.loads(raw)
        themes = result.get("themes", [])
    except json.JSONDecodeError:
        print(f"[Themes] Failed to parse LLM response: {raw[:200]}")
        themes = [
            {"label": "General Feedback", "description": "Mixed user feedback"},
        ]

    # Enforce max themes
    themes = themes[: config.MAX_THEMES]
    print(f"[Themes] Discovered {len(themes)} themes:")
    for t in themes:
        print(f"  • {t['label']}: {t['description']}")

    return themes


if __name__ == "__main__":
    # Quick test with dummy data
    test_reviews = [
        {"rating": 1, "text": "App crashes every time I open portfolio"},
        {"rating": 5, "text": "Love the SIP tracker, best feature"},
        {"rating": 2, "text": "Customer support never responds"},
        {"rating": 4, "text": "Great app but UI could be better"},
        {"rating": 1, "text": "Keeps freezing on Android 12"},
    ]
    themes = generate_themes(test_reviews)
    print(json.dumps(themes, indent=2))
