"""Provision fictional Free and Essential accounts only in isolated local testing."""

from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import hash_password, verify_password
from app.config import Settings
from app.models import Case, CaseMembership, DocumentCreditLedgerEntry, User

TEST_EMAIL = "local-test@example.com"
ESSENTIAL_TEST_EMAIL = "essential-test@localhost.invalid"


def validate_local_environment(settings: Settings) -> None:
    if (
        urlparse(settings.database_url).hostname != "local-test-db"
        or settings.s3_endpoint_url != "http://127.0.0.1:5000"
        or settings.s3_bucket != "local-test-documents"
        or settings.deletion_ledger_bucket != "local-test-deletion-ledger"
        or settings.auth_public_base_url != "https://192.168.1.17:8444"
        or settings.demo_mode_enabled
        or not settings.auth_enabled
        or not settings.case_data_enabled
        or not settings.case_materials_enabled
        or settings.production_readiness_required
        or settings.owner_beta_enabled
        or settings.ai_analysis_enabled
        or settings.stripe_secret_key
        or settings.smtp_host not in (None, "local-test-mail")
    ):
        raise ValueError("Account provisioning is restricted to the isolated local-test environment.")


def ensure_test_account(db: Session, password: str) -> None:
    user = db.scalar(select(User).where(User.email == TEST_EMAIL).with_for_update())
    if user is not None:
        if user.status != "active" or not user.password_hash or not verify_password(user.password_hash, password):
            raise ValueError("The existing local test account differs; it was not modified.")
        return
    db.add(
        User(
            email=TEST_EMAIL,
            password_hash=hash_password(password),
            status="active",
            email_verified_at=datetime.now(UTC),
        )
    )
    db.flush()


def ensure_essential_test_account(db: Session, password: str) -> None:
    user = db.scalar(select(User).where(User.email == ESSENTIAL_TEST_EMAIL).with_for_update())
    if user is None:
        user = User(
            id=uuid4(), email=ESSENTIAL_TEST_EMAIL, password_hash=hash_password(password),
            status="active", email_verified_at=datetime.now(UTC),
        )
        db.add(user)
        db.flush()
    elif user.status != "active" or not user.password_hash or not verify_password(user.password_hash, password):
        raise ValueError("The existing Essential test account differs; it was not modified.")
    case = db.scalar(
        select(Case).join(CaseMembership, CaseMembership.case_id == Case.id)
        .where(CaseMembership.user_id == user.id, CaseMembership.role == "owner")
        .with_for_update()
    )
    if case is None:
        case = Case(
            id=uuid4(), status="draft", metadata_json={"case_title": "Essential test case"},
            attempt_credit_balance=0,
        )
        db.add(case)
        db.flush()
        db.add(CaseMembership(case_id=case.id, user_id=user.id, role="owner"))
    key = "local-test:essential-initial-grant"
    if db.scalar(select(DocumentCreditLedgerEntry.id).where(
        DocumentCreditLedgerEntry.user_id == user.id,
        DocumentCreditLedgerEntry.idempotency_key == key,
    )) is None:
        case.attempt_credit_balance += 5
        db.add(DocumentCreditLedgerEntry(
            user_id=user.id, case_id=case.id, idempotency_key=key,
            source_type="package_purchase", source_reference="isolated-local-test-grant",
            delta=5, balance_after=case.attempt_credit_balance,
        ))
    db.flush()


if __name__ == "__main__":
    settings = Settings()
    validate_local_environment(settings)
    from app.database import SessionLocal

    password = Path("/run/secrets/local-test-password").read_text().strip()
    with SessionLocal() as db:
        ensure_test_account(db, password)
        ensure_essential_test_account(db, password)
        db.commit()
    print(f"Local test accounts ready: {TEST_EMAIL} (Free), {ESSENTIAL_TEST_EMAIL} (Essential). Existing case data was preserved.")
