"""
Email Drafter — Composes and sends the weekly pulse as a draft email.
Uses smtplib with Gmail SMTP or saves as .eml file.
"""

import smtplib
import ssl
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import config

try:
    import markdown2
except ImportError:
    markdown2 = None


def _markdown_to_html(md_text: str) -> str:
    """Convert Markdown to styled HTML for email."""
    if markdown2:
        html_body = markdown2.markdown(md_text, extras=["fenced-code-blocks", "tables"])
    else:
        # Basic fallback: wrap in <pre>
        html_body = f"<pre style='font-family: sans-serif;'>{md_text}</pre>"

    return f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 650px; margin: 0 auto; padding: 20px; color: #333; }}
    h1 {{ color: #1a1a2e; border-bottom: 2px solid #e94560; padding-bottom: 10px; font-size: 22px; }}
    h2 {{ color: #16213e; font-size: 17px; margin-top: 24px; }}
    blockquote {{ border-left: 3px solid #e94560; padding: 8px 16px; margin: 12px 0; background: #f8f9fa; font-style: italic; color: #555; }}
    ol, ul {{ padding-left: 20px; }}
    li {{ margin: 6px 0; line-height: 1.5; }}
    strong {{ color: #1a1a2e; }}
    hr {{ border: none; border-top: 1px solid #ddd; margin: 20px 0; }}
    .footer {{ font-size: 12px; color: #888; margin-top: 24px; }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""


def compose_email(note: Dict) -> Dict:
    """
    Compose the email subject, body (HTML + plain text), and headers.

    Args:
        note: Dict from note_builder with 'week_label', 'markdown', 'metadata'

    Returns:
        Dict with keys: subject, html_body, plain_body, to, from_addr
    """
    week_label = note.get("week_label", "Unknown")
    metadata = note.get("metadata", {})
    top_themes = metadata.get("top_themes", [])
    themes_str = ", ".join(top_themes[:3]) if top_themes else "Review Summary"

    subject = f"[INDmoney Pulse] {week_label} — Top: {themes_str}"
    plain_body = note.get("markdown", "")
    html_body = _markdown_to_html(plain_body)

    email_data = {
        "subject": subject,
        "html_body": html_body,
        "plain_body": plain_body,
        "to": config.EMAIL_ADDRESS or "your_email@gmail.com",
        "from_addr": config.EMAIL_ADDRESS or "your_email@gmail.com",
    }

    return email_data


def send_email(email_data: Dict) -> bool:
    """
    Send the email via Gmail SMTP.

    Args:
        email_data: Dict from compose_email()

    Returns:
        True if sent successfully, False otherwise
    """
    if not config.EMAIL_ADDRESS or not config.EMAIL_APP_PASSWORD:
        print("[Email] No email credentials configured. Saving draft instead.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = email_data["subject"]
    msg["From"] = email_data["from_addr"]
    msg["To"] = email_data["to"]

    # Attach plain text and HTML versions
    msg.attach(MIMEText(email_data["plain_body"], "plain", "utf-8"))
    msg.attach(MIMEText(email_data["html_body"], "html", "utf-8"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(config.SMTP_SERVER, config.SMTP_PORT, context=context) as server:
            server.login(config.EMAIL_ADDRESS, config.EMAIL_APP_PASSWORD)
            server.sendmail(
                email_data["from_addr"],
                email_data["to"],
                msg.as_string(),
            )
        print(f"[Email] SUCCESS: Sent to {email_data['to']}")
        return True
    except Exception as e:
        print(f"[Email] FAILURE: Send failed: {e}")
        return False


def save_email_draft(email_data: Dict, note: Dict, output_dir: str = None) -> str:
    """
    Save the email as a text draft artifact.

    Args:
        email_data: Dict from compose_email()
        note: Dict from note_builder
        output_dir: Directory to save in (defaults to config.EMAIL_DRAFTS_DIR)

    Returns:
        Path to saved draft file
    """
    output_dir = output_dir or config.EMAIL_DRAFTS_DIR
    os.makedirs(output_dir, exist_ok=True)

    week_label = note.get("week_label", "draft")
    filename = f"email_draft_{week_label}.txt"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"TO: {email_data['to']}\n")
        f.write(f"FROM: {email_data['from_addr']}\n")
        f.write(f"SUBJECT: {email_data['subject']}\n")
        f.write(f"DATE: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("=" * 60 + "\n\n")
        f.write(email_data["plain_body"])

    # Also save HTML version
    html_path = os.path.join(output_dir, f"email_draft_{week_label}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(email_data["html_body"])

    print(f"[Email] Draft saved: {filepath}")
    print(f"[Email] HTML draft saved: {html_path}")
    return filepath


def draft_and_send(note: Dict) -> Dict:
    """
    Full email workflow: compose → try send → save draft.

    Args:
        note: Dict from note_builder

    Returns:
        Dict with status, draft_path, and sent flag
    """
    email_data = compose_email(note)
    draft_path = save_email_draft(email_data, note)
    sent = send_email(email_data)

    return {
        "sent": sent,
        "draft_path": draft_path,
        "subject": email_data["subject"],
        "to": email_data["to"],
    }


if __name__ == "__main__":
    # Quick test
    test_note = {
        "week_label": "W12-2026",
        "markdown": "# Test Pulse\n\nThis is a test note.",
        "metadata": {"top_themes": ["Stability", "Features"], "total_reviews": 100},
    }
    result = draft_and_send(test_note)
    print(f"Email sent: {result['sent']}, Draft: {result['draft_path']}")
