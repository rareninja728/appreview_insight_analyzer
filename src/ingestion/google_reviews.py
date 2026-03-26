"""
Google Play Store Review Fetcher.
Uses the `google-play-scraper` package (public API, no login required).
"""

from datetime import datetime, timedelta
from typing import List, Dict
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import config

try:
    from google_play_scraper import Sort, reviews as gplay_reviews
except ImportError:
    gplay_reviews = None
    Sort = None
    print("[Google] google-play-scraper not installed. Run: pip install google-play-scraper")


def fetch_google_reviews(
    package_name: str = None,
    weeks_back: int = None,
    count: int = 500,
) -> List[Dict]:
    """
    Fetch recent reviews from Google Play Store.

    Args:
        package_name: Google Play package name (defaults to config.GOOGLE_PACKAGE)
        weeks_back: Number of weeks to look back (defaults to config.WEEKS_BACK)
        count: Maximum number of reviews to request per batch

    Returns:
        List of review dicts with keys: source, rating, title, text, date
    """
    if gplay_reviews is None:
        print("[Google] Skipping — google-play-scraper not available")
        return []

    package_name = package_name or config.GOOGLE_PACKAGE
    weeks_back = weeks_back or config.WEEKS_BACK
    cutoff_date = datetime.now() - timedelta(weeks=weeks_back)

    all_reviews: List[Dict] = []
    continuation_token = None

    # Fetch in batches (the scraper returns up to `count` per call)
    for batch_num in range(5):  # max 5 batches = up to 2500 reviews
        try:
            result, continuation_token = gplay_reviews(
                package_name,
                lang="en",
                country="in",
                sort=Sort.NEWEST,
                count=count,
                continuation_token=continuation_token,
            )
        except Exception as e:
            print(f"[Google] Batch {batch_num + 1} fetch failed: {e}")
            break

        if not result:
            break

        reached_cutoff = False
        for entry in result:
            review_date = entry.get("at")
            if isinstance(review_date, datetime):
                if review_date < cutoff_date:
                    reached_cutoff = True
                    continue
                date_str = review_date.strftime("%Y-%m-%d")
            else:
                date_str = str(review_date) if review_date else ""

            review = {
                "source": "google",
                "rating": int(entry.get("score", 0)),
                "title": "",  # Google Play reviews don't always have titles
                "text": entry.get("content", ""),
                "date": date_str,
            }
            all_reviews.append(review)

        if reached_cutoff or continuation_token is None:
            break

    print(f"[Google] Fetched {len(all_reviews)} reviews (last {weeks_back} weeks)")
    return all_reviews


if __name__ == "__main__":
    reviews = fetch_google_reviews()
    print(f"Total Google reviews: {len(reviews)}")
    for r in reviews[:3]:
        print(f"  ★{r['rating']} | {r['date']} | {r['text'][:60]}")
