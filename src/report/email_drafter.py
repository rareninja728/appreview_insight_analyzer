import smtplib
import ssl
import os
import sys
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Optional
import traceback

# ── Step 3: Deep Logging ──────────────────────────────────
logger = logging.getLogger("INDmoney-Mailer")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import config

try:
    import markdown2
except ImportError:
    markdown2 = None
    logger.warning("markdown2 not found. Email will fallback to plain text-only HTML.")


def _markdown_to_html(md_text: str) -> str:
    """Convert Markdown to styled HTML for email."""
    if markdown2:
        html_body = markdown2.markdown(md_text, extras=["fenced-code-blocks", "tables"])
    else:
        # Basic fallback: wrap in <pre>
        html_body = f"<pre style='font-family: sans-serif; white-space: pre-wrap;'>{md_text}</pre>"

    return f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 650px; margin: 0 auto; padding: 20px; color: #333; }}
    h1 {{ color: #1a1a2e; border-bottom: 2px solid #00d284; padding-bottom: 10px; font-size: 22px; }}
    h2 {{ color: #16213e; font-size: 17px; margin-top: 24px; }}
    blockquote {{ border-left: 4px solid #00d284; padding: 12px 20px; margin: 20px 0; background: #f0fdf4; font-style: italic; color: #374151; }}
    ol, ul {{ padding-left: 20px; }}
    li {{ margin: 8px 0; line-height: 1.6; }}
    strong {{ color: #064e3b; }}
    hr {{ border: none; border-top: 1px solid #e5e7eb; margin: 30px 0; }}
    .footer {{ font-size: 11px; color: #9ca3af; margin-top: 40px; text-align: center; border-top: 1px dashed #e5e7eb; padding-top: 20px; }}
</style>
</head>
<body>
{html_body}
<div class="footer">
    This is an automated intelligence pulse from INDmoney Review Analyzer.<br>
    Configured Recipient: {config.EMAIL_ADDRESS}
</div>
</body>
</html>"""


def compose_email(note: Dict) -> Dict:
    """Compose the email subject, body, and headers."""
    week_label = note.get("week_label", "Unknown")
    metadata = note.get("metadata", {})
    top_themes = metadata.get("top_themes", [])
    themes_str = ", ".join(top_themes[:3]) if top_themes else "Weekly Review Summary"

    subject = f"💸 [INDmoney Pulse] {week_label} | {themes_str}"
    plain_body = note.get("markdown", "")
    html_body = _markdown_to_html(plain_body)

    return {
        "subject": subject,
        "html_body": html_body,
        "plain_body": plain_body,
        "to": config.EMAIL_ADDRESS,
        "from_addr": config.SENDER_EMAIL,
    }


def send_email(email_data: Dict) -> bool:
    """
    Step 5: Robust Email Sending Logic.
    Sends mail via SMTP_SSL with explicit timeout and error logging.
    """
    logger.info(f"Preparing to send email to {email_data['to']}...")
    
    if not config.SENDER_EMAIL or not config.EMAIL_APP_PASSWORD:
        logger.error("Email credentials missing in config (SENDER_EMAIL or EMAIL_APP_PASSWORD)")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = email_data["subject"]
    msg["From"] = email_data["from_addr"]
    msg["To"] = email_data["to"]

    msg.attach(MIMEText(email_data["plain_body"], "plain", "utf-8"))
    msg.attach(MIMEText(email_data["html_body"], "html", "utf-8"))

    try:
        host = config.SMTP_SERVER
        port = config.SMTP_PORT
        logger.info(f"Connecting to SMTP Server: {host}:{port}")
        
        context = ssl.create_default_context()
        
        # Explicitly use SMTP_SSL for port 465 or SMTP + starttls for others
        # Here we assume port 465 (SSL) as per config default
        with smtplib.SMTP_SSL(host, port, context=context, timeout=20) as server:
            logger.info("Connection established. Attempting login...")
            server.login(config.SENDER_EMAIL, config.EMAIL_APP_PASSWORD)
            logger.info("Login successful. Sending message...")
            server.sendmail(
                email_data["from_addr"],
                email_data["to"],
                msg.as_string(),
            )
            
        logger.info(f"✅ SUCCESS: Newsletter delivered to {email_data['to']}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP Authentication Failed. Check EMAIL_APP_PASSWORD and App Password settings.")
    except smtplib.SMTPConnectError:
        logger.error(f"Failed to connect to SMTP server at {config.SMTP_SERVER}:{config.SMTP_PORT}")
    except Exception as e:
        logger.error(f"❌ CRITICAL Error in send_email: {str(e)}", exc_info=True)
        
    return False


def save_email_draft(email_data: Dict, note: Dict, output_dir: str = None) -> str:
    """Save the email as a text draft artifact (for debugging/backup)."""
    output_dir = output_dir or config.EMAIL_DRAFTS_DIR
    os.makedirs(output_dir, exist_ok=True)

    week_label = note.get("week_label", "draft").replace(" ", "_")
    filename = f"email_draft_{week_label}.txt"
    filepath = os.path.join(output_dir, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"TO: {email_data['to']}\n")
            f.write(f"FROM: {email_data['from_addr']}\n")
            f.write(f"SUBJECT: {email_data['subject']}\n")
            f.write(f"DATE: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write("=" * 60 + "\n\n")
            f.write(email_data["plain_body"])

        html_path = os.path.join(output_dir, f"email_draft_{week_label}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(email_data["html_body"])

        logger.info(f"Email draft saved to: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to save email draft: {e}")
        return ""


def draft_and_send(note: Dict) -> Dict:
    """Full workflow: compose → save draft → send."""
    email_data = compose_email(note)
    draft_path = save_email_draft(email_data, note)
    sent = send_email(email_data)

    return {
        "sent": sent,
        "draft_path": draft_path,
        "subject": email_data["subject"],
        "to": email_data["to"],
    }
