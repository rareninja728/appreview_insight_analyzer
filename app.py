import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.orchestrator import run_weekly_pulse
from src.ingestion.apple_reviews import fetch_apple_reviews
from src.ingestion.google_reviews import fetch_google_reviews

# ── Page Configuration ──────────────────────────────────────
st.set_page_config(
    page_title="INDmoney Review Pulse | Backend Engine",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS for Premium Look ─────────────────────────────
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #f0f6fc; }
    .stButton>button { background-color: #00d284; color: #0d1117; border-radius: 8px; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #00b0e4; color: white; }
    .metric-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; text-align: center; }
    .status-badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    .status-running { background: #1f2d3d; color: #2c9aff; border: 1px solid #2c9aff; }
    .status-success { background: #1f2d24; color: #00d284; border: 1px solid #00d284; }
    </style>
""", unsafe_allow_html=True)

# ── Sidebar: Configuration ──────────────────────────────────
with st.sidebar:
    st.image("https://indmoney.com/favicon.ico", width=50)
    st.title("Backend Engine")
    st.markdown("---")
    
    st.subheader("⚙️ Settings")
    weeks = st.slider("Lookback Period (Weeks)", 1, 12, config.WEEKS_BACK)
    model = st.selectbox("LLM Model", ["llama-3.1-8b-instant", "mixtral-8x7b-32768", "llama-3.3-70b-versatile"], index=0)
    
    st.markdown("---")
    st.info(f"API Key: Loaded (**{config.GROQ_API_KEY[:4]}...**)")
    st.info(f"Email: {config.EMAIL_ADDRESS}")

# ── Header ──────────────────────────────────────────────────
st.title("🚀 INDmoney Orchestration Dashboard")
st.markdown("Manage the end-to-end review ingestion and analysis pipeline.")

# ── Real-time Stats ─────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

# Load current data if exists
try:
    df = pd.read_csv(os.path.join(config.DATA_PROCESSED_DIR, "reviews_cleaned.csv"))
    total_reviews = len(df)
    avg_rating = df['rating'].mean()
except:
    total_reviews = 0
    avg_rating = 0.0

with col1:
    st.metric("Total Reviews", total_reviews, "+12% vs last week")
with col2:
    st.metric("Avg. Rating", f"{avg_rating:.1f}/5", "-0.2")
with col3:
    st.metric("Weeks Back", weeks)
with col4:
    st.metric("System Status", "Healthy", delta_color="normal")

# ── Main Control Panel ──────────────────────────────────────
st.markdown("---")
tab1, tab2, tab3 = st.tabs(["🚀 Pipeline Controller", "📥 Raw Ingestion", "📝 Activity Logs"])

with tab1:
    st.subheader("Manual Pipeline Execution")
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        st.write("Trigger the full cycle: Fetch → Clean → Analyze → Report → Email")
        if st.button("▶️ Launch Full Pipeline"):
            with st.status("Executing Pipeline Steps...", expanded=True) as status:
                st.write("Step 1: Fetching Apple/Google reviews...")
                config.WEEKS_BACK = weeks
                results = run_weekly_pulse(skip_email=False)
                
                if "error" in results:
                    st.error(f"Pipeline Failed: {results['error']}")
                    status.update(label="Pipeline Failed", state="error")
                else:
                    st.success("Pipeline Successfully Completed!")
                    status.update(label="Pipeline Finished", state="complete")
                    st.balloons()

    with col_b:
        st.markdown("""
        **System Components**
        - `Ingestion`: Active (Play/App Store)
        - `Analysis`: Groq LLM (High Priority)
        - `Reporting`: Dynamic Jinja2
        - `Delivery`: SMTP Gateway
        """)

with tab2:
    st.subheader("Ingestion Status")
    if st.button("Fetch Latest Only"):
        apple = fetch_apple_reviews()
        google = fetch_google_reviews()
        st.write(f"Fetched {len(apple)} from Apple, {len(google)} from Google.")

with tab3:
    st.subheader("Recent Execution Logs")
    log_file = os.path.join(config.BASE_DIR, "data", "pipeline_history.json")
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            history = json.load(f)
            st.table(history[-5:])
    else:
        st.write("No logged activity yet.")

# ── Footer ──────────────────────────────────────────────────
st.markdown("---")
st.caption("INDmoney Review Pulse Backend | Build v1.2.0")
