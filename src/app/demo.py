from datetime import UTC, datetime
from uuid import UUID

from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo"
DEMO_USER_ID = UUID("00000000-0000-4000-8000-000000000001")
DEMO_EMAIL = "demo@localhost.invalid"
_PASSWORD_HASHER = PasswordHash.recommended()


def ensure_demo_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.id == DEMO_USER_ID).with_for_update())
    if user is None:
        user = User(
            id=DEMO_USER_ID,
            email=DEMO_EMAIL,
            password_hash=_PASSWORD_HASHER.hash(DEMO_PASSWORD),
            status="active",
            email_verified_at=datetime.now(UTC),
        )
        db.add(user)
        db.flush()
    return user


def verify_demo_password(password: str, password_hash: str | None) -> bool:
    return password_hash is not None and _PASSWORD_HASHER.verify(password, password_hash)
