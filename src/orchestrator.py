import json
import os
import sys
from datetime import datetime
import logging
import pandas as pd
import traceback

# ── Step 3: Deep Logging Configuration ──────────────────────
logger = logging.getLogger("INDmoney-Orchestrator")

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
    """Run the complete weekly pulse pipeline with robust logging."""
    logger.info("🚀 Starting INDmoney Weekly Review Pulse Orchestration")
    
    results = {"status": "started", "logs": []}

    try:
        # ── Phase 1: Ingest Reviews ───────────────────────────
        logger.info("📡 Phase 1: Fetching Raw Reviews from Stores...")
        apple_reviews = fetch_apple_reviews()
        google_reviews = fetch_google_reviews()
        
        all_reviews = apple_reviews + google_reviews
        logger.info(f"   Collected {len(all_reviews)} total reviews (Apple: {len(apple_reviews)}, Google: {len(google_reviews)})")

        if not all_reviews:
            logger.error("❌ No reviews found. Pipeline halted.")
            return {"status": "error", "message": "No reviews fetched"}

        # ── PII Stripping ─────────────────────────────────────
        logger.info("🛡️ Phase 1b: Redacting PII from Review Data...")
        clean_reviews = strip_pii_from_reviews(all_reviews)

        # Save cleaned reviews to CSV
        df = pd.DataFrame(clean_reviews)
        csv_path = os.path.join(config.DATA_PROCESSED_DIR, "reviews_cleaned.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8")
        logger.info(f"   Cleaned data saved to {csv_path}")

        results["reviews_count"] = len(clean_reviews)
        results["csv_path"] = csv_path

        # ── Phase 2: Generate Themes ──────────────────────────
        logger.info("🧠 Phase 2: Identifying Themes via Groq AI...")
        themes = generate_themes(clean_reviews)
        logger.info(f"   AI identified {len(themes)} key themes.")

        logger.info("🏷️ Phase 2b: Classifying Reviews into Strategic Themes...")
        grouped_reviews = assign_themes(clean_reviews, themes)

        # Save grouped reviews
        grouped_df = pd.DataFrame(grouped_reviews)
        grouped_csv = os.path.join(config.DATA_PROCESSED_DIR, "reviews_grouped.csv")
        grouped_df.to_csv(grouped_csv, index=False, encoding="utf-8")
        logger.info(f"   Thematic data saved to {grouped_csv}")

        results["themes"] = themes
        results["grouped_csv"] = grouped_csv

        # ── Phase 3: Build Weekly Note ────────────────────────
        logger.info("📝 Phase 3: Building Executive Weekly Note...")
        note = build_weekly_note(grouped_reviews, target_week)
        note_path = save_note(note)
        logger.info(f"   Weekly pulse report built and saved: {note_path}")

        results["note"] = note
        results["note_path"] = note_path

        # ── Phase 4: Draft & Send Email ───────────────────────
        if skip_email:
            logger.info("✉️ Phase 4: Skipping Actual Email Send (Dry-run mode).")
            results["email"] = {"sent": False, "message": "Skipped per skip_email parameter"}
        else:
            logger.info("✉️ Phase 4: Composing and Dispatching Pulse Email...")
            email_result = draft_and_send(note)
            results["email"] = email_result
            if email_result.get("sent"):
                logger.info(f"   ✅ Email successfully sent to {email_result.get('to')}")
            else:
                logger.warning("   ⚠️ Email delivery failed. Backup draft saved.")

        results["status"] = "success"
        logger.info("⭐ INDmoney Weekly Pulse Pipeline Successfully Completed.")
        return results

    except Exception as e:
        logger.error(f"💥 CRITICAL PIPELINE FAILURE: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }


if __name__ == "__main__":
    import argparse
    # Ensure logging shows in console when run directly
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(description="INDmoney Weekly Review Pulse")
    parser.add_argument("--week", type=str, help="Target week (e.g. W12-2026)")
    parser.add_argument("--skip-email", action="store_true", help="Skip email sending")
    args = parser.parse_args()

    run_weekly_pulse(target_week=args.week, skip_email=args.skip_email)
