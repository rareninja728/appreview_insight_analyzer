"""
Apple App Store Review Fetcher.
Uses Apple's public RSS/JSON feed — no login or scraping required.
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import List, Dict
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import config


def fetch_apple_reviews(
    app_id: str = None,
    weeks_back: int = None,
    max_pages: int = 10,
) -> List[Dict]:
    """
    Fetch recent reviews from the Apple App Store RSS feed.

    Args:
        app_id: Apple App Store app ID (defaults to config.APPLE_APP_ID)
        weeks_back: Number of weeks to look back (defaults to config.WEEKS_BACK)
        max_pages: Maximum number of RSS pages to fetch (each page ≈50 reviews)

    Returns:
        List of review dicts with keys: source, rating, title, text, date
    """
    app_id = app_id or config.APPLE_APP_ID
    weeks_back = weeks_back or config.WEEKS_BACK
    cutoff_date = datetime.now() - timedelta(weeks=weeks_back)

    all_reviews: List[Dict] = []

    for page in range(1, max_pages + 1):
        url = (
            f"https://itunes.apple.com/in/rss/customerreviews"
            f"/page={page}/id={app_id}/sortby=mostrecent/json"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            print(f"[Apple] Page {page} fetch failed: {e}")
            break

        entries = data.get("feed", {}).get("entry", [])
        if not entries:
            break

        for entry in entries:
            # Skip the app-metadata entry (has 'im:name' but no 'im:rating')
            if "im:rating" not in entry:
                continue

            try:
                review_date = datetime.strptime(
                    entry.get("updated", {}).get("label", ""),
                    "%Y-%m-%dT%H:%M:%S-07:00",
                )
            except (ValueError, TypeError):
                # Try alternate date format
                try:
                    date_str = entry.get("updated", {}).get("label", "")
                    # Strip timezone info and parse
                    review_date = datetime.fromisoformat(
                        date_str.replace("Z", "+00:00").split("+")[0]
                    )
                except (ValueError, TypeError):
                    review_date = datetime.now()

            if review_date < cutoff_date:
                continue

            review = {
                "source": "apple",
                "rating": int(entry.get("im:rating", {}).get("label", "0")),
                "title": entry.get("title", {}).get("label", ""),
                "text": entry.get("content", {}).get("label", ""),
                "date": review_date.strftime("%Y-%m-%d"),
            }
            all_reviews.append(review)

    print(f"[Apple] Fetched {len(all_reviews)} reviews (last {weeks_back} weeks)")
    return all_reviews


if __name__ == "__main__":
    reviews = fetch_apple_reviews()
    print(f"Total Apple reviews: {len(reviews)}")
    for r in reviews[:3]:
        print(f"  ★{r['rating']} | {r['date']} | {r['title'][:50]}")
