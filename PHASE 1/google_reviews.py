from datetime import datetime, timedelta
from typing import List, Dict
import os
import config
from google_play_scraper import Sort, reviews as gplay_reviews

def fetch_google_reviews(package_name: str = None, weeks_back: int = None, count: int = 500) -> List[Dict]:
    """
    Fetch reviews from Google Play Store for the given package name.
    """
    package_name = package_name or config.GOOGLE_PACKAGE
    weeks_back = weeks_back or config.WEEKS_BACK
    cutoff_date = datetime.now() - timedelta(weeks=weeks_back)

    all_reviews: List[Dict] = []
    continuation_token = None

    # Fetch 500 reviews by 500 reviews, up to 5 times (2500 total)
    for batch_num in range(5):
        try:
            result, continuation_token = gplay_reviews(
                package_name, 
                lang="en", 
                country="in",
                sort=Sort.NEWEST, 
                count=count, 
                continuation_token=continuation_token
            )
        except Exception as e:
            print(f"[Google] Error fetching batch {batch_num}: {e}")
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
                date_str = str(review_date)
            
            all_reviews.append({
                "source": "google",
                "id": entry.get("reviewId", ""),
                "rating": int(entry.get("score", 0)),
                "title": "",  # Google Play scraper doesn't give a title field
                "text": entry.get("content", ""),
                "date": date_str,
                "author": entry.get("userName", "Anonymous"),
            })

        print(f"[Google] Batch {batch_num + 1} complete. Fetched {len(all_reviews)} total.")
        
        if reached_cutoff or continuation_token is None:
            break

    print(f"[Google] Total reviews fetched: {len(all_reviews)}")
    return all_reviews

if __name__ == "__main__":
    # Test fetch
    reviews = fetch_google_reviews()
    if reviews:
        print(f"Sample: {reviews[0]['text'][:50]}... ({reviews[0]['rating']}★) - {reviews[0]['date']}")
