import smtplib
from email.message import EmailMessage

from app.config import Settings, get_settings


def send_smtp_message(message: EmailMessage, settings: Settings | None = None) -> None:
    current = settings or get_settings()
    if not current.smtp_host or not current.auth_email_from:
        raise RuntimeError("Email delivery is not configured.")
    with smtplib.SMTP(current.smtp_host, current.smtp_port, timeout=10) as client:
        if current.smtp_starttls:
            client.starttls()
        if current.smtp_username:
            client.login(current.smtp_username, current.smtp_password)
        client.send_message(message)
