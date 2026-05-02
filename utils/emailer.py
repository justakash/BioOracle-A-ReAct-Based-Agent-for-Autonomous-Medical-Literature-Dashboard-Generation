"""
Email Delivery Utility
Sends dashboard reports via SMTP.
"""

import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from loguru import logger


def send_report_email(
    csv_path: str,
    config_id: str,
    recipient: str,
    subject: Optional[str] = "BioOracle Dashboard Report",
) -> bool:
    """
    Send a dashboard report email with the CSV attached.
    Reads SMTP credentials from environment variables.
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)

    if not smtp_user or not smtp_password:
        logger.warning("SMTP credentials not configured. Email not sent.")
        return False

    msg = MIMEMultipart()
    msg["From"] = smtp_from
    msg["To"] = recipient
    msg["Subject"] = subject

    body = f"""
Hello,

Your BioOracle dashboard report (config ID: {config_id}) is attached.

You can access the interactive dashboard at:
  http://localhost:8000/api/v1/dashboard/{config_id}

Best regards,
BioOracle
"""
    msg.attach(MIMEText(body, "plain"))

    # Attach CSV
    if os.path.exists(csv_path):
        with open(csv_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        filename = os.path.basename(csv_path)
        part.add_header("Content-Disposition", f"attachment; filename={filename}")
        msg.attach(part)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_from, recipient, msg.as_string())
        logger.info(f"Report emailed to {recipient}")
        return True
    except Exception as e:
        logger.exception(f"Failed to send email to {recipient}: {e}")
        raise
