import base64
import hashlib
import json
import logging
import secrets
import smtplib
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from typing import Annotated, TypeAlias
from urllib.parse import urlencode
from uuid import UUID, uuid4

import httpx
import jwt
import pyotp
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import case, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.exceptions import WebAuthnException
from webauthn.helpers import options_to_json
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    UserVerificationRequirement,
)

from app.auth import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    normalize_email,
    random_token,
    validate_password,
    verify_password,
    verify_token,
)
from app.config import get_settings
from app.database import get_db
from app.demo import DEMO_USERNAME, verify_demo_password
from app.models import (
    AuthAuditEvent,
    AuthChallenge,
    AuthRateLimit,
    AuthSession,
    AuthToken,
    ExternalIdentity,
    PasskeyCredential,
    RecoveryCode,
    RefreshToken,
    TotpCredential,
    User,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["authentication"])
DbSession: TypeAlias = Annotated[Session, Depends(get_db)]
_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_REFRESH_COOKIE = "auth_refresh"
_ACCESS_COOKIE = "auth_access"
_CSRF_COOKIE = "auth_csrf"


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)


class EmailTokenRequest(BaseModel):
    token: str = Field(min_length=20, max_length=256)


class EmailRequest(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    email: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


class PasswordResetRequest(BaseModel):
    token: str = Field(min_length=20, max_length=256)
    password: str = Field(min_length=1, max_length=1024)


class TotpCodeRequest(BaseModel):
    code: str = Field(min_length=6, max_length=128)


class MfaChallengeRequest(TotpCodeRequest):
    challenge_id: UUID
    challenge: str = Field(min_length=20, max_length=256)


class PasskeyNameRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)


class PasskeyAuthenticationOptionsRequest(BaseModel):
    email: EmailStr | None = None


class PasskeyAuthenticationRequest(BaseModel):
    challenge_id: UUID
    credential: dict


class GoogleLinkRequest(BaseModel):
    password: str = Field(min_length=1, max_length=1024)
    totp_code: str | None = Field(default=None, min_length=6, max_length=128)


class ReauthenticationRequest(BaseModel):
    password: str = Field(min_length=1, max_length=1024)
    totp_code: str | None = Field(default=None, min_length=6, max_length=128)


def _require_secret_config() -> None:
    settings = get_settings()
    if (
        not settings.auth_enabled
        or not settings.auth_jwt_secret
        or len(settings.auth_jwt_secret.encode()) < 32
    ):
        raise HTTPException(
            status_code=503,
            detail="Authentication is not configured.",
        )


def _require_email_config() -> None:
    settings = get_settings()
    _require_secret_config()
    if not settings.smtp_host or not settings.auth_email_from:
        raise HTTPException(status_code=503, detail="Email delivery is not configured.")


def _send_email(recipient: str, subject: str, body: str) -> None:
    settings = get_settings()
    message = EmailMessage()
    message["From"] = settings.auth_email_from
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as client:
        if settings.smtp_starttls:
            client.starttls()
        if settings.smtp_username:
            client.login(settings.smtp_username, settings.smtp_password)
        client.send_message(message)


def _audit(
    db: Session,
    event_type: str,
    outcome: str,
    user_id: UUID | None = None,
    context: dict | None = None,
) -> None:
    db.add(
        AuthAuditEvent(
            user_id=user_id,
            event_type=event_type,
            outcome=outcome,
            context=context or {},
        )
    )


def _rate_limit(db: Session, request: Request, action: str, identifier: str = "") -> None:
    settings = get_settings()
    now = datetime.now(UTC)
    window_start = now - timedelta(seconds=settings.auth_rate_limit_window_seconds)
    client_host = request.client.host if request.client else "unknown"
    key = hash_token(f"{action}:{client_host}:{identifier.casefold()}")
    statement = insert(AuthRateLimit).values(
        key_hash=key,
        window_started_at=now,
        attempts=1,
    )
    statement = statement.on_conflict_do_update(
        index_elements=[AuthRateLimit.key_hash],
        set_={
            "attempts": case(
                (AuthRateLimit.window_started_at < window_start, 1),
                else_=AuthRateLimit.attempts + 1,
            ),
            "window_started_at": case(
                (AuthRateLimit.window_started_at < window_start, now),
                else_=AuthRateLimit.window_started_at,
            ),
        },
    ).returning(AuthRateLimit.attempts)
    attempts = db.execute(statement).scalar_one()
    db.commit()
    if attempts > settings.auth_rate_limit_attempts:
        raise HTTPException(status_code=429, detail="Too many attempts. Try again shortly.")


def _set_auth_cookies(response: Response, access: str, refresh: str, csrf: str) -> None:
    settings = get_settings()
    common = {
        "secure": settings.auth_cookie_secure,
        "samesite": settings.auth_cookie_samesite,
        "path": "/",
    }
    response.set_cookie(
        _ACCESS_COOKIE,
        access,
        httponly=True,
        max_age=settings.auth_access_token_minutes * 60,
        **common,
    )
    response.set_cookie(
        _REFRESH_COOKIE,
        refresh,
        httponly=True,
        max_age=settings.auth_refresh_token_days * 86400,
        **common,
    )
    response.set_cookie(
        _CSRF_COOKIE,
        csrf,
        httponly=False,
        max_age=settings.auth_refresh_token_days * 86400,
        **common,
    )


def clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    common = {
        "secure": settings.auth_cookie_secure,
        "samesite": settings.auth_cookie_samesite,
        "path": "/",
    }
    for name in (_ACCESS_COOKIE, _REFRESH_COOKIE, _CSRF_COOKIE):
        response.delete_cookie(name, **common)


def _require_csrf(request: Request) -> None:
    cookie = request.cookies.get(_CSRF_COOKIE)
    header = request.headers.get("x-csrf-token")
    if not cookie or not header or not secrets.compare_digest(cookie, header):
        raise HTTPException(status_code=403, detail="CSRF validation failed.")


def _create_session(db: Session, user: User) -> tuple[AuthSession, str, str, str]:
    settings = get_settings()
    now = datetime.now(UTC)
    db.scalar(select(User.id).where(User.id == user.id).with_for_update())
    absolute_expiry = now + timedelta(days=settings.auth_absolute_session_days)
    idle_expiry = min(
        now + timedelta(days=settings.auth_idle_session_days),
        absolute_expiry,
    )
    active_sessions = list(
        db.scalars(
            select(AuthSession)
            .where(
                AuthSession.user_id == user.id,
                AuthSession.revoked_at.is_(None),
                AuthSession.absolute_expires_at > now,
            )
            .order_by(AuthSession.created_at.desc())
        )
    )
    for old_session in active_sessions[max(0, settings.auth_max_active_sessions - 1) :]:
        old_session.revoked_at = now
        old_session.revoke_reason = "session_limit"
    session = AuthSession(
        user_id=user.id,
        family_id=uuid4(),
        idle_expires_at=idle_expiry,
        absolute_expires_at=absolute_expiry,
    )
    db.add(session)
    db.flush()
    refresh, refresh_id, refresh_expiry = create_refresh_token(
        user.id,
        session.id,
        settings,
        lifetime=min(
            timedelta(days=settings.auth_refresh_token_days),
            absolute_expiry - now,
        ),
    )
    access, _, _ = create_access_token(user.id, settings, session.id)
    db.add(
        RefreshToken(
            session_id=session.id,
            jti_hash=hash_token(refresh_id),
            expires_at=min(refresh_expiry, absolute_expiry),
        )
    )
    return session, access, refresh, random_token()


def _finish_login(
    db: Session,
    user: User,
    response: Response,
) -> dict:
    session, access, refresh, csrf = _create_session(db, user)
    _audit(db, "login", "success", user.id)
    db.commit()
    _set_auth_cookies(response, access, refresh, csrf)
    return {
        "access_token": access,
        "token_type": "Bearer",
        "expires_in": get_settings().auth_access_token_minutes * 60,
        "session_id": str(session.id),
    }


def _encrypted_totp_key() -> bytes:
    value = get_settings().auth_encryption_key
    if not value or len(value.encode()) < 32:
        raise HTTPException(status_code=503, detail="MFA encryption is not configured.")
    return hashlib.sha256(value.encode()).digest()


def _encrypt_totp(secret: str) -> bytes:
    nonce = secrets.token_bytes(12)
    return nonce + AESGCM(_encrypted_totp_key()).encrypt(nonce, secret.encode(), None)


def _decrypt_totp(encrypted: bytes) -> str:
    try:
        return AESGCM(_encrypted_totp_key()).decrypt(
            encrypted[:12], encrypted[12:], None
        ).decode()
    except (InvalidTag, UnicodeDecodeError) as error:
        logger.exception("Could not decrypt a TOTP credential.")
        raise HTTPException(status_code=503, detail="MFA credential is unavailable.") from error


