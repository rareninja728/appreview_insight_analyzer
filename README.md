# 📊 INDmoney Weekly Review Pulse

Turn recent App Store / Play Store reviews into a **one-page weekly pulse** containing top themes, real user quotes, and action ideas — then draft an email with the note.

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone & navigate
cd appreview_insight_analyzer

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
copy .env.example .env
```

Edit `.env` with your credentials:

| Variable | Where to Get It |
|---|---|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) → API Keys |
| `EMAIL_ADDRESS` | Your Gmail address |
| `EMAIL_APP_PASSWORD` | [Google App Passwords](https://myaccount.google.com/apppasswords) |

### 3. Run the Pipeline

**Option A — CLI (one command):**
```bash
python -c "from src.orchestrator import run_weekly_pulse; run_weekly_pulse()"
```

**Option B — Streamlit Dashboard:**
```bash
streamlit run app.py
```

---

## 🔄 How to Re-run for a New Week

1. Activate your virtual environment
2. Run the pipeline — it automatically fetches the latest reviews:
   ```bash
   python -c "from src.orchestrator import run_weekly_pulse; run_weekly_pulse()"
   ```
3. Or open the Streamlit app and click through each tab:
   - **Tab 1**: Fetch reviews → **Tab 2**: Generate themes → **Tab 3**: Build note → **Tab 4**: Send email
4. The new weekly note appears in `outputs/weekly_notes/`
5. The email draft appears in `outputs/email_drafts/`

---

## 🏷️ Theme Legend

Themes are generated dynamically by the Groq LLM based on actual review content. Common themes for INDmoney include:

| Theme | Description |
|---|---|
| **App Stability** | Crashes, freezes, performance issues |
| **Investment Features** | SIP tracking, mutual funds, stocks |
| **Customer Support** | Response time, ticket resolution |
| **UI/UX** | Interface design, navigation, usability |
| **Account & KYC** | Account creation, verification, KYC flow |

> These labels are auto-generated each run — actual themes may vary based on review data.

---

## 📁 Project Structure

```
appreview_insight_analyzer/
├── config.py                 # Settings & env loading
├── app.py                    # Streamlit UI
├── requirements.txt
├── .env.example
│
├── src/
│   ├── ingestion/
│   │   ├── apple_reviews.py  # App Store RSS fetcher
│   │   ├── google_reviews.py # Play Store scraper
│   │   └── pii_stripper.py   # PII removal
│   ├── analysis/
│   │   ├── theme_generator.py # Groq theme discovery
│   │   └── review_grouper.py  # Review classification
│   ├── report/
│   │   ├── note_builder.py   # Weekly note generator
│   │   └── email_drafter.py  # Email compose & send
│   └── orchestrator.py       # Full pipeline runner
│
├── data/processed/           # Cleaned reviews (CSV/JSON)
├── outputs/
│   ├── weekly_notes/         # Generated Markdown notes
│   └── email_drafts/         # Email text/HTML drafts
└── tests/
```

---

## 📦 Deliverables

| Deliverable | Location |
|---|---|
| Working prototype | `streamlit run app.py` |
| Weekly note (MD) | `outputs/weekly_notes/week_WXX-YYYY.md` |
| Email draft | `outputs/email_drafts/` |
| Reviews CSV | `data/processed/reviews_cleaned.csv` |
| Reviews JSON | `data/processed/reviews_cleaned.json` |

---

## 🔒 Privacy & Constraints

- ✅ Uses **public** review exports only — no scraping behind logins
- ✅ No usernames, emails, or IDs stored in any artifact
- ✅ PII is regex-stripped (email, phone, Aadhaar, PAN, UPI)
- ✅ Notes are capped at **≤250 words** for scannability
- ✅ Maximum **5 themes** per analysis run

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| LLM | Groq (`llama-3.3-70b-versatile`) |
| Reviews | Apple RSS + `google-play-scraper` |
| Dashboard | Streamlit |
| Email | smtplib + Gmail SMTP |

---

*Built for Product, Growth, Support, and Leadership teams at INDmoney.*
