import base64
import hashlib
import json
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal
from urllib.parse import urlencode
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth_routes import require_current_user
from app.config import get_settings
from app.database import get_db
from app.failure_logging import log_failure_event
from app.models import AuthChallenge, ExportProviderConnection, User
from app.secret_encryption import decrypt_secret, derive_encryption_key, encrypt_secret

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/export-integrations", tags=["export integrations"])
DbSession = Annotated[Session, Depends(get_db)]
Provider = Literal["google_drive", "dropbox"]
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.file"
DROPBOX_SCOPES = "account_info.read files.content.write"
OAUTH_STATE_TTL = timedelta(minutes=10)


def _settings_ready(provider: Provider) -> bool:
    settings = get_settings()
    if not settings.auth_enabled or not settings.case_data_enabled or settings.demo_mode_enabled:
        return False
    try:
        derive_encryption_key(settings.auth_encryption_key)
    except ValueError:
        return False
    if provider == "google_drive":
        return bool(settings.google_client_id and settings.google_client_secret)
    return bool(settings.dropbox_app_key and settings.dropbox_app_secret)


def _token_aad(provider: str, user_id: UUID, purpose: str) -> bytes:
    return f"export:{provider}:{user_id}:{purpose}:v1".encode()


def _encode_verifier(verifier: str) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()


def _authorization_url(provider: Provider, state: str, verifier: str) -> str:
    settings = get_settings()
    if provider == "google_drive":
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": f"{settings.auth_public_base_url.rstrip('/')}/api/export-integrations/google_drive/callback",
            "response_type": "code",
            "scope": f"openid email {DRIVE_SCOPE}",
            "state": state,
            "code_challenge": _encode_verifier(verifier),
            "code_challenge_method": "S256",
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    params = {
        "client_id": settings.dropbox_app_key,
        "redirect_uri": f"{settings.auth_public_base_url.rstrip('/')}/api/export-integrations/dropbox/callback",
        "response_type": "code",
        "token_access_type": "offline",
        "scope": DROPBOX_SCOPES,
        "state": state,
        "code_challenge": _encode_verifier(verifier),
        "code_challenge_method": "S256",
    }
    return f"https://www.dropbox.com/oauth2/authorize?{urlencode(params)}"


@router.get("/destinations")
def export_destinations(
    user: Annotated[User, Depends(require_current_user)],
    db: DbSession,
    response: Response,
) -> dict:
    settings = get_settings()
    try:
        connections = {
            connection.provider: connection
            for connection in db.scalars(
                select(ExportProviderConnection).where(ExportProviderConnection.user_id == user.id)
            )
        }
    except SQLAlchemyError as error:
        log_failure_event(logger, "proposal_download_destination_status_failed", error)
        raise HTTPException(status_code=503, detail="Export destination status is unavailable.") from error
    destinations = {
        "google_drive": {
            "configured": _settings_ready("google_drive"),
            "connected": "google_drive" in connections,
            "account": connections["google_drive"].account_label
            if "google_drive" in connections
            else None,
            "destination": "Google Drive root (private)",
        },
        "dropbox": {
            "configured": _settings_ready("dropbox"),
            "connected": "dropbox" in connections,
            "account": connections["dropbox"].account_label if "dropbox" in connections else None,
            "destination": "Dropbox app folder root (private)",
        },
        "email": {
            "configured": bool(
                settings.auth_enabled
                and settings.case_data_enabled
                and not settings.demo_mode_enabled
                and settings.smtp_host
                and settings.auth_email_from
            ),
            "connected": False,
            "account": None,
            "sender": settings.auth_email_from,
        },
    }
    response.headers["Cache-Control"] = "no-store"
    return destinations


@router.post("/{provider}/connect")
def start_export_provider_connection(
    provider: str,
    user: Annotated[User, Depends(require_current_user)],
    db: DbSession,
    response: Response,
) -> dict[str, str]:
    if provider not in {"google_drive", "dropbox"}:
        raise HTTPException(status_code=404, detail="Export provider not found.")
    selected_provider: Provider = provider
    if not _settings_ready(selected_provider):
        raise HTTPException(
            status_code=503,
            detail=f"{selected_provider.replace('_', ' ').title()} connection is not configured.",
        )

    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = AuthChallenge(
        user_id=user.id,
        purpose=f"export_{selected_provider}",
        challenge=state,
        expires_at=datetime.now(UTC) + OAUTH_STATE_TTL,
        context={"code_verifier": verifier},
    )
    try:
        db.add(challenge)
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=503, detail="Provider connection could not be started.") from error
    response.headers["Cache-Control"] = "no-store"
    return {"authorization_url": _authorization_url(selected_provider, state, verifier)}