def _verify_totp(secret: str, code: str) -> int | None:
    if not code.isdigit() or len(code) != 6:
        return None
    totp = pyotp.TOTP(secret)
    now_step = int(datetime.now(UTC).timestamp() // totp.interval)
    for step in (now_step - 1, now_step, now_step + 1):
        if totp.verify(code, for_time=step * totp.interval, valid_window=0):
            return step
    return None


def _send_security_email(recipient: str, subject: str, body: str) -> None:
    try:
        _send_email(recipient, subject, body)
    except (smtplib.SMTPException, OSError) as error:
        logger.exception("Could not deliver an authentication email.")
        raise HTTPException(status_code=503, detail="Email delivery is temporarily unavailable.") from error


def _verify_second_factor(
    db: Session,
    user: User,
    credential: TotpCredential,
    code: str,
) -> bool:
    step = _verify_totp(_decrypt_totp(credential.encrypted_secret), code)
    if step is not None:
        if credential.last_used_step is not None and step <= credential.last_used_step:
            return False
        credential.last_used_step = step
        return True
    recovery = db.scalar(
        select(RecoveryCode).where(
            RecoveryCode.user_id == user.id,
            RecoveryCode.code_hash == hash_token(code),
            RecoveryCode.used_at.is_(None),
        )
    )
    if recovery is None:
        return False
    recovery.used_at = datetime.now(UTC)
    _audit(db, "recovery_code_used", "success", user.id)
    return True


def _current_user(request: Request, db: Session) -> User:
    _require_secret_config()
    access = request.cookies.get(_ACCESS_COOKIE)
    authorization = request.headers.get("authorization", "")
    if authorization.startswith("Bearer "):
        access = authorization[7:]
    if not access:
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        claims = verify_token(access, get_settings(), "access")
        user_id = UUID(claims["sub"])
        session_id = UUID(claims["sid"])
    except (ValueError, KeyError) as error:
        raise HTTPException(status_code=401, detail="Authentication required.") from error
    session = db.get(AuthSession, session_id)
    user = db.get(User, user_id)
    now = datetime.now(UTC)
    if (
        session is None
        or user is None
        or session.user_id != user.id
        or session.revoked_at is not None
        or session.idle_expires_at <= now
        or session.absolute_expires_at <= now
        or user.status != "active"
    ):
        raise HTTPException(status_code=401, detail="Authentication required.")
    if request.cookies.get(_ACCESS_COOKIE) and request.method in _UNSAFE_METHODS:
        _require_csrf(request)
    session.last_used_at = now
    session.idle_expires_at = min(
        now + timedelta(days=get_settings().auth_idle_session_days),
        session.absolute_expires_at,
    )
    db.commit()
    return user


def require_current_user(request: Request, db: DbSession) -> User:
    return _current_user(request, db)


@router.post("/signup", status_code=202)
def signup(payload: SignupRequest, request: Request, db: DbSession) -> dict[str, str]:
    _require_email_config()
    email = normalize_email(str(payload.email))
    try:
        validate_password(payload.password)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    _rate_limit(db, request, "signup", email)
    existing = db.scalar(select(User).where(User.email == email))
    if existing is None:
        user = User(email=email, password_hash=hash_password(payload.password))
        db.add(user)
        try:
            db.flush()
            token = random_token()
            db.add(
                AuthToken(
                    user_id=user.id,
                    purpose="email_verification",
                    token_hash=hash_token(token),
                    expires_at=datetime.now(UTC) + timedelta(hours=24),
                )
            )
            _audit(db, "signup", "success", user.id)
            db.commit()
            _send_security_email(
                email,
                "Verify your email",
                f"Complete verification by submitting this one-time token: {token}",
            )
        except IntegrityError:
            db.rollback()
        except SQLAlchemyError:
            db.rollback()
            logger.exception("Could not complete the signup email operation.")
            raise HTTPException(status_code=503, detail="Signup could not be completed.")
        except (smtplib.SMTPException, OSError):
            logger.exception("Could not deliver the signup verification email.")
            raise HTTPException(status_code=503, detail="Signup email could not be delivered.")
    return {"message": "If signup can be completed, verification instructions will be sent."}


@router.get("/providers")
def available_authentication_providers() -> dict[str, bool]:
    settings = get_settings()
    return {
        "google": bool(
            settings.auth_enabled
            and settings.auth_jwt_secret
            and len(settings.auth_jwt_secret.encode()) >= 32
            and settings.google_client_id
            and settings.google_client_secret
        ),
        "demo": bool(
            settings.auth_enabled
            and settings.auth_jwt_secret
            and len(settings.auth_jwt_secret.encode()) >= 32
            and settings.demo_mode_enabled
        ),
    }


@router.post("/verify-email")
def verify_email(payload: EmailTokenRequest, db: DbSession) -> dict[str, str]:
    _require_secret_config()
    token = db.scalar(
        select(AuthToken).where(
            AuthToken.token_hash == hash_token(payload.token),
            AuthToken.purpose == "email_verification",
            AuthToken.used_at.is_(None),
            AuthToken.revoked_at.is_(None),
        )
    )
    now = datetime.now(UTC)
    if token is None or token.expires_at <= now:
        raise HTTPException(status_code=400, detail="Verification token is invalid or expired.")
    user = db.get(User, token.user_id)
    if user is None or user.status != "pending_verification":
        raise HTTPException(status_code=400, detail="Verification token is invalid or expired.")
    token.used_at = now
    user.status = "active"
    user.email_verified_at = now
    _audit(db, "email_verification", "success", user.id)
    db.commit()
    return {"message": "Email verified. You can now sign in."}


@router.post("/verify-email/resend", status_code=202)
def resend_verification(
    payload: EmailRequest,
    request: Request,
    db: DbSession,
) -> dict[str, str]:
    _require_email_config()
    email = normalize_email(str(payload.email))
    _rate_limit(db, request, "verify-resend", email)
    user = db.scalar(
        select(User).where(User.email == email, User.status == "pending_verification")
    )
    if user is not None:
        now = datetime.now(UTC)
        db.execute(
            update(AuthToken)
            .where(
                AuthToken.user_id == user.id,
                AuthToken.purpose == "email_verification",
                AuthToken.used_at.is_(None),
                AuthToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        token = random_token()
        db.add(
            AuthToken(
                user_id=user.id,
                purpose="email_verification",
                token_hash=hash_token(token),
                expires_at=now + timedelta(hours=24),
            )
        )
        db.commit()
        _send_security_email(user.email, "Verify your email", f"One-time token: {token}")
    return {"message": "If the account needs verification, instructions will be sent."}


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: DbSession,
) -> dict:
    _require_secret_config()
    settings = get_settings()
    demo_login = settings.demo_mode_enabled and payload.email.strip().casefold() == DEMO_USERNAME
    identifier = DEMO_USERNAME if demo_login else payload.email
    _rate_limit(db, request, "login", identifier)
    if demo_login:
        user = db.scalar(select(User).where(User.email == "demo@localhost.invalid"))
    else:
        try:
            email = normalize_email(payload.email)
        except ValueError:
            email = ""
        user = db.scalar(select(User).where(User.email == email)) if email else None
    if (
        user is None
        or user.status != "active"
        or user.password_hash is None
        or not (
            verify_demo_password(payload.password, user.password_hash)
            if demo_login
            else verify_password(user.password_hash, payload.password)
        )
    ):
        _audit(db, "login", "failure", user.id if user else None)
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if user.mfa_enabled:
        challenge = uuid4()
        challenge_token = random_token()
        db.add(
            AuthChallenge(
                id=challenge,
                user_id=user.id,
                purpose="mfa_login",
                challenge=hash_token(challenge_token),
                expires_at=datetime.now(UTC) + timedelta(minutes=5),
                context={},
            )
        )
        db.commit()
        return {"mfa_required": True, "challenge_id": str(challenge), "challenge": challenge_token}
    return _finish_login(db, user, response)


@router.post("/mfa/totp/verify")
def verify_login_totp(
    payload: MfaChallengeRequest,
    request: Request,
    response: Response,
    db: DbSession,
) -> dict:
    _require_secret_config()
    _rate_limit(db, request, "mfa-login", str(payload.challenge_id))
    record = db.get(AuthChallenge, payload.challenge_id)
    now = datetime.now(UTC)
    if (
        record is None
        or record.purpose != "mfa_login"
        or record.consumed_at is not None
        or record.expires_at <= now
        or not secrets.compare_digest(record.challenge, hash_token(payload.challenge))
    ):
        raise HTTPException(status_code=401, detail="Authentication challenge is invalid.")
    user = db.get(User, record.user_id)
    credential = db.scalar(
        select(TotpCredential).where(
            TotpCredential.user_id == record.user_id,
            TotpCredential.pending.is_(False),
            TotpCredential.revoked_at.is_(None),
        )
    )
    if user is None or user.status != "active" or credential is None:
        raise HTTPException(status_code=401, detail="Authentication challenge is invalid.")
    if not _verify_second_factor(db, user, credential, payload.code):
        raise HTTPException(status_code=401, detail="Invalid authentication code.")
    record.consumed_at = now
    return _finish_login(db, user, response)


@router.post("/refresh")
def refresh(request: Request, response: Response, db: DbSession) -> dict:
    _require_secret_config()
    _require_csrf(request)
    _rate_limit(db, request, "refresh")
    raw_token = request.cookies.get(_REFRESH_COOKIE)
    if not raw_token:
        raise HTTPException(status_code=401, detail="Refresh authentication is required.")
    try:
        claims = verify_token(raw_token, get_settings(), "refresh")
        session_id = UUID(claims["sid"])
    except (ValueError, KeyError) as error:
        clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="Refresh authentication is required.") from error
    stored = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.jti_hash == hash_token(claims["jti"]))
        .with_for_update()
    )
    session = db.get(AuthSession, session_id)
    user = db.get(User, UUID(claims["sub"]))
    now = datetime.now(UTC)
    if stored is not None and stored.used_at is not None and session is not None:
        db.execute(
            update(AuthSession)
            .where(AuthSession.family_id == session.family_id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=now, revoke_reason="refresh_reuse")
        )
        _audit(db, "refresh_reuse", "revoked", user.id if user else None)
        db.commit()
        clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="Refresh token reuse detected.")
    if (
        stored is None
        or stored.revoked_at is not None
        or stored.expires_at <= now
        or session is None
        or session.revoked_at is not None
        or session.idle_expires_at <= now
        or session.absolute_expires_at <= now
        or user is None
        or user.status != "active"
    ):
        clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="Refresh authentication is required.")
    stored.used_at = now
    session.last_used_at = now
    session.idle_expires_at = min(
        now + timedelta(days=get_settings().auth_idle_session_days),
        session.absolute_expires_at,
    )
    new_refresh, new_id, new_expiry = create_refresh_token(
        user.id,
        session.id,
        get_settings(),
        lifetime=min(
            timedelta(days=get_settings().auth_refresh_token_days),
            session.absolute_expires_at - now,
        ),
    )
    access, _, _ = create_access_token(user.id, get_settings(), session.id)
    db.add(
        RefreshToken(
            session_id=session.id,
            jti_hash=hash_token(new_id),
            expires_at=min(new_expiry, session.absolute_expires_at),
        )
    )
    csrf = random_token()
    _audit(db, "refresh", "success", user.id)
    db.commit()
    _set_auth_cookies(response, access, new_refresh, csrf)
    return {
        "access_token": access,
        "token_type": "Bearer",
        "expires_in": get_settings().auth_access_token_minutes * 60,
    }


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: DbSession) -> Response:
    _require_secret_config()
    _require_csrf(request)
    raw_token = request.cookies.get(_REFRESH_COOKIE)
    if raw_token:
        try:
            claims = verify_token(raw_token, get_settings(), "refresh")
            session_id = UUID(claims["sid"])
            session = db.get(AuthSession, session_id)
            if session is not None:
                session.revoked_at = datetime.now(UTC)
                session.revoke_reason = "logout"
                _audit(db, "logout", "success", session.user_id)
                db.commit()
        except (ValueError, KeyError):
            db.rollback()
    clear_auth_cookies(response)
    return response


