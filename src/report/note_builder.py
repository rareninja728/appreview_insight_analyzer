"""
Note Builder — Generates a ≤250-word weekly pulse from grouped reviews.
Uses Groq LLM to select best quotes and generate action ideas.
"""

import json
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import config

from groq import Groq


def _get_client() -> Groq:
    """Initialize Groq client."""
    return Groq(api_key=config.GROQ_API_KEY)


def _get_week_label(date_str: str) -> str:
    """Convert date string to week label like 'W12-2026'."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        week_num = dt.isocalendar()[1]
        return f"W{week_num:02d}-{dt.year}"
    except (ValueError, TypeError):
        return "Unknown"


def _get_week_range(target_week: str = None) -> tuple:
    """Get the start and end dates for a week label or latest week."""
    now = datetime.now()
    if target_week:
        # Parse W12-2026 format
        parts = target_week.replace("W", "").split("-")
        week_num = int(parts[0])
        year = int(parts[1])
        # Calculate Monday of that week
        jan1 = datetime(year, 1, 1)
        start = jan1 + timedelta(weeks=week_num - 1, days=-jan1.weekday())
    else:
        # Latest complete week (Mon–Sun before today)
        start = now - timedelta(days=now.weekday() + 7)

    end = start + timedelta(days=6)
    return start, end


def _select_best_quotes(
    theme_reviews: Dict[str, List[Dict]],
    top_themes: List[str],
) -> List[Dict]:
    """Use Groq to pick the most impactful quote per theme."""
    client = _get_client()
    quotes = []

    for theme in top_themes:
        reviews = theme_reviews.get(theme, [])
        if not reviews:
            continue

        # Take up to 10 reviews for Groq to pick from
        candidates = reviews[:10]
        reviews_text = "\n".join(
            [f"[{i}] ★{r.get('rating', 0)} | {r.get('text', '')[:200]}"
             for i, r in enumerate(candidates)]
        )

        prompt = f"""From these reviews under the theme "{theme}", pick the single most 
impactful quote. It should be specific, actionable, and representative.

Reviews:
{reviews_text}

Return ONLY valid JSON:
{{"index": 0, "quote": "exact quote text"}}"""

        try:
            response = client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=200,
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            result = json.loads(raw)
            idx = result.get("index", 0)
            if 0 <= idx < len(candidates):
                quotes.append({
                    "theme": theme,
                    "quote": result.get("quote", candidates[idx].get("text", "")[:150]),
                    "rating": candidates[idx].get("rating", 0),
                })
            else:
                quotes.append({
                    "theme": theme,
                    "quote": candidates[0].get("text", "")[:150],
                    "rating": candidates[0].get("rating", 0),
                })
        except Exception as e:
            print(f"[Note] Quote selection failed for {theme}: {e}")
            if candidates:
                quotes.append({
                    "theme": theme,
                    "quote": candidates[0].get("text", "")[:150],
                    "rating": candidates[0].get("rating", 0),
                })

    return quotes[:3]


def _generate_actions(
    theme_reviews: Dict[str, List[Dict]],
    top_themes: List[str],
) -> List[str]:
    """Use Groq to generate 3 concrete action ideas."""
    client = _get_client()

    summaries = []
    for theme in top_themes:
        reviews = theme_reviews.get(theme, [])
        sample_texts = [r.get("text", "")[:100] for r in reviews[:5]]
        summaries.append(f"**{theme}** ({len(reviews)} reviews):\n" + "\n".join(sample_texts))

    context = "\n\n".join(summaries)

    prompt = f"""You are a product strategist for INDmoney (a personal finance & investment app).
Given the top user feedback themes and sample reviews below, suggest exactly 3 concrete, 
actionable improvement ideas.

Each idea should be:
- 1 sentence
- Specific and implementable
- Directly addresses the user pain point

Themes & Reviews:
{context}

