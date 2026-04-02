from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import os
import sys
import pandas as pd
from typing import Optional, List, Dict
import json
import logging
import traceback

# ── Step 3: Deep Logging Configuration ──────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("INDmoney-API")

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

app = FastAPI(title="INDmoney Review Pulse API")

# ── Step 7: Verify CORS & Public Exposure ───────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific domains for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# ── API Endpoints ───────────────────────────────────────────

@app.get("/api/config")
async def get_config():
    """Get the current configuration."""
    return {
        "groq_api_key_set": bool(config.GROQ_API_KEY),
        "email_address": config.EMAIL_ADDRESS,
        "weeks_back": config.WEEKS_BACK,
        "max_themes": config.MAX_THEMES,
        "note_max_words": config.NOTE_MAX_WORDS,
        "backend_url": config.BACKEND_URL
    }

# ── Step 2: Dedicated Test Endpoint ───────────────────────
@app.get("/api/test-email")
async def test_email_endpoint():
    """Quickly verify SMTP connectivity."""
    logger.info("Manual trigger: /api/test-email hit")
    try:
        # Create a dummy note for testing
        test_note = {
            "week_label": "PROD-TEST",
            "markdown": "# Production SMTP Test\n\nIf you see this, your SMTP configuration is working perfectly.",
            "metadata": {"top_themes": ["Test"], "total_reviews": 1}
        }
        logger.info(f"Attempting to send test email to {config.EMAIL_ADDRESS}")
        result = draft_and_send(test_note)
        
        if result["sent"]:
            return {"status": "success", "message": f"Test email sent to {config.EMAIL_ADDRESS}"}
        else:
            return {"status": "error", "message": "Draft saved but email failed to send. Check logs.", "draft": result["draft_path"]}
    except Exception as e:
        logger.error(f"Test email failed: {str(e)}", exc_info=True)
        return {"status": "error", "detail": str(e), "traceback": traceback.format_exc()}

# ── Step 8: Manual Trigger Endpoint ───────────────────────
@app.post("/api/run-weekly-pulse")
async def trigger_pipeline(data: Dict = Body(default={})):
    """Full pipeline execution with deep logging."""
    logger.info(f"Manual trigger: /api/run-weekly-pulse hit with data: {data}")
    try:
        if "weeks_back" in data:
            config.WEEKS_BACK = int(data["weeks_back"])
        if "email" in data:
            config.EMAIL_ADDRESS = data["email"]
            
        logger.info(f"Starting pipeline orchestration for {config.WEEKS_BACK} weeks...")
        results = run_weekly_pulse()
        
        logger.info(f"Pipeline finished with status: {results.get('status')}")
        return results
    except Exception as e:
        logger.error(f"Pipeline failed significantly: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"error": str(e), "traceback": traceback.format_exc()})

@app.post("/api/run_pipeline")
async def run_pipeline_legacy(data: Dict = Body(default={})):
    """Legacy endpoint wrapper."""
    return await trigger_pipeline(data)

@app.get("/api/health")
async def health():
    """Health check endpoint for monitoring."""
    return {"status": "ok", "message": "Backend is healthy and reachable"}

# ── Serve Frontend ──────────────────────────────────────────
@app.get("/")
async def homepage():
    return JSONResponse({"status": "active", "service": "INDmoney API", "docs": "/docs"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    # Step 7: Bind to 0.0.0.0 for production exposure
    logger.info(f"🚀 Starting Production-Ready Server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