def _consume_challenge(
    db: Session,
    user: User,
    provider: Provider,
    state: str,
) -> AuthChallenge:
    now = datetime.now(UTC)
    challenge = db.scalar(
        select(AuthChallenge)
        .where(
            AuthChallenge.user_id == user.id,
            AuthChallenge.purpose == f"export_{provider}",
            AuthChallenge.challenge == state,
            AuthChallenge.consumed_at.is_(None),
        )
        .with_for_update()
    )
    if challenge is None or challenge.expires_at <= now:
        raise HTTPException(status_code=401, detail="Provider authorization could not be verified.")
    challenge.consumed_at = now
    return challenge


def _exchange_token(
    provider: Provider,
    code: str,
    verifier: str,
) -> dict:
    settings = get_settings()
    if provider == "google_drive":
        response = httpx.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": code,
                "code_verifier": verifier,
                "grant_type": "authorization_code",
                "redirect_uri": f"{settings.auth_public_base_url.rstrip('/')}/api/export-integrations/google_drive/callback",
            },
            timeout=10,
        )
    else:
        response = httpx.post(
            "https://api.dropboxapi.com/oauth2/token",
            data={
                "client_id": settings.dropbox_app_key,
                "client_secret": settings.dropbox_app_secret,
                "code": code,
                "code_verifier": verifier,
                "grant_type": "authorization_code",
                "redirect_uri": f"{settings.auth_public_base_url.rstrip('/')}/api/export-integrations/dropbox/callback",
            },
            timeout=10,
        )
    response.raise_for_status()
    token_data = response.json()
    if (
        not isinstance(token_data, dict)
        or not isinstance(token_data.get("access_token"), str)
        or not token_data["access_token"]
    ):
        raise ValueError("Provider did not return an access token.")
    return token_data


def _provider_account(provider: Provider, access_token: str) -> tuple[str, str]:
    if provider == "google_drive":
        response = httpx.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        response.raise_for_status()
        account = response.json()
        if not isinstance(account, dict):
            raise ValueError("Provider account details were invalid.")
        subject = account.get("sub")
        label = account.get("email")
    else:
        response = httpx.post(
            "https://api.dropboxapi.com/2/users/get_current_account",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        response.raise_for_status()
        account = response.json()
        if not isinstance(account, dict):
            raise ValueError("Provider account details were invalid.")
        subject = account.get("account_id")
        label = account.get("email")
    if (
        not isinstance(subject, str)
        or not subject
        or not isinstance(label, str)
        or not label
    ):
        raise ValueError("Provider account details were invalid.")
    return subject[:255], label[:320]


def _connection_result_page(provider: Provider, connected: bool) -> HTMLResponse:
    provider_name = "Google Drive" if provider == "google_drive" else "Dropbox"
    message = (
        f"{provider_name} connected. Return to the settlement planner."
        if connected
        else f"{provider_name} connection was canceled or could not be verified."
    )
    event = {
        "type": "casework-export-connection",
        "provider": provider,
        "connected": connected,
    }
    return HTMLResponse(
        content=(
            "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            f"<title>{provider_name} connection</title><body>"
            "<header><a href=\"/\" aria-label=\"Casework home\">Casework</a></header><main>"
            f"<h1>{provider_name} connection</h1><p>{message}</p>"
            "<a href=\"/\">Return to Casework</a></main>"
            "<footer>Casework &middot; Washington divorce mediation &middot; Product preview</footer><script>"
            f"if(window.opener){{window.opener.postMessage({json.dumps(event)},window.location.origin);window.close();}}"
            "</script></body></html>"
        ),
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.get("/{provider}/callback")
def complete_export_provider_connection(
    provider: str,
    state: str,
    user: Annotated[User, Depends(require_current_user)],
    db: DbSession,
    code: str | None = None,
    error: str | None = None,
) -> Response:
    if provider not in {"google_drive", "dropbox"}:
        raise HTTPException(status_code=404, detail="Export provider not found.")
    selected_provider: Provider = provider
    if not _settings_ready(selected_provider):
        raise HTTPException(status_code=503, detail="Provider connection is not configured.")
    try:
        challenge = _consume_challenge(db, user, selected_provider, state)
        verifier = (
            challenge.context.get("code_verifier")
            if isinstance(challenge.context, dict)
            else None
        )
        if not isinstance(verifier, str):
            raise HTTPException(status_code=401, detail="Provider authorization could not be verified.")
        db.commit()
        if error or not code:
            return _connection_result_page(selected_provider, False)
        token_data = _exchange_token(
            selected_provider,
            code,
            verifier,
        )
        scopes = token_data.get("scope", "")
        granted_scopes = scopes.split() if isinstance(scopes, str) else []
        required_scopes = (
            {DRIVE_SCOPE}
            if selected_provider == "google_drive"
            else {"account_info.read", "files.content.write"}
        )
        if not required_scopes.issubset(granted_scopes):
            raise HTTPException(
                status_code=400,
                detail="Provider did not grant the required file-access permission.",
            )
        subject, label = _provider_account(selected_provider, token_data["access_token"])
        encryption_key = derive_encryption_key(get_settings().auth_encryption_key)
        connection = db.scalar(
            select(ExportProviderConnection).where(
                ExportProviderConnection.user_id == user.id,
                ExportProviderConnection.provider == selected_provider,
            )
        )
        if connection is None:
            connection = ExportProviderConnection(
                id=uuid4(),
                user_id=user.id,
                provider=selected_provider,
                provider_subject=subject,
                account_label=label,
                encrypted_access_token=b"",
            )
            db.add(connection)
        refresh_token = token_data.get("refresh_token")
        if not refresh_token and connection.encrypted_refresh_token:
            refresh_token = decrypt_secret(
                connection.encrypted_refresh_token,
                encryption_key,
                _token_aad(selected_provider, user.id, "refresh"),
            ).decode()
        if not isinstance(refresh_token, str):
            raise HTTPException(
                status_code=400,
                detail="Provider did not grant offline access. Reconnect and approve account access.",
            )
        expires_in = token_data.get("expires_in")
        connection.provider_subject = subject
        connection.account_label = label
        connection.encrypted_access_token = encrypt_secret(
            token_data["access_token"].encode(),
            encryption_key,
            _token_aad(selected_provider, user.id, "access"),
        )
        connection.encrypted_refresh_token = encrypt_secret(
            refresh_token.encode(),
            encryption_key,
            _token_aad(selected_provider, user.id, "refresh"),
        )
        connection.token_expires_at = (
            datetime.now(UTC) + timedelta(seconds=int(expires_in))
            if isinstance(expires_in, (int, float)) and expires_in > 0
            else None
        )
        connection.scopes = granted_scopes
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except (httpx.HTTPError, KeyError, ValueError, UnicodeDecodeError, TypeError) as error:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail="Provider account connection could not be verified.",
        ) from error
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Provider account connection changed. Restart the connection flow.",
        ) from error
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=503, detail="Provider account could not be saved.") from error
    return _connection_result_page(selected_provider, True)


