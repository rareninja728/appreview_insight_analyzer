"""
Local Configuration for PHASE 1: Review Ingestion.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# App Identifiers
APPLE_APP_ID = "1450178837"          # INDmoney: Stocks, Mutual Funds
GOOGLE_PACKAGE = "in.indwealth"      # INDmoney: Stocks, Mutual Funds

# Fetch Settings
WEEKS_BACK = 12

# Local Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR]:
    os.makedirs(d, exist_ok=True)
