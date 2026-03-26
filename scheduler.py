import os
import sys
import subprocess
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Add project root to sys path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Scheduler")

RECIPIENT_EMAIL = "sugandhawankar123@gmail.com"

def run_pulse_job():
    """Executes the weekly pulse pipeline via CLI."""
    logger.info("--- Starting Scheduled Weekly Pulse Job ---")
    
    try:
        # Run the CLI command: python cli.py run
        # We pass the recipient email as an argument if needed, 
        # but the orchestrator usually uses config.EMAIL_ADDRESS.
        # However, to be extra safe, we'll ensure we run it correctly.
        
        logger.info(f"Triggering CLI: python cli.py run")
        
        result = subprocess.run(
            [sys.executable, "cli.py", "run"],
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info("Pipeline Output:\n" + result.stdout)
        logger.info("Weekly Pulse Job successfully completed.")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Scheduled job failed with return code {e.returncode}")
        logger.error(f"Error Output:\n{e.stderr}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

def start_scheduler():
    scheduler = BlockingScheduler(timezone=pytz.timezone('Asia/Kolkata'))
    
    # Schedule every day at 3:20 PM (15:20) IST
    trigger = CronTrigger(
        day_of_week='mon-sun',
        hour=15,
        minute=20,
        timezone='Asia/Kolkata'
    )
    
    scheduler.add_job(run_pulse_job, trigger, id='weekly_pulse_job')
    
    logger.info("--- Scheduler Service Initialized ---")
    logger.info("Target: 3:20 PM IST (Asia/Kolkata)")
    logger.info(f"Target Email: {RECIPIENT_EMAIL}")
    logger.info("Press Ctrl+C to exit")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler service stopped.")

if __name__ == "__main__":
    start_scheduler()
