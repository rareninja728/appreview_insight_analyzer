import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime, timedelta
import sys
import requests
import logging

# Configure logging for Streamlit
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("INDmoney-UI")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config

# ── Page Configuration ──────────────────────────────────────
st.set_page_config(
    page_title="INDmoney Review Pulse | Dashboard",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS for Stunning Aesthetics ──────────────────────
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&display=swap');
    
    html, body, [class*="st-"] {
        font-family: 'Outfit', sans-serif;
    }

    .main { background-color: #0d1117; color: #f0f6fc; }
    
    /* Premium Metric Cards */
    [data-testid="stMetricValue"] {
        font-size: 2.8rem !important;
        font-weight: 900 !important;
        color: #00d284 !important;
        text-shadow: 0 0 20px rgba(0, 210, 132, 0.3);
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        color: #8b949e !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #00d284 0%, #00b0e4 100%);
        color: #0d1117;
        border-radius: 12px;
        font-weight: 900;
        border: none;
        padding: 1rem 2rem;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-shadow: 0 4px 15px rgba(0, 210, 132, 0.2);
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 30px rgba(0, 210, 132, 0.4);
        color: white;
    }

    /* Status Badges */
    .status-pulse {
        display: inline-block;
        width: 10px;
        height: 10px;
        background: #00d284;
        border-radius: 50%;
        margin-right: 8px;
        box-shadow: 0 0 10px #00d284;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 210, 132, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(0, 210, 132, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 210, 132, 0); }
    }

    /* Cards */
    .glass-card {
        background: rgba(22, 27, 34, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(48, 54, 61, 0.5);
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 20px;
        transition: border 0.3s ease;
    }
    .glass-card:hover {
        border-color: #00d284;
    }
    
    /* Tabs Customization */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #161b22;
        border-radius: 10px 10px 0 0;
        gap: 1px;
        padding: 0 24px;
        color: #8b949e;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f2937 !important;
        color: #00d284 !important;
        border-bottom: 2px solid #00d284 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ── Sidebar: Control Center ─────────────────────────────────
with st.sidebar:
    st.markdown("### 💸 **Review Pulse**")
    st.image("https://indmoney.com/favicon.ico", width=40)
    st.markdown("---")
    
    st.subheader("⚙️ System Config")
    weeks = st.slider("Lookback Window", 1, 12, config.WEEKS_BACK)
    
    st.markdown("---")
    st.markdown("### 🔌 **Connectivity (Prod Mode)**")
    st.info(f"Backend: {config.BACKEND_URL}")
    
    if st.button("🔌 Verify Connection"):
        try:
            resp = requests.get(f"{config.BACKEND_URL}/api/config", timeout=5)
            if resp.status_code == 200:
                st.success("✅ Connected to Backend")
            else:
                st.error(f"❌ Backend Error: {resp.status_code}")
        except Exception as e:
            st.error(f"❌ Connection Failed: {e}")

# ── Header ──────────────────────────────────────────────────
st.title("🚀 Orchestrator Dashboard")
st.markdown(f"<span class='status-pulse'></span> **System Status: Healthy** | API: `{config.BACKEND_URL}`", unsafe_allow_html=True)

# ── Metrics Row ─────────────────────────────────────────────
st.markdown("---")
mcol1, mcol2, mcol3, mcol4 = st.columns(4)

# Load data for metrics
try:
    df = pd.read_csv(os.path.join(config.DATA_PROCESSED_DIR, "reviews_cleaned.csv"))
    total_reviews = len(df)
    avg_rating = df['rating'].mean() if not df.empty else 0
    google_count = len(df[df['source'] == 'google'])
    apple_count = len(df[df['source'] == 'apple'])
except:
    total_reviews = 0
    avg_rating = 0.0
    google_count = 0
    apple_count = 0
    df = pd.DataFrame()

with mcol1:
    st.metric("Total Reviews", f"{total_reviews}")
with mcol2:
    st.metric("Avg. Rating", f"{avg_rating:.1f} / 5")
with mcol3:
    st.metric("Platform Mix", f"🍎 {apple_count} | 🤖 {google_count}")
with mcol4:
    st.metric("Active Period", f"{weeks} Weeks")

# ── Main Content Area ───────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["⚡ Core Pipeline", "👁️ Insights Explorer", "📥 Raw Feed", "📜 History"])

with tab1:
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        st.markdown("### **Manual Trigger**")
        st.write("Initiate the intelligence cycle: **Fetch** → **Theme AI** → **Report** → **Email**.")
        
        target_email = st.text_input("Recipient Email", config.EMAIL_ADDRESS)
        
        if st.button("🔥 SEND WEEKLY PULSE"):
            if not target_email:
                st.error("Please enter a valid email address.")
            else:
                logger.info(f"UI: Triggering pipeline via {config.BACKEND_URL}")
                with st.status("🌊 Requesting Backend Intelligence...", expanded=True) as status:
                    try:
                        payload = {"weeks_back": weeks, "email": target_email}
                        api_url = f"{config.BACKEND_URL}/api/run-weekly-pulse"
                        st.write(f"📡 Sending request to `{api_url}`...")
                        
                        response = requests.post(api_url, json=payload, timeout=120)
                        
                        if response.status_code == 200:
                            results = response.json()
                            st.success("✅ Pipeline Finished Successfully!")
                            if results.get("email", {}).get("sent"):
                                st.balloons()
                                st.info(f"📧 Email delivered to {target_email}")
                            else:
                                st.warning("⚠️ Analysis complete, but Email failed to send. Check backend logs.")
                            
                            with st.expander("📝 Preview Generated Note", expanded=True):
                                st.markdown(results.get("note", {}).get("markdown", "No content returned."))
                            
                            status.update(label="Process Complete", state="complete")
                        else:
                            st.error(f"❌ Backend Error {response.status_code}")
                            st.code(response.text)
                            status.update(label="Backend Error", state="error")
                    except Exception as e:
                        st.error(f"❌ network Error: {e}")
                        status.update(label="Critical UI Error", state="error")

    with col_b:
        st.markdown("### **Infrastructure**")
        st.write("Current stack capabilities:")
        st.checkbox("Scraping Engine", value=True, disabled=True)
        st.checkbox("PII Redaction", value=True, disabled=True)
        st.checkbox("LLM Thematic Analysis", value=True, disabled=True)
        st.checkbox("SMTP Gateway", value=True, disabled=True)

with tab2:
    st.subheader("💡 Latest AI Themes")
    path_grouped = os.path.join(config.DATA_PROCESSED_DIR, "reviews_grouped.csv")
    if os.path.exists(path_grouped):
        gdf = pd.read_csv(path_grouped)
        if 'theme' in gdf.columns:
            themes = gdf['theme'].value_counts()
            st.bar_chart(themes)
            sel_theme = st.selectbox("Explore Theme Quotes", themes.index)
            quotes = gdf[gdf['theme'] == sel_theme]['text'].head(5).tolist()
            for q in quotes:
                st.markdown(f"> \"{q}\"")
        else:
            st.info("Run analysis to see themes.")
    else:
        st.info("No grouped reviews found. Please run the pipeline.")

with tab3:
    st.subheader("Raw Review Stream")
    if not df.empty:
        st.dataframe(df.head(100), use_container_width=True)
    else:
        st.warning("No data ingested yet.")

with tab4:
    st.subheader("Execution History (Logs)")
    st.caption("Logs are managed on the Backend via `logger.info()` and file logs.")
    st.info("Check production platform (Railway/Streamlit Cloud) console for deep logging traces.")

    with col_b:
        st.markdown("### **Infrastructure**")
        st.write("Current stack capabilities:")
        st.checkbox("Scraping Engine (Active)", value=True, disabled=True)
        st.checkbox("PII Redaction (Active)", value=True, disabled=True)
        st.checkbox("LLM Thematic Analysis (Active)", value=True, disabled=True)
        st.checkbox("Jinja2 Reporting (Active)", value=True, disabled=True)
        st.checkbox("SMTP Gateway (Verified)", value=True, disabled=True)

with tab2:
    st.subheader("💡 Latest AI Themes")
    path_grouped = os.path.join(config.DATA_PROCESSED_DIR, "reviews_grouped.csv")
    if os.path.exists(path_grouped):
        gdf = pd.read_csv(path_grouped)
        if 'theme' in gdf.columns:
            themes = gdf['theme'].value_counts()
            st.bar_chart(themes)
            
            sel_theme = st.selectbox("Explore Theme Quotes", themes.index)
            quotes = gdf[gdf['theme'] == sel_theme]['text'].head(5).tolist()
            for q in quotes:
                st.markdown(f"> \"{q}\"")
        else:
            st.info("Run analysis to see themes.")
    else:
        st.info("No grouped reviews found. Please run the pipeline.")

with tab3:
    st.subheader("Raw Review Stream")
    if total_reviews > 0:
        st.dataframe(df.head(100), use_container_width=True)
        st.download_button("📥 Download Cleaned CSV", df.to_csv(index=False), "indmoney_reviews.csv", "text/csv")
    else:
        st.warning("No data ingested yet.")

with tab4:
    st.subheader("Execution History")
    log_file = os.path.join(config.BASE_DIR, "data", "pipeline_history.json")
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            history = json.load(f)
            st.table(history[::-1][:10]) # Recent first
    else:
        st.caption("No execution records found.")

# ── Footer ──────────────────────────────────────────────────
st.markdown("---")
st.caption("© 2026 INDmoney Review Pulse | Built for Premium Insights | v1.5.0 ST-Cloud Ready")