@router.post("/password/forgot", status_code=202)
def forgot_password(
    payload: EmailRequest,
    request: Request,
    db: DbSession,
) -> dict[str, str]:
    _require_email_config()
    email = normalize_email(str(payload.email))
    _rate_limit(db, request, "password-forgot", email)
    user = db.scalar(select(User).where(User.email == email, User.status == "active"))
    if user is not None:
        now = datetime.now(UTC)
        token = random_token()
        db.add(
            AuthToken(
                user_id=user.id,
                purpose="password_reset",
                token_hash=hash_token(token),
                expires_at=now + timedelta(minutes=30),
            )
        )
        db.commit()
        _send_security_email(user.email, "Reset your password", f"One-time token: {token}")
    return {"message": "If the account exists, password reset instructions will be sent."}


@router.post("/password/reset")
def reset_password(
    payload: PasswordResetRequest,
    request: Request,
    db: DbSession,
) -> dict[str, str]:
    _require_secret_config()
    try:
        validate_password(payload.password)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    _rate_limit(db, request, "password-reset", hash_token(payload.token))
    token = db.scalar(
        select(AuthToken).where(
            AuthToken.token_hash == hash_token(payload.token),
            AuthToken.purpose == "password_reset",
            AuthToken.used_at.is_(None),
            AuthToken.revoked_at.is_(None),
        )
    )
    now = datetime.now(UTC)
    if token is None or token.expires_at <= now:
        raise HTTPException(status_code=400, detail="Password reset token is invalid or expired.")
    user = db.get(User, token.user_id)
    if user is None or user.status != "active":
        raise HTTPException(status_code=400, detail="Password reset token is invalid or expired.")
    user.password_hash = hash_password(payload.password)
    token.used_at = now
    db.execute(
        update(AuthToken)
        .where(
            AuthToken.user_id == user.id,
            AuthToken.purpose == "password_reset",
            AuthToken.id != token.id,
            AuthToken.used_at.is_(None),
            AuthToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=now, revoke_reason="password_reset")
    )
    _audit(db, "password_reset", "success", user.id)
    db.commit()
    return {"message": "Password reset complete. Sign in with your new password."}


