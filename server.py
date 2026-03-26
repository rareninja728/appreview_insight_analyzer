from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import os
import sys
import pandas as pd
from typing import Optional, List, Dict
import json
import logging

# Add project root to sys path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.orchestrator import run_weekly_pulse
from src.ingestion.apple_reviews import fetch_apple_reviews
from src.ingestion.google_reviews import fetch_google_reviews
from src.ingestion.pii_stripper import strip_pii_from_reviews
from src.analysis.theme_generator import generate_themes
from src.analysis.review_grouper import assign_themes
from src.report.note_builder import build_weekly_note, save_note
from src.report.email_drafter import draft_and_send, compose_email, send_email

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="INDmoney Review Pulse API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Endpoints ───────────────────────────────────────────

@app.get("/api/config")
async def get_config():
    """Get the current configuration."""
    return {
        "groq_api_key_set": bool(config.GROQ_API_KEY),
        "email_address": config.EMAIL_ADDRESS,
        "weeks_back": config.WEEKS_BACK,
        "max_themes": config.MAX_THEMES,
        "note_max_words": config.NOTE_MAX_WORDS
    }

@app.post("/api/config")
async def update_config(data: Dict = Body(...)):
    """Update configuration temporarily in memory/env."""
    if "groq_api_key" in data:
        config.GROQ_API_KEY = data["groq_api_key"]
        os.environ["GROQ_API_KEY"] = data["groq_api_key"]
    if "email_address" in data:
        config.EMAIL_ADDRESS = data["email_address"]
    if "email_app_password" in data:
        config.EMAIL_APP_PASSWORD = data["email_app_password"]
    if "weeks_back" in data:
        config.WEEKS_BACK = int(data["weeks_back"])
    
    return {"status": "Updated successfully"}

@app.get("/api/reviews")
async def get_reviews(limit: int = 100):
    """Fetch reviews from files if available, else return empty."""
    path = os.path.join(config.DATA_PROCESSED_DIR, "reviews_cleaned.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        return df.head(limit).to_dict("records")
    return []

@app.post("/api/fetch")
async def fetch_reviews_api():
    """Trigger review fetching and cleaning process."""
    try:
        logger.info("Fetching reviews...")
        apple = fetch_apple_reviews()
        google = fetch_google_reviews()
        all_reviews = apple + google
        
        if not all_reviews:
            raise HTTPException(status_code=404, detail="No reviews found")
            
        clean = strip_pii_from_reviews(all_reviews)
        
        # Save to CSV
        df = pd.DataFrame(clean)
        csv_path = os.path.join(config.DATA_PROCESSED_DIR, "reviews_cleaned.csv")
        df.to_csv(csv_path, index=False)
        
        return {
            "status": "success",
            "count": len(clean),
            "apple_count": len(apple),
            "google_count": len(google)
        }
    except Exception as e:
        logger.error(f"Fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_reviews_api():
    """Trigger theme analysis and classification."""
    try:
        path = os.path.join(config.DATA_PROCESSED_DIR, "reviews_cleaned.csv")
        if not os.path.exists(path):
            raise HTTPException(status_code=400, detail="Reviews not fetched yet. Run fetch first.")
            
        df = pd.read_csv(path)
        reviews = df.to_dict("records")
        
        logger.info("Generating themes via LLM...")
        themes = generate_themes(reviews)
        
        logger.info("Classifying reviews into themes...")
        grouped = assign_themes(reviews, themes)
        
        # Save grouped reviews
        out_path = os.path.join(config.DATA_PROCESSED_DIR, "reviews_grouped.csv")
        pd.DataFrame(grouped).to_csv(out_path, index=False)
        
        return {
            "status": "success",
            "themes": themes,
            "grouped_count": len(grouped)
        }
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/report")
async def build_report_api():
    """Generate the weekly pulse note."""
    try:
        path = os.path.join(config.DATA_PROCESSED_DIR, "reviews_grouped.csv")
        if not os.path.exists(path):
            raise HTTPException(status_code=400, detail="Reviews not analyzed yet. Run analyze first.")
            
        df = pd.read_csv(path)
        grouped = df.to_dict("records")
        
        logger.info("Building note...")
        note = build_weekly_note(grouped)
        note_path = save_note(note)
        
        return {
            "status": "success",
            "note": note,
            "path": note_path
        }
    except Exception as e:
        logger.error(f"Report build failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/email")
async def send_email_api():
    """Draft and send/save the email pulse."""
    try:
        path = os.path.join(config.DATA_PROCESSED_DIR, "reviews_grouped.csv")
        if not os.path.exists(path):
            raise HTTPException(status_code=400, detail="Reviews not analyzed yet.")
            
        df = pd.read_csv(path)
        grouped = df.to_dict("records")
        note = build_weekly_note(grouped) # Ensure we have latest note
        
        logger.info("Drafting/Sending email...")
        result = draft_and_send(note)
        
        return {
            "status": "success",
            "sent": result["sent"],
            "draft_path": result["draft_path"],
            "recipient": result["to"]
        }
    except Exception as e:
        logger.error(f"Email failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run_pipeline")
async def run_pipeline_api():
    """Trigger the full one-click pipeline."""
    try:
        logger.info("Running full pipeline...")
        results = run_weekly_pulse()
        return results
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ── Serve Frontend ──────────────────────────────────────────

# If frontend folder exists, serve index.html as homepage
@app.get("/")
async def homepage():
    return FileResponse(os.path.join(os.path.dirname(__file__), "frontend", "index.html"))

# Mount static files (JS, CSS)
if os.path.exists(os.path.join(os.path.dirname(__file__), "frontend")):
    app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "frontend")), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
