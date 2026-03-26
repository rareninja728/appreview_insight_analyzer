import json
import os
import pandas as pd
from apple_reviews import fetch_apple_reviews
from google_reviews import fetch_google_reviews
from pii_stripper import strip_pii_from_reviews
import config

def main():
    print("Initialising Phase 1: Review Ingestion & PII Redaction")
    print("-" * 50)
    
    # 1. Fetch Apple App Store reviews
    print("\n[Step 1/4] Fetching Apple reviews...")
    apple_reviews = fetch_apple_reviews()
    
    # 2. Fetch Google Play Store reviews
    print("\n[Step 2/4] Fetching Google reviews...")
    google_reviews = fetch_google_reviews()
    
    all_reviews = apple_reviews + google_reviews
    print(f"\n[Step 3/4] Totals: {len(all_reviews)} raw reviews collected (Apple: {len(apple_reviews)}, Google: {len(google_reviews)}).")
    
    if not all_reviews:
        print("No reviews found. Check app IDs or network connection.")
        return

    # 3. Strip PII
    print("\n[Step 4/4] Redacting IDs, emails, phones, Aadhaar, PAN... (PII Stripping)")
    cleaned_reviews = strip_pii_from_reviews(all_reviews)
    
    # 4. Save results
    # Use config paths
    os.makedirs(config.DATA_PROCESSED_DIR, exist_ok=True)
    
    csv_path = os.path.join(config.DATA_PROCESSED_DIR, "reviews_cleaned.csv")
    json_path = os.path.join(config.DATA_PROCESSED_DIR, "reviews_cleaned.json")
    
    # Save as CSV
    pd.DataFrame(cleaned_reviews).to_csv(csv_path, index=False)
    
    # Save as JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_reviews, f, indent=4, ensure_ascii=False)
        
    print("-" * 50)
    print("\nPhase 1 successfully completed!")
    print(f"Processed reviews saved to: {config.DATA_PROCESSED_DIR}")
    print(f"Files: reviews_cleaned.csv, reviews_cleaned.json")

if __name__ == "__main__":
    main()
