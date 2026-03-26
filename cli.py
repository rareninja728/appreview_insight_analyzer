import typer
import sys
import os
from typing import Optional
from datetime import datetime

# Add the project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.orchestrator import run_weekly_pulse
from src.ingestion.apple_reviews import fetch_apple_reviews
from src.ingestion.google_reviews import fetch_google_reviews
from src.ingestion.pii_stripper import strip_pii_from_reviews
from src.analysis.theme_generator import generate_themes
from src.analysis.review_grouper import assign_themes
from src.report.note_builder import build_weekly_note, save_note
from src.report.email_drafter import draft_and_send

import pandas as pd
import json

app = typer.Typer(help="INDmoney Review Pulse CLI — Turn app reviews into weekly insights.")

@app.command()
def fetch(
    output: str = typer.Option("reviews_cleaned.csv", "--output", "-o", help="Output filename in data/processed/"),
    weeks: int = typer.Option(config.WEEKS_BACK, "--weeks", "-w", help="Number of weeks to look back")
):
    """Fetch and clean reviews from App Store and Play Store."""
    typer.echo("Phase 1: Fetching Reviews...")
    config.WEEKS_BACK = weeks
    
    apple = fetch_apple_reviews()
    google = fetch_google_reviews()
    all_reviews = apple + google
    
    if not all_reviews:
        typer.echo("FAILED: No reviews fetched. Check network/API access.")
        raise typer.Exit(code=1)
    
    typer.echo(f"Stripping PII from {len(all_reviews)} reviews...")
    clean = strip_pii_from_reviews(all_reviews)
    
    df = pd.DataFrame(clean)
    out_path = os.path.join(config.DATA_PROCESSED_DIR, output)
    df.to_csv(out_path, index=False)
    
    # Also save JSON
    json_path = out_path.replace(".csv", ".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2)
        
    typer.echo(f"SUCCESS! Saved {len(clean)} reviews to {out_path}")

@app.command()
def analyze(
    input_file: str = typer.Option("reviews_cleaned.csv", "--input", "-i", help="Input cleaned reviews file"),
    output: str = typer.Option("reviews_grouped.csv", "--output", "-o", help="Output grouped reviews file")
):
    """Discover themes and classify reviews using Groq LLM."""
    in_path = os.path.join(config.DATA_PROCESSED_DIR, input_file)
    if not os.path.exists(in_path):
        typer.echo(f"FAILED: Input file not found: {in_path}")
        raise typer.Exit(code=1)
    
    typer.echo("Phase 2: Generating Themes via Groq LLM...")
    if in_path.endswith(".csv"):
        df = pd.read_csv(in_path)
        reviews = df.to_dict("records")
    else:
        with open(in_path, "r", encoding="utf-8") as f:
            reviews = json.load(f)
            
    themes = generate_themes(reviews)
    typer.echo(f"Discovered {len(themes)} themes.")
    
    typer.echo("Classifying reviews...")
    grouped = assign_themes(reviews, themes)
    
    out_path = os.path.join(config.DATA_PROCESSED_DIR, output)
    pd.DataFrame(grouped).to_csv(out_path, index=False)
    typer.echo(f"SUCCESS! Saved grouped reviews to {out_path}")

@app.command()
def report(
    input_file: str = typer.Option("reviews_grouped.csv", "--input", "-i", help="Input grouped reviews file"),
    week: Optional[str] = typer.Option(None, "--week", help="Week label (e.g. W12-2026)")
):
    """Build the weekly one-page pulse note."""
    in_path = os.path.join(config.DATA_PROCESSED_DIR, input_file)
    if not os.path.exists(in_path):
        typer.echo(f"FAILED: Input file not found: {in_path}")
        raise typer.Exit(code=1)
        
    df = pd.DataFrame(pd.read_csv(in_path))
    grouped = df.to_dict("records")
    
    typer.echo("Phase 3: Building Weekly Pulse Note...")
    note = build_weekly_note(grouped, week)
    note_path = save_note(note)
    
    typer.echo(f"SUCCESS! Note saved to: {note_path}")
    typer.echo("-" * 40)
    typer.echo(note["markdown"][:500] + "...")
    typer.echo("-" * 40)

@app.command()
def run(
    week: Optional[str] = typer.Option(None, "--week", help="Target week (e.g. W12-2026)"),
    skip_email: bool = typer.Option(False, "--skip-email", help="Skip sending email")
):
    """Run the entire end-to-end pipeline (fetch -> analyze -> report -> email)."""
    typer.echo("Starting Full Pipeline Cycle...")
    results = run_weekly_pulse(target_week=week, skip_email=skip_email)
    
    if "error" in results:
        typer.echo(f"FAILED: Pipeline failed: {results['error']}")
        raise typer.Exit(code=1)
    
    typer.echo("SUCCESS: Pipeline Completed Successfully!")

@app.command()
def version():
    """Show the version of the tool."""
    typer.echo("INDmoney Review Pulse CLI v1.0.0")

if __name__ == "__main__":
    app()