def _revoke_provider_token(provider: Provider, token: str) -> bool:
    try:
        if provider == "google_drive":
            response = httpx.post(
                "https://oauth2.googleapis.com/revoke",
                data={"token": token},
                timeout=10,
            )
        else:
            response = httpx.post(
                "https://api.dropboxapi.com/2/auth/token/revoke",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
        return response.is_success
    except httpx.HTTPError:
        return False


@router.delete("/{provider}/connection")
def disconnect_export_provider(
    provider: str,
    user: Annotated[User, Depends(require_current_user)],
    db: DbSession,
    response: Response,
) -> dict[str, bool]:
    if provider not in {"google_drive", "dropbox"}:
        raise HTTPException(status_code=404, detail="Export provider not found.")
    selected_provider: Provider = provider
    try:
        connection = db.scalar(
            select(ExportProviderConnection).where(
                ExportProviderConnection.user_id == user.id,
                ExportProviderConnection.provider == selected_provider,
            )
        )
    except SQLAlchemyError as error:
        log_failure_event(logger, "proposal_delivery_destination_lookup_failed", error)
        raise HTTPException(status_code=503, detail="Provider connection could not be removed.") from error
    if connection is None:
        response.headers["Cache-Control"] = "no-store"
        return {"disconnected": True, "provider_revoked": True}
    token = None
    try:
        key = derive_encryption_key(get_settings().auth_encryption_key)
        encrypted = connection.encrypted_refresh_token or connection.encrypted_access_token
        purpose = "refresh" if connection.encrypted_refresh_token else "access"
        token = decrypt_secret(
            encrypted,
            key,
            _token_aad(selected_provider, user.id, purpose),
        ).decode()
    except (ValueError, UnicodeDecodeError):
        token = None
    revoked = _revoke_provider_token(selected_provider, token) if token else False
    try:
        db.delete(connection)
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=503, detail="Provider connection could not be removed.") from error
    response.headers["Cache-Control"] = "no-store"
    return {"disconnected": True, "provider_revoked": revoked}
