"""
Review Grouper — Assigns each review to one of the discovered themes using Groq LLM.
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
    return Groq(api_key=config.GROQ_API_KEY)


def assign_themes(
    reviews: List[Dict],
    themes: List[Dict],
    batch_size: int = 25,
) -> List[Dict]:
    """
    Pass 2 — Classify each review into one of the discovered themes.

    Args:
        reviews: List of review dicts (must have 'text' key)
        themes: List of theme dicts from theme_generator
        batch_size: Number of reviews to classify per LLM call

    Returns:
        List of review dicts with added 'theme' key
    """
    client = _get_client()
    theme_labels = [t["label"] for t in themes]
    themes_desc = "\n".join(
        [f"- {t['label']}: {t['description']}" for t in themes]
    )

    classified = []

    for batch_start in range(0, len(reviews), batch_size):
        batch = reviews[batch_start: batch_start + batch_size]

        review_lines = []
        for i, r in enumerate(batch):
            text = r.get("text", "")[:200]
            review_lines.append(f"[{i}] ★{r.get('rating', 0)} | {text}")

        reviews_block = "\n".join(review_lines)

        prompt = f"""Classify each review below into EXACTLY ONE of these themes:
{themes_desc}

If a review doesn't clearly fit any theme, classify it as "Other".

Reviews:
{reviews_block}

Return ONLY valid JSON (no markdown, no explanation):
[{{"review_index": 0, "theme": "Theme Label"}}, ...]"""

        try:
            response = client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1500,
            )

            raw = response.choices[0].message.content.strip()

            # Parse JSON — handle possible markdown wrapping
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            assignments = json.loads(raw)

            # Apply theme assignments
            for assignment in assignments:
                idx = assignment.get("review_index", -1)
                theme = assignment.get("theme", "Other")

                # Validate theme label
                if theme not in theme_labels:
                    theme = "Other"

                if 0 <= idx < len(batch):
                    review_copy = batch[idx].copy()
                    review_copy["theme"] = theme
                    classified.append(review_copy)

        except (json.JSONDecodeError, Exception) as e:
            print(f"[Grouper] Batch classification failed: {e}")
            # Fallback: assign "Other" to all in batch
            for r in batch:
                review_copy = r.copy()
                review_copy["theme"] = "Other"
                classified.append(review_copy)

        print(f"[Grouper] Classified {len(classified)}/{len(reviews)} reviews")

    # Merge small themes: if "Other" is large, keep it; otherwise distribute
    theme_counts = {}
    for r in classified:
        t = r.get("theme", "Other")
        theme_counts[t] = theme_counts.get(t, 0) + 1

    print(f"[Grouper] Theme distribution:")
    for t, c in sorted(theme_counts.items(), key=lambda x: -x[1]):
        pct = c / len(classified) * 100 if classified else 0
        print(f"  • {t}: {c} reviews ({pct:.1f}%)")

    return classified


if __name__ == "__main__":
    test_reviews = [
        {"rating": 1, "text": "App crashes every time"},
        {"rating": 5, "text": "Love the mutual fund tracking"},
        {"rating": 2, "text": "Support team is unresponsive"},
    ]
    test_themes = [
        {"label": "App Stability", "description": "Crashes and performance issues"},
        {"label": "Investment Features", "description": "MF and SIP tracking"},
        {"label": "Customer Support", "description": "Response time and quality"},
    ]
    result = assign_themes(test_reviews, test_themes)
    for r in result:
        print(f"  {r['theme']}: {r['text'][:50]}")
