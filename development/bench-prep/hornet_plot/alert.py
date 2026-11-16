"""
One email when the chamber first falls below 80 mTorr.

The recipient is fixed. The sender login stays in the environment:
SMTP_HOST, SMTP_USER, SMTP_PASSWORD, and optional SMTP_PORT (default 587).
Nothing here stores a password.
"""

import os
import smtplib
from email.message import EmailMessage

TO = "harshdes@umich.edu"


def send_cryo_mail(pressure_torr):
    host = os.environ.get("SMTP_HOST", "")
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    if not host or not user or not password:
        return False
    msg = EmailMessage()
    msg["From"] = user
    msg["To"] = TO
    msg["Subject"] = "Less than 80 mTorr. Turn on the cryopump."
    msg.set_content(
        "Chamber pressure is %.3E Torr.\nTurn on the cryopump.\n" % pressure_torr
    )
    port = int(os.environ.get("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(msg)
    return True