@router.post("/mfa/totp/enroll")
def enroll_totp(
    request: Request,
    user: Annotated[User, Depends(require_current_user)],
    db: DbSession,
) -> dict:
    _rate_limit(db, request, "totp-enroll", str(user.id))
    secret = pyotp.random_base32()
    credential = db.scalar(select(TotpCredential).where(TotpCredential.user_id == user.id))
    if credential is None:
        credential = TotpCredential(
            user_id=user.id,
            encrypted_secret=_encrypt_totp(secret),
            pending=True,
        )
        db.add(credential)
    else:
        credential.encrypted_secret = _encrypt_totp(secret)
        credential.pending = True
        credential.last_used_step = None
        credential.confirmed_at = None
        credential.revoked_at = None
    db.commit()
    uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=get_settings().webauthn_rp_name)
    return {"secret": secret, "provisioning_uri": uri}


@router.post("/mfa/totp/confirm")
def confirm_totp(
    payload: TotpCodeRequest,
    request: Request,
    user: Annotated[User, Depends(require_current_user)],
    db: DbSession,
) -> dict[str, list[str]]:
    _rate_limit(db, request, "totp-confirm", str(user.id))
    credential = db.scalar(
        select(TotpCredential).where(
            TotpCredential.user_id == user.id,
            TotpCredential.pending.is_(True),
            TotpCredential.revoked_at.is_(None),
        )
    )
    if credential is None:
        raise HTTPException(status_code=409, detail="No pending TOTP enrollment exists.")
    step = _verify_totp(_decrypt_totp(credential.encrypted_secret), payload.code)
    if step is None:
        raise HTTPException(status_code=401, detail="Invalid authentication code.")
    credential.pending = False
    credential.last_used_step = step
    credential.confirmed_at = datetime.now(UTC)
    user.mfa_enabled = True
    codes = [secrets.token_urlsafe(9) for _ in range(10)]
    db.execute(
        RecoveryCode.__table__.delete().where(RecoveryCode.user_id == user.id)
    )
    db.add_all(
        RecoveryCode(user_id=user.id, code_hash=hash_token(code))
        for code in codes
    )
    _audit(db, "totp_enrollment", "success", user.id)
    db.commit()
    return {"recovery_codes": codes}


@router.post("/mfa/totp/disable")
def disable_totp(
    payload: TotpCodeRequest,
    request: Request,
    user: Annotated[User, Depends(require_current_user)],
    db: DbSession,
) -> dict[str, str]:
    _rate_limit(db, request, "totp-disable", str(user.id))
    credential = db.scalar(
        select(TotpCredential).where(
            TotpCredential.user_id == user.id,
            TotpCredential.pending.is_(False),
            TotpCredential.revoked_at.is_(None),
        )
    )
    if credential is None:
        raise HTTPException(status_code=409, detail="TOTP is not enabled.")
    if not _verify_second_factor(db, user, credential, payload.code):
        raise HTTPException(status_code=401, detail="Invalid authentication code.")
    now = datetime.now(UTC)
    credential.revoked_at = now
    user.mfa_enabled = False
    db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=now, revoke_reason="totp_disabled")
    )
    _audit(db, "totp_disabled", "success", user.id)
    db.commit()
    return {"message": "TOTP has been disabled. Sign in again."}


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


@router.get("/oidc/google/start")
def google_oidc_start(request: Request, db: DbSession) -> Response:
    settings = get_settings()
    _require_secret_config()
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured.")
    _rate_limit(db, request, "google-oidc-start")
    state = random_token()
    nonce = random_token()
    verifier = secrets.token_urlsafe(48)
    challenge = _b64url_encode(hashlib.sha256(verifier.encode()).digest())
    callback = f"{settings.auth_public_base_url.rstrip('/')}/api/auth/oidc/google/callback"
    auth_challenge = AuthChallenge(
        purpose="google_oidc",
        challenge=state,
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
        context={"nonce": nonce, "verifier": verifier},
    )
    db.add(auth_challenge)
    db.commit()
    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": callback,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "nonce": nonce,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
    )
    return Response(
        status_code=302,
        headers={"Location": f"https://accounts.google.com/o/oauth2/v2/auth?{query}"},
    )


