from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AttemptCreditPackagePurchase,
    Case,
    DocumentCreditLedgerEntry,
    SettlementNegotiationAttempt,
    User,
)

PACKAGE_SIZES = (5, 10)
PACKAGE_CATALOG = {
    5: {"price_amount": 500, "currency": "usd"},
    10: {"price_amount": 800, "currency": "usd"},
}


def package_size_for_price(settings: object, price_id: str | None) -> int | None:
    if not isinstance(price_id, str) or not price_id:
        return None
    configured = (
        (getattr(settings, "stripe_price_id_attempt_credits_5", None), 5),
        (getattr(settings, "stripe_price_id_attempt_credits_10", None), 10),
    )
    matches = [size for configured_id, size in configured if configured_id == price_id]
    return matches[0] if len(matches) == 1 else None


def consume_finalization_credit(
    db: Session,
    case: Case,
    actor: User,
    attempt: SettlementNegotiationAttempt,
) -> dict[str, int | str | None]:
    if not case.first_finalization_used:
        case.first_finalization_used = True
        return {
            "policy": "free_first_case_finalization",
            "credit_cost": 0,
            "ledger_entry_id": None,
            "balance_after": case.attempt_credit_balance,
        }
    if case.attempt_credit_balance < 1:
        raise HTTPException(
            status_code=402,
            detail=(
                "This finalized proposal needs 1 attempt credit. Your edits are saved; "
                "purchase a 5- or 10-credit package to continue."
            ),
        )

    purchase = db.scalar(
        select(AttemptCreditPackagePurchase)
        .where(
            AttemptCreditPackagePurchase.case_id == case.id,
            AttemptCreditPackagePurchase.status.in_(("paid", "refund_pending")),
            AttemptCreditPackagePurchase.credits_used < AttemptCreditPackagePurchase.package_size,
        )
        .order_by(AttemptCreditPackagePurchase.created_at)
        .with_for_update()
        .limit(1)
    )
    if isinstance(purchase, AttemptCreditPackagePurchase) and purchase.status == "refund_pending":
        raise HTTPException(
            status_code=409,
            detail="A package refund is being processed; finalization is temporarily unavailable.",
        )
    case.attempt_credit_balance -= 1
    if isinstance(purchase, AttemptCreditPackagePurchase):
        purchase.credits_used += 1
    entry = DocumentCreditLedgerEntry(
        id=uuid4(),
        user_id=actor.id,
        case_id=case.id,
        proposal_version_id=None,
        idempotency_key=f"finalization:{attempt.id}",
        source_type="attempt_finalization",
        source_reference=str(attempt.id),
        package_purchase_id=purchase.id if isinstance(purchase, AttemptCreditPackagePurchase) else None,
        delta=-1,
        balance_after=case.attempt_credit_balance,
    )
    db.add(entry)
    return {
        "policy": "attempt_credit",
        "credit_cost": 1,
        "ledger_entry_id": str(entry.id),
        "balance_after": case.attempt_credit_balance,
    }


def grant_package_credits(
    db: Session,
    case: Case,
    buyer: User,
    *,
    package_size: int,
    checkout_session_id: str,
    purchase: AttemptCreditPackagePurchase | None = None,
) -> bool:
    if package_size not in PACKAGE_SIZES:
        return False
    idempotency_key = f"stripe-checkout:{checkout_session_id}"
    existing = db.scalar(
        select(DocumentCreditLedgerEntry.id).where(
            DocumentCreditLedgerEntry.case_id == case.id,
            DocumentCreditLedgerEntry.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        return False

    case.attempt_credit_balance += package_size
    db.add(
        DocumentCreditLedgerEntry(
            id=uuid4(),
            user_id=buyer.id,
            case_id=case.id,
            proposal_version_id=None,
            idempotency_key=idempotency_key,
            source_type="package_purchase",
            source_reference=checkout_session_id,
            package_purchase_id=purchase.id if purchase else None,
            delta=package_size,
            balance_after=case.attempt_credit_balance,
        )
    )
    return True
