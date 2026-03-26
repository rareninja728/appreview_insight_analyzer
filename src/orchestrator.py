"""
Orchestrator — End-to-end pipeline for the INDmoney Weekly Review Pulse.
Ties together ingestion → PII stripping → theme generation → note building → email.
"""

import json
import os
import sys
from datetime import datetime

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config

from src.ingestion.apple_reviews import fetch_apple_reviews
from src.ingestion.google_reviews import fetch_google_reviews
from src.ingestion.pii_stripper import strip_pii_from_reviews
from src.analysis.theme_generator import generate_themes
from src.analysis.review_grouper import assign_themes
from src.report.note_builder import build_weekly_note, save_note
from src.report.email_drafter import draft_and_send


def run_weekly_pulse(target_week: str = None, skip_email: bool = False) -> dict:
    """
    Run the complete weekly pulse pipeline.

    Args:
        target_week: Optional week label (e.g. "W12-2026"), defaults to latest
        skip_email: If True, skip email sending (still saves draft)

    Returns:
        Dict with pipeline results
    """
    print("=" * 60)
    print("INDmoney Weekly Review Pulse - Pipeline Starting")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = {}

    # ── Phase 1: Ingest Reviews ───────────────────────────
    print("\nPhase 1: Fetching Reviews...")
    apple_reviews = fetch_apple_reviews()
    google_reviews = fetch_google_reviews()

    all_reviews = apple_reviews + google_reviews
    print(f"  Total raw reviews: {len(all_reviews)}")

    if not all_reviews:
        print("No reviews fetched. Check network/API access.")
        return {"error": "No reviews fetched"}

    # ── PII Stripping ─────────────────────────────────────
    print("\nPhase 1b: Stripping PII...")
    clean_reviews = strip_pii_from_reviews(all_reviews)

    # Save cleaned reviews to CSV
    df = pd.DataFrame(clean_reviews)
    csv_path = os.path.join(config.DATA_PROCESSED_DIR, "reviews_cleaned.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"  Saved cleaned reviews: {csv_path}")

    # Also save as JSON
    json_path = os.path.join(config.DATA_PROCESSED_DIR, "reviews_cleaned.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(clean_reviews, f, indent=2, ensure_ascii=False)

    results["reviews_count"] = len(clean_reviews)
    results["csv_path"] = csv_path

    # ── Phase 2: Generate Themes ──────────────────────────
    print("\nPhase 2: Generating Themes via Groq LLM...")
    themes = generate_themes(clean_reviews)

    print("\nPhase 2b: Classifying Reviews into Themes...")
    grouped_reviews = assign_themes(clean_reviews, themes)

    # Save grouped reviews
    grouped_df = pd.DataFrame(grouped_reviews)
    grouped_csv = os.path.join(config.DATA_PROCESSED_DIR, "reviews_grouped.csv")
    grouped_df.to_csv(grouped_csv, index=False, encoding="utf-8")

    results["themes"] = themes
    results["grouped_csv"] = grouped_csv

    # ── Phase 3: Build Weekly Note ────────────────────────
    print("\nPhase 3: Building Weekly Pulse Note...")
    note = build_weekly_note(grouped_reviews, target_week)
    note_path = save_note(note)

    results["note"] = note
    results["note_path"] = note_path

    # ── Phase 4: Draft & Send Email ───────────────────────
    print("\nPhase 4: Drafting Email...")
    email_result = draft_and_send(note)
    results["email"] = email_result

    # ── Summary ───────────────────────────────────────────
    print("\n" + "=" * 60)
    print("Pipeline Complete!")
    print(f"   Reviews analyzed: {results['reviews_count']}")
    print(f"   Themes found: {len(themes)}")
    print(f"   Weekly note: {note_path}")
    print(f"   Email sent: {email_result.get('sent', False)}")
    print(f"   Email draft: {email_result.get('draft_path', 'N/A')}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="INDmoney Weekly Review Pulse")
    parser.add_argument("--week", type=str, help="Target week (e.g. W12-2026)")
    parser.add_argument("--skip-email", action="store_true", help="Skip email sending")
    args = parser.parse_args()

    run_weekly_pulse(target_week=args.week, skip_email=args.skip_email)