@router.post("/oidc/google/link/start")
def google_oidc_link_start(
    payload: GoogleLinkRequest,
    request: Request,
    user: Annotated[User, Depends(require_current_user)],
    db: DbSession,
) -> Response:
    settings = get_settings()
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured.")
    _rate_limit(db, request, "google-oidc-link", str(user.id))
    if user.password_hash is None or not verify_password(user.password_hash, payload.password):
        raise HTTPException(status_code=401, detail="Recent account verification is required.")
    if user.mfa_enabled:
        credential = db.scalar(
            select(TotpCredential).where(
                TotpCredential.user_id == user.id,
                TotpCredential.pending.is_(False),
                TotpCredential.revoked_at.is_(None),
            )
        )
        if (
            credential is None
            or payload.totp_code is None
            or not _verify_second_factor(db, user, credential, payload.totp_code)
        ):
            raise HTTPException(status_code=401, detail="Recent account verification is required.")
    state = random_token()
    nonce = random_token()
    verifier = secrets.token_urlsafe(48)
    code_challenge = _b64url_encode(hashlib.sha256(verifier.encode()).digest())
    callback = f"{settings.auth_public_base_url.rstrip('/')}/api/auth/oidc/google/callback"
    db.add(
        AuthChallenge(
            user_id=user.id,
            purpose="google_oidc_link",
            challenge=state,
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
            context={"nonce": nonce, "verifier": verifier},
        )
    )
    db.commit()
    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": callback,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    return Response(
        status_code=302,
        headers={"Location": f"https://accounts.google.com/o/oauth2/v2/auth?{query}"},
    )


@router.get("/oidc/google/callback", response_model=None)
def google_oidc_callback(
    request: Request,
    response: Response,
    db: DbSession,
    state: str,
    code: str | None = None,
    error: str | None = None,
) -> Response | dict[str, str | bool]:
    settings = get_settings()
    _require_secret_config()
    if error or not code or not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=401, detail="Google sign-in could not be completed.")
    _rate_limit(db, request, "google-oidc-callback")
    challenge = db.scalar(
        select(AuthChallenge).where(
            AuthChallenge.purpose.in_(("google_oidc", "google_oidc_link")),
            AuthChallenge.challenge == state,
            AuthChallenge.consumed_at.is_(None),
        )
    )
    now = datetime.now(UTC)
    if challenge is None or challenge.expires_at <= now:
        raise HTTPException(status_code=401, detail="Google sign-in could not be completed.")
    callback_url = f"{settings.auth_public_base_url.rstrip('/')}/api/auth/oidc/google/callback"
    try:
        token_response = httpx.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": code,
                "code_verifier": challenge.context["verifier"],
                "grant_type": "authorization_code",
                "redirect_uri": callback_url,
            },
            timeout=10,
        )
        token_response.raise_for_status()
        identity_token = token_response.json()["id_token"]
        keys_response = httpx.get("https://www.googleapis.com/oauth2/v3/certs", timeout=10)
        keys_response.raise_for_status()
        jwk_set = jwt.PyJWKSet.from_dict(keys_response.json())
        key_id = jwt.get_unverified_header(identity_token).get("kid")
        signing_key = next(key.key for key in jwk_set.keys if key.key_id == key_id)
        claims = jwt.decode(
            identity_token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.google_client_id,
            issuer=["https://accounts.google.com", "accounts.google.com"],
            options={"require": ["sub", "iss", "aud", "exp", "iat", "nonce"]},
        )
    except (httpx.HTTPError, KeyError, StopIteration, jwt.PyJWTError, ValueError) as error:
        logger.info("Google OIDC callback rejected an invalid provider response.")
        raise HTTPException(
            status_code=401,
            detail="Google sign-in could not be verified.",
        ) from error
    if claims.get("nonce") != challenge.context.get("nonce") or claims.get("email_verified") is not True:
        raise HTTPException(status_code=401, detail="Google sign-in could not be verified.")
    try:
        email = normalize_email(claims["email"])
        subject = str(claims["sub"])
    except (KeyError, ValueError) as error:
        raise HTTPException(status_code=401, detail="Google sign-in could not be verified.") from error
    identity = db.scalar(
        select(ExternalIdentity).where(
            ExternalIdentity.provider == "google",
            ExternalIdentity.provider_subject == subject,
        )
    )
    if challenge.purpose == "google_oidc_link":
        linked_user = db.get(User, challenge.user_id)
        if linked_user is None or linked_user.status != "active":
            raise HTTPException(status_code=401, detail="Google account linking could not be completed.")
        if identity is not None and identity.user_id != linked_user.id:
            raise HTTPException(status_code=409, detail="Google identity is already linked.")
        if identity is None:
            db.add(
                ExternalIdentity(
                    user_id=linked_user.id,
                    provider="google",
                    provider_subject=subject,
                    provider_email=email,
                    email_verified=True,
                )
            )
        challenge.consumed_at = now
        _audit(db, "provider_linked", "success", linked_user.id, {"provider": "google"})
        db.commit()
        response.status_code = 303
        response.headers["Location"] = "/"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response
    if identity is not None:
        user = db.get(User, identity.user_id)
    else:
        user = db.scalar(select(User).where(User.email == email))
        if user is not None:
            raise HTTPException(
                status_code=409,
                detail="Sign in with the existing method before linking Google.",
            )
        user = User(
            email=email,
            status="active",
            email_verified_at=now,
        )
        db.add(user)
        db.flush()
        identity = ExternalIdentity(
            user_id=user.id,
            provider="google",
            provider_subject=subject,
            provider_email=email,
            email_verified=True,
        )
        db.add(identity)
    challenge.consumed_at = now
    if user is None or user.status != "active":
        raise HTTPException(status_code=401, detail="Google sign-in could not be completed.")
    if user.mfa_enabled:
        mfa_challenge = random_token()
        mfa_record = AuthChallenge(
            user_id=user.id,
            purpose="mfa_login",
            challenge=hash_token(mfa_challenge),
            expires_at=now + timedelta(minutes=5),
            context={},
        )
        db.add(mfa_record)
        _audit(db, "login", "mfa_required", user.id, {"provider": "google"})
        db.commit()
        return {
            "mfa_required": True,
            "challenge_id": str(mfa_record.id),
            "challenge": mfa_challenge,
        }
    _audit(db, "login", "success", user.id, {"provider": "google"})
    _, access, refresh, csrf = _create_session(db, user)
    db.commit()
    _set_auth_cookies(response, access, refresh, csrf)
    response.status_code = 303
    response.headers["Location"] = "/"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@router.post("/passkeys/register/options")
