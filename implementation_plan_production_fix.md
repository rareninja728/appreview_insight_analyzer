# Implementation Plan: End-to-End Production Fix for Email Sending

This plan outlines the systematic steps to fix the issue where the INDmoney Review Pulse application works locally but fails to send emails in production.

## 🎯 **Objective**
Ensure the "Send Pulse" button triggers email sending reliably in production by fixing configuration, connectivity, and implementing robust logging.

## 🛠 **Phase 1: Environment & Config (Steps 1 & 4)**
- **Update `config.py`**:
    - Replace all hardcoded values with `os.getenv()`.
    - Add `BACKEND_URL` for frontend use.
    - Implement `assert` checks for critical variables (`GROQ_API_KEY`, `EMAIL_ADDRESS`, `EMAIL_APP_PASSWORD`).
    - Standardize SMTP settings.

## 🛠 **Phase 2: Backend Enhancement (Steps 2, 3, 7, 8)**
- **Update `server.py`**:
    - Add deep logging using the standard `logging` library.
    - Implement a dedicated `/api/test-email` GET endpoint.
    - Implement a robust `/api/run-weekly-pulse` POST endpoint.
    - Ensure `CORSMiddleware` allows requests from all origins (or specific production domains).
    - Add an environment validation startup check.

## 🛠 **Phase 3: Robust Logic (Steps 5 & 6)**
- **Update `src/report/email_drafter.py`**:
    - Use `logging` instead of `print`.
    - Wrap the entire SMTP connection/login/send block in a comprehensive `try/except`.
    - Log the full stack trace on failure using `logging.error(..., exc_info=True)`.
    - Ensure TLS/SSL configuration is correct and explicit.

## 🛠 **Phase 4: Frontend Connectivity (Step 1)**
- **Update `app.py`**:
    - Update the "SEND WEEKLY PULSE" button logic to hit the `/api/run_pipeline` endpoint using the `BACKEND_URL`.
    - Add UI feedback/logging for the API call status.

## 🧪 **Phase 5: Validation (Step 9)**
- Test `/api/test-email` to verify SMTP connectivity.
- Test `/api/run_pipeline` to verify full orchestration.
- Verify production environment variables are correctly set in the hosting platform (Railway/Streamlit Cloud).

## 🚀 **Deliverables**
- **Refined `config.py`**
- **Production-ready `server.py`**
- **Robust `email_drafter.py`**
- **Connected `app.py`**