Return ONLY valid JSON:
{{"actions": ["Action 1", "Action 2", "Action 3"]}}"""

    try:
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=300,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        result = json.loads(raw)
        return result.get("actions", [])[:3]
    except Exception as e:
        print(f"[Note] Action generation failed: {e}")
        return [
            "Investigate top-mentioned issues in upcoming sprint",
            "Review support ticket SLAs for improvement",
            "Survey power users for feature prioritization",
        ]


def _star_display(rating: int) -> str:
    """Convert rating to star emoji display."""
    return "★" * rating + "☆" * (5 - rating)


def build_weekly_note(
    grouped_reviews: List[Dict],
    target_week: str = None,
) -> Dict:
    """
    Build the ≤250-word weekly pulse note.

    Args:
        grouped_reviews: List of review dicts with 'theme', 'date' keys
        target_week: Optional week label (e.g. "W12-2026"), defaults to latest week

    Returns:
        Dict with keys: week_label, markdown, metadata
    """
    # Determine target week
    if not target_week:
        # Find the most recent week in the data
        week_labels = [_get_week_label(r.get("date", "")) for r in grouped_reviews]
        week_counter = Counter(week_labels)
        week_counter.pop("Unknown", None)
        if week_counter:
            target_week = max(week_counter.keys())
        else:
            target_week = f"W{datetime.now().isocalendar()[1]:02d}-{datetime.now().year}"

    # Filter reviews for the target week (or use all if week filtering yields too few)
    week_reviews = [
        r for r in grouped_reviews
        if _get_week_label(r.get("date", "")) == target_week
    ]
    if len(week_reviews) < 10:
        # Not enough reviews for just one week — use all available
        week_reviews = grouped_reviews

    total_count = len(week_reviews)
    apple_count = sum(1 for r in week_reviews if r.get("source") == "apple")
    google_count = sum(1 for r in week_reviews if r.get("source") == "google")

    # Group by theme
    theme_reviews: Dict[str, List[Dict]] = {}
    for r in week_reviews:
        theme = r.get("theme", "Other")
        theme_reviews.setdefault(theme, []).append(r)

    # Top 3 themes by count
    theme_counts = {t: len(revs) for t, revs in theme_reviews.items()}
    top_themes = sorted(theme_counts, key=lambda t: -theme_counts[t])[:3]

    # Get week date range
    week_start, week_end = _get_week_range(target_week)
    date_range = f"{week_start.strftime('%b %d')} – {week_end.strftime('%b %d')}"

    # Select quotes & actions via LLM
    quotes = _select_best_quotes(theme_reviews, top_themes)
    actions = _generate_actions(theme_reviews, top_themes)

    # ── Build Markdown ─────────────────────────────────────
    lines = [
        f"# 📊 INDmoney Weekly Review Pulse",
        f"**Week:** {target_week} ({date_range})",
        f"**Reviews Analyzed:** {total_count} (Apple: {apple_count}, Google: {google_count})",
        "",
        "---",
        "",
        "## 🔥 Top Themes",
    ]

    for i, theme in enumerate(top_themes, 1):
        count = theme_counts[theme]
        pct = count / total_count * 100 if total_count else 0
        lines.append(f"{i}. **{theme}** — {pct:.0f}% of reviews ({count} mentions)")

    lines.extend(["", "## 💬 User Voices"])

    for q in quotes:
        stars = _star_display(q["rating"])
        lines.append(f'> "{q["quote"]}" — {stars}')
        lines.append("")

    lines.extend(["## 💡 Action Ideas"])

    for i, action in enumerate(actions, 1):
        lines.append(f"{i}. {action}")

    lines.extend([
        "",
        "---",
        f"*Generated from {total_count} public reviews · No PII included*",
    ])

    markdown = "\n".join(lines)

    # ── Word count check ───────────────────────────────────
    word_count = len(markdown.split())
    if word_count > config.NOTE_MAX_WORDS:
        print(f"[Note] Warning: {word_count} words exceeds {config.NOTE_MAX_WORDS} limit. Trimming quotes...")
        # Trim long quotes
        for q in quotes:
            if len(q["quote"].split()) > 20:
                q["quote"] = " ".join(q["quote"].split()[:20]) + "..."

    print(f"[Note] Built weekly pulse: {word_count} words, {len(top_themes)} themes")

    return {
        "week_label": target_week,
        "markdown": markdown,
        "metadata": {
            "total_reviews": total_count,
            "apple_count": apple_count,
            "google_count": google_count,
            "top_themes": top_themes,
            "theme_counts": theme_counts,
            "word_count": word_count,
        },
    }


def save_note(note: Dict, output_dir: str = None) -> str:
    """Save the weekly note as a Markdown file."""
    output_dir = output_dir or config.WEEKLY_NOTES_DIR
    os.makedirs(output_dir, exist_ok=True)

    filename = f"week_{note['week_label']}.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(note["markdown"])

    print(f"[Note] Saved to: {filepath}")
    return filepath


if __name__ == "__main__":
    # Quick test with dummy grouped data
    test_data = [
        {"source": "google", "rating": 1, "text": "App crashes daily", "date": "2026-03-20", "theme": "App Stability"},
        {"source": "apple", "rating": 5, "text": "Best SIP tracker", "date": "2026-03-19", "theme": "Investment Features"},
        {"source": "google", "rating": 2, "text": "No support response", "date": "2026-03-18", "theme": "Customer Support"},
    ]
    note = build_weekly_note(test_data)
    print(note["markdown"])