def passkey_registration_options(
    payload: PasskeyNameRequest,
    request: Request,
    user: Annotated[User, Depends(require_current_user)],
    db: DbSession,
) -> dict:
    _rate_limit(db, request, "passkey-register-options", str(user.id))
    settings = get_settings()
    challenge_bytes = secrets.token_bytes(32)
    challenge = _b64url_encode(challenge_bytes)
    existing = db.scalars(
        select(PasskeyCredential).where(
            PasskeyCredential.user_id == user.id,
            PasskeyCredential.revoked_at.is_(None),
        )
    )
    excluded = [
        PublicKeyCredentialDescriptor(id=_b64url_decode(item.credential_id))
        for item in existing
    ]
    options = generate_registration_options(
        rp_id=settings.webauthn_rp_id,
        rp_name=settings.webauthn_rp_name,
        user_id=user.id.bytes,
        user_name=user.email,
        user_display_name=user.email,
        challenge=challenge_bytes,
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.REQUIRED
        ),
        exclude_credentials=excluded,
    )
    record = AuthChallenge(
        user_id=user.id,
        purpose="passkey_registration",
        challenge=challenge,
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
        context={"display_name": payload.display_name.strip()},
    )
    db.add(record)
    db.commit()
    return {"challenge_id": str(record.id), "options": json.loads(options_to_json(options))}


@router.post("/passkeys/register/verify")
def verify_passkey_registration(
    payload: PasskeyAuthenticationRequest,
    request: Request,
    user: Annotated[User, Depends(require_current_user)],
    db: DbSession,
) -> dict[str, str]:
    _rate_limit(db, request, "passkey-register-verify", str(user.id))
    challenge = db.get(AuthChallenge, payload.challenge_id)
    now = datetime.now(UTC)
    if (
        challenge is None
        or challenge.user_id != user.id
        or challenge.purpose != "passkey_registration"
        or challenge.consumed_at is not None
        or challenge.expires_at <= now
    ):
        raise HTTPException(status_code=400, detail="Passkey challenge is invalid or expired.")
    try:
        verified = verify_registration_response(
            credential=payload.credential,
            expected_challenge=_b64url_decode(challenge.challenge),
            expected_rp_id=get_settings().webauthn_rp_id,
            expected_origin=get_settings().webauthn_origin,
            require_user_verification=True,
        )
    except WebAuthnException as error:
        raise HTTPException(status_code=400, detail="Passkey registration could not be verified.") from error
    credential_id = _b64url_encode(verified.credential_id)
    transports = payload.credential.get("response", {}).get("transports", [])
    db.add(
        PasskeyCredential(
            user_id=user.id,
            credential_id=credential_id,
            public_key=verified.credential_public_key,
            sign_count=verified.sign_count,
            transports=transports,
            display_name=challenge.context["display_name"],
        )
    )
    challenge.consumed_at = now
    _audit(db, "passkey_registered", "success", user.id)
    db.commit()
    return {"message": "Passkey registered."}


