import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import List, Dict
import os
import config

def fetch_apple_reviews(app_id: str = None, weeks_back: int = None, max_pages: int = 10) -> List[Dict]:
    """
    Fetch reviews from the Apple App Store RSS feed for the given app ID.
    Limits to the last `weeks_back` weeks and `max_pages` pages (50 reviews per page).
    """
    app_id = app_id or config.APPLE_APP_ID
    weeks_back = weeks_back or config.WEEKS_BACK
    cutoff_date = datetime.now() - timedelta(weeks=weeks_back)

    all_reviews: List[Dict] = []
    
    # Apple RSS feed provides up to 10 pages, each with 50 reviews.
    for page in range(1, max_pages + 1):
        url = f"https://itunes.apple.com/in/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
        
        try:
            req = urllib.request.Request(
                url, 
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            print(f"[Apple] Failed to fetch page {page}: {e}")
            break

        feed = data.get("feed", {})
        entries = feed.get("entry", [])
        
        # In case of empty feed or single entry
        if not entries:
            break
        if isinstance(entries, dict):
            entries = [entries]

        for entry in entries:
            # Skip the metadata entry that doesn't have a rating
            if "im:rating" not in entry:
                continue

            try:
                # Format: 2024-03-23T04:25:31-07:00
                date_str = entry.get("updated", {}).get("label", "")
                # Simple parsing for ISO-like strings
                # Strip timezone suffix to be safe
                clean_date = date_str.split("T")[0]
                review_date = datetime.strptime(clean_date, "%Y-%m-%d")
            except (ValueError, TypeError):
                review_date = datetime.now()

            if review_date < cutoff_date:
                # Once we hit reviews older than the cutoff, we can stop
                continue

            all_reviews.append({
                "source": "apple",
                "id": entry.get("id", {}).get("label", ""),
                "rating": int(entry.get("im:rating", {}).get("label", "0")),
                "title": entry.get("title", {}).get("label", ""),
                "text": entry.get("content", {}).get("label", ""),
                "date": review_date.strftime("%Y-%m-%d"),
                "author": entry.get("author", {}).get("name", {}).get("label", "Anonymous"),
            })

    print(f"[Apple] Fetched {len(all_reviews)} reviews from {max_pages} pages.")
    return all_reviews

if __name__ == "__main__":
    # Test fetch
    reviews = fetch_apple_reviews()
    if reviews:
        print(f"Sample: {reviews[0]['title']} ({reviews[0]['rating']}★) - {reviews[0]['date']}")
