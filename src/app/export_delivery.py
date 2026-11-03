import json
import secrets
import smtplib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from typing import Literal
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.mail_delivery import send_smtp_message
from app.models import ExportProviderConnection, User
from app.secret_encryption import decrypt_secret, derive_encryption_key, encrypt_secret

DeliveryChannel = Literal["google_drive", "dropbox", "email"]
GOOGLE_REFRESH_URL = "https://oauth2.googleapis.com/token"
DROPBOX_REFRESH_URL = "https://api.dropboxapi.com/oauth2/token"
GOOGLE_UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files"
DROPBOX_UPLOAD_URL = "https://content.dropboxapi.com/2/files/upload"


@dataclass(frozen=True)
class ExportFile:
    filename: str
    content_type: str
    content: bytes


class ExportDeliveryError(RuntimeError):
    def __init__(self, message: str, delivered_files: int = 0):
        super().__init__(message)
        self.delivered_files = delivered_files


def _token_aad(provider: str, user_id: UUID, purpose: str) -> bytes:
    return f"export:{provider}:{user_id}:{purpose}:v1".encode()


def _refresh_access_token(
    connection: ExportProviderConnection,
    user: User,
    db: Session,
) -> str:
    settings = get_settings()
    try:
        key = derive_encryption_key(settings.auth_encryption_key)
        refresh_token = decrypt_secret(
            connection.encrypted_refresh_token or b"",
            key,
            _token_aad(connection.provider, user.id, "refresh"),
        ).decode()
    except (ValueError, UnicodeDecodeError) as error:
        raise ExportDeliveryError("The connected provider token is unavailable.") from error

    if connection.provider == "google_drive":
        token_url = GOOGLE_REFRESH_URL
        data = {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    else:
        token_url = DROPBOX_REFRESH_URL
        data = {
            "client_id": settings.dropbox_app_key,
            "client_secret": settings.dropbox_app_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    try:
        response = httpx.post(token_url, data=data, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        if not isinstance(token_data, dict):
            raise ValueError("Provider token response was invalid.")
        access_token = token_data["access_token"]
        if not isinstance(access_token, str) or not access_token:
            raise ValueError("Provider access token was invalid.")
    except (httpx.HTTPError, KeyError, ValueError) as error:
        raise ExportDeliveryError("The connected provider could not be refreshed.") from error

    connection.encrypted_access_token = encrypt_secret(
        access_token.encode(),
        key,
        _token_aad(connection.provider, user.id, "access"),
    )
    expires_in = token_data.get("expires_in")
    connection.token_expires_at = (
        datetime.now(UTC) + timedelta(seconds=int(expires_in))
        if isinstance(expires_in, (int, float)) and expires_in > 0
        else None
    )
    rotated_refresh = token_data.get("refresh_token")
    if isinstance(rotated_refresh, str) and rotated_refresh:
        connection.encrypted_refresh_token = encrypt_secret(
            rotated_refresh.encode(),
            key,
            _token_aad(connection.provider, user.id, "refresh"),
        )
    db.commit()
    return access_token


def _access_token(
    connection: ExportProviderConnection,
    user: User,
    db: Session,
) -> str:
    if (
        connection.token_expires_at is None
        or connection.token_expires_at <= datetime.now(UTC) + timedelta(seconds=60)
    ):
        return _refresh_access_token(connection, user, db)
    try:
        return decrypt_secret(
            connection.encrypted_access_token,
            derive_encryption_key(get_settings().auth_encryption_key),
            _token_aad(connection.provider, user.id, "access"),
        ).decode()
    except (ValueError, UnicodeDecodeError) as error:
        raise ExportDeliveryError("The connected provider token is unavailable.") from error


def _upload_google_drive(token: str, export: ExportFile) -> None:
    boundary = f"casework-{secrets.token_hex(18)}"
    metadata = json.dumps(
        {"name": export.filename, "mimeType": export.content_type},
        separators=(",", ":"),
    ).encode()
    body = b"".join(
        (
            f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode(),
            metadata,
            f"\r\n--{boundary}\r\nContent-Type: {export.content_type}\r\n\r\n".encode(),
            export.content,
            f"\r\n--{boundary}--".encode(),
        )
    )
    response = httpx.post(
        GOOGLE_UPLOAD_URL,
        params={"uploadType": "multipart", "fields": "id,name"},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/related; boundary={boundary}",
        },
        content=body,
        timeout=30,
    )
    response.raise_for_status()


def _upload_dropbox(token: str, export: ExportFile) -> None:
    response = httpx.post(
        DROPBOX_UPLOAD_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream",
            "Dropbox-API-Arg": json.dumps(
                {
                    "path": f"/{export.filename}",
                    "mode": "add",
                    "autorename": False,
                    "mute": True,
                },
                separators=(",", ":"),
            ),
        },
        content=export.content,
        timeout=30,
    )
    response.raise_for_status()


def _send_email(recipient: str, exports: list[ExportFile]) -> None:
    settings = get_settings()
    if not settings.auth_email_from:
        raise ExportDeliveryError("Application email delivery is not configured.")
    message = EmailMessage()
    message["From"] = settings.auth_email_from
    message["To"] = recipient
    message["Subject"] = "Your settlement proposal drafts"
    message.set_content(
        "Attached are the CR 2A-style proposal draft and property-division workbook "
        "you explicitly requested. Review them with qualified Washington counsel."
    )
    for export in exports:
        major, minor = export.content_type.split("/", 1)
        message.add_attachment(
            export.content,
            maintype=major,
            subtype=minor,
            filename=export.filename,
        )
    try:
        send_smtp_message(message, settings)
    except (smtplib.SMTPException, OSError, RuntimeError) as error:
        raise ExportDeliveryError("Email delivery failed.") from error


def deliver_export_files(
    db: Session,
    user: User,
    channel: DeliveryChannel,
    destination: str,
    exports: list[ExportFile],
) -> int:
    if channel == "email":
        _send_email(destination, exports)
        return len(exports)

    connection = db.scalar(
        select(ExportProviderConnection).where(
            ExportProviderConnection.user_id == user.id,
            ExportProviderConnection.provider == channel,
        )
    )
    if connection is None:
        raise ExportDeliveryError("Connect the selected provider before delivery.")
    if channel == "google_drive" and not (
        get_settings().google_client_id and get_settings().google_client_secret
    ):
        raise ExportDeliveryError("Google Drive delivery is not configured.")
    if channel == "dropbox" and not (
        get_settings().dropbox_app_key and get_settings().dropbox_app_secret
    ):
        raise ExportDeliveryError("Dropbox delivery is not configured.")
    token = _access_token(connection, user, db)
    delivered = 0
    for export in exports:
        try:
            if channel == "google_drive":
                _upload_google_drive(token, export)
            else:
                _upload_dropbox(token, export)
        except httpx.HTTPError as error:
            provider_name = "Google Drive" if channel == "google_drive" else "Dropbox"
            raise ExportDeliveryError(
                f"{provider_name} uploaded {delivered} of {len(exports)} files before an error.",
                delivered_files=delivered,
            ) from error
        delivered += 1
    return delivered