@router.post("/passkeys/authenticate/options")
def passkey_authentication_options(
    payload: PasskeyAuthenticationOptionsRequest,
    request: Request,
    db: DbSession,
) -> dict:
    _require_secret_config()
    _rate_limit(db, request, "passkey-auth-options")
    settings = get_settings()
    user = None
    credentials = []
    if payload.email:
        email = normalize_email(str(payload.email))
        user = db.scalar(select(User).where(User.email == email, User.status == "active"))
        if user is not None:
            credentials = list(
                db.scalars(
                    select(PasskeyCredential).where(
                        PasskeyCredential.user_id == user.id,
                        PasskeyCredential.revoked_at.is_(None),
                    )
                )
            )
    challenge_bytes = secrets.token_bytes(32)
    options = generate_authentication_options(
        rp_id=settings.webauthn_rp_id,
        challenge=challenge_bytes,
        allow_credentials=[
            PublicKeyCredentialDescriptor(id=_b64url_decode(item.credential_id))
            for item in credentials
        ],
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    record = AuthChallenge(
        user_id=user.id if user else None,
        purpose="passkey_authentication",
        challenge=_b64url_encode(challenge_bytes),
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
        context={},
    )
    db.add(record)
    db.commit()
    return {"challenge_id": str(record.id), "options": json.loads(options_to_json(options))}


@router.post("/passkeys/authenticate/verify")
def verify_passkey_authentication(
    payload: PasskeyAuthenticationRequest,
    request: Request,
    response: Response,
    db: DbSession,
) -> dict:
    _require_secret_config()
    _rate_limit(db, request, "passkey-auth-verify")
    challenge = db.get(AuthChallenge, payload.challenge_id)
    credential_value = payload.credential.get("rawId")
    if not isinstance(credential_value, str):
        raise HTTPException(status_code=400, detail="Passkey assertion is invalid.")
    credential_id = _b64url_encode(_b64url_decode(credential_value))
    credential = db.scalar(
        select(PasskeyCredential).where(
            PasskeyCredential.credential_id == credential_id,
            PasskeyCredential.revoked_at.is_(None),
        )
    )
    now = datetime.now(UTC)
    if (
        challenge is None
        or challenge.purpose != "passkey_authentication"
        or challenge.consumed_at is not None
        or challenge.expires_at <= now
        or credential is None
        or challenge.user_id != credential.user_id
    ):
        raise HTTPException(status_code=401, detail="Passkey assertion is invalid.")
    try:
        verified = verify_authentication_response(
            credential=payload.credential,
            expected_challenge=_b64url_decode(challenge.challenge),
            expected_rp_id=get_settings().webauthn_rp_id,
            expected_origin=get_settings().webauthn_origin,
            credential_public_key=credential.public_key,
            credential_current_sign_count=credential.sign_count,
            require_user_verification=True,
        )
    except WebAuthnException as error:
        raise HTTPException(status_code=401, detail="Passkey assertion is invalid.") from error
    user = db.get(User, credential.user_id)
    if user is None or user.status != "active":
        raise HTTPException(status_code=401, detail="Passkey assertion is invalid.")
    challenge.consumed_at = now
    credential.sign_count = verified.new_sign_count
    credential.last_used_at = now
    session, access, refresh, csrf = _create_session(db, user)
    _audit(db, "login", "success", user.id, {"method": "passkey"})
    db.commit()
    _set_auth_cookies(response, access, refresh, csrf)
    return {
        "access_token": access,
        "token_type": "Bearer",
        "expires_in": get_settings().auth_access_token_minutes * 60,
        "session_id": str(session.id),
    }


@router.get("/passkeys")
def list_passkeys(
    user: Annotated[User, Depends(require_current_user)],
    db: DbSession,
) -> list[dict]:
    credentials = db.scalars(
        select(PasskeyCredential).where(
            PasskeyCredential.user_id == user.id,
            PasskeyCredential.revoked_at.is_(None),
        )
    )
    return [
        {
            "id": str(item.id),
            "display_name": item.display_name,
            "created_at": item.created_at,
            "last_used_at": item.last_used_at,
            "transports": item.transports,
        }
        for item in credentials
    ]


@router.delete("/passkeys/{credential_id}", status_code=204)
def revoke_passkey(
    credential_id: UUID,
    payload: ReauthenticationRequest,
    request: Request,
    user: Annotated[User, Depends(require_current_user)],
    db: DbSession,
) -> Response:
    _rate_limit(db, request, "passkey-revoke", str(user.id))
    credential = db.get(PasskeyCredential, credential_id)
    if credential is None or credential.user_id != user.id or credential.revoked_at is not None:
        raise HTTPException(status_code=404, detail="Passkey not found.")
    if user.password_hash is None or not verify_password(user.password_hash, payload.password):
        raise HTTPException(status_code=401, detail="Recent account verification is required.")
    if user.mfa_enabled:
        totp = db.scalar(
            select(TotpCredential).where(
                TotpCredential.user_id == user.id,
                TotpCredential.pending.is_(False),
                TotpCredential.revoked_at.is_(None),
            )
        )
        if (
            totp is None
            or payload.totp_code is None
            or not _verify_second_factor(db, user, totp, payload.totp_code)
        ):
            raise HTTPException(status_code=401, detail="Recent account verification is required.")
    credential.revoked_at = datetime.now(UTC)
    _audit(db, "passkey_revoked", "success", user.id)
    db.commit()
    return Response(status_code=204)


@router.get("/sessions")
def list_sessions(user: Annotated[User, Depends(require_current_user)], db: DbSession) -> list[dict]:
    now = datetime.now(UTC)
    sessions = db.scalars(
        select(AuthSession).where(
            AuthSession.user_id == user.id,
            AuthSession.revoked_at.is_(None),
            AuthSession.idle_expires_at > now,
            AuthSession.absolute_expires_at > now,
        )
    )
    return [
        {
            "id": str(session.id),
            "created_at": session.created_at,
            "last_used_at": session.last_used_at,
            "idle_expires_at": session.idle_expires_at,
            "absolute_expires_at": session.absolute_expires_at,
        }
        for session in sessions
    ]


@router.delete("/sessions/{session_id}", status_code=204)
def revoke_session(
    session_id: UUID,
    user: Annotated[User, Depends(require_current_user)],
    db: DbSession,
) -> Response:
    session = db.get(AuthSession, session_id)
    if session is None or session.user_id != user.id or session.revoked_at is not None:
        raise HTTPException(status_code=404, detail="Session not found.")
    session.revoked_at = datetime.now(UTC)
    session.revoke_reason = "user_revoked"
    _audit(db, "session_revoked", "success", user.id)
    db.commit()
    return Response(status_code=204)
