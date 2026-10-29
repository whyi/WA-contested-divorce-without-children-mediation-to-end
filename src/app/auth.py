import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from email_validator import EmailNotValidError, validate_email
from pwdlib import PasswordHash

from app.config import Settings

_PASSWORD_HASHER = PasswordHash.recommended()
_COMMON_PASSWORDS = {
    "password",
    "password123!",
    "password123",
    "qwerty123",
    "letmein123",
    "welcome123",
    "iloveyou123",
}


class AuthConfigurationError(RuntimeError):
    """Raised when authentication is used without required secrets."""


def normalize_email(email: str) -> str:
    try:
        normalized = validate_email(email.strip(), check_deliverability=False).normalized
    except EmailNotValidError as error:
        raise ValueError("Enter a valid email address.") from error
    return normalized.casefold()


def validate_password(password: str) -> None:
    if password.casefold() in _COMMON_PASSWORDS:
        raise ValueError("Password is too common.")
    if len(password) < 15:
        raise ValueError("Password must be at least 15 characters long.")
    if len(password.encode("utf-8")) > 1024:
        raise ValueError("Password must not exceed 1024 characters.")
    if len(set(password)) < 5:
        raise ValueError("Password is too common.")


def hash_password(password: str) -> str:
    validate_password(password)
    return _PASSWORD_HASHER.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _PASSWORD_HASHER.verify(password, password_hash)
    except (ValueError, TypeError):
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _signing_secret(settings: Settings) -> str:
    secret = settings.auth_jwt_secret
    if secret is None or len(secret.encode("utf-8")) < 32:
        raise AuthConfigurationError(
            "Authentication requires an AUTH_JWT_SECRET of at least 32 bytes."
        )
    return secret


def create_token(
    user_id: UUID,
    session_id: UUID,
    settings: Settings,
    token_type: str,
    lifetime: timedelta,
) -> tuple[str, str, datetime]:
    now = datetime.now(UTC)
    expires_at = now + lifetime
    token_id = str(uuid4())
    claims = {
        "sub": str(user_id),
        "sid": str(session_id),
        "jti": token_id,
        "iss": settings.auth_issuer,
        "aud": settings.auth_audience,
        "iat": now,
        "exp": expires_at,
        "token_type": token_type,
    }
    token = jwt.encode(claims, _signing_secret(settings), algorithm="HS256")
    return token, token_id, expires_at


def create_access_token(
    user_id: UUID,
    settings: Settings,
    session_id: UUID | None = None,
) -> tuple[str, str, datetime]:
    return create_token(
        user_id,
        session_id or uuid4(),
        settings,
        "access",
        timedelta(minutes=settings.auth_access_token_minutes),
    )


def create_refresh_token(
    user_id: UUID,
    session_id: UUID,
    settings: Settings,
    lifetime: timedelta | None = None,
) -> tuple[str, str, datetime]:
    return create_token(
        user_id,
        session_id,
        settings,
        "refresh",
        lifetime or timedelta(days=settings.auth_refresh_token_days),
    )


def verify_token(token: str, settings: Settings, expected_type: str) -> dict:
    try:
        claims = jwt.decode(
            token,
            _signing_secret(settings),
            algorithms=["HS256"],
            issuer=settings.auth_issuer,
            audience=settings.auth_audience,
            options={"require": ["sub", "jti", "iss", "aud", "iat", "exp", "token_type"]},
        )
    except AuthConfigurationError:
        raise
    except jwt.PyJWTError as error:
        raise ValueError("Invalid or expired authentication token.") from error
    if claims.get("token_type") != expected_type:
        raise ValueError("Invalid authentication token type.")
    try:
        UUID(claims["sub"])
        UUID(claims["jti"])
        if "sid" in claims:
            UUID(claims["sid"])
    except (ValueError, TypeError) as error:
        raise ValueError("Invalid authentication token claims.") from error
    return claims


def random_token() -> str:
    return secrets.token_urlsafe(32)


def constant_time_hash_matches(token: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_token(token), stored_hash)
