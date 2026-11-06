import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Literal
from urllib.parse import urlparse
from uuid import UUID, uuid4

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.attempt_credits import (
    PACKAGE_CATALOG,
    PACKAGE_SIZES,
    grant_package_credits,
    package_size_for_price,
)
from app.auth_routes import require_current_user
from app.config import get_settings
from app.database import get_db
from app.models import (
    AttemptCreditPackagePurchase,
    BillingWebhookEvent,
    Case,
    CaseMembership,
    DocumentCreditLedgerEntry,
    User,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/billing", tags=["billing"])
MAX_WEBHOOK_BYTES = 1_000_000
ZERO_DECIMAL_CURRENCIES = {
    "BIF", "CLP", "DJF", "GNF", "JPY", "KMF", "KRW", "MGA",
    "PYG", "RWF", "UGX", "VND", "VUV", "XAF", "XOF", "XPF",
}
THREE_DECIMAL_CURRENCIES = {"BHD", "JOD", "KWD", "OMR", "TND"}


class CheckoutCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    package_size: Literal[5, 10]


class AttemptCreditPackageRead(BaseModel):
    credits: int
    price: str | None
    available: bool


class AttemptCreditPackagesRead(BaseModel):
    packages: list[AttemptCreditPackageRead]
    checkout_configured: bool


class AccountEntitlementRead(BaseModel):
    status: Literal["free", "paid"]


class PackagePurchaseRead(BaseModel):
    id: UUID
    credits: int
    amount: str
    status: str
    purchased_at: datetime | None
    credits_used: int
    refund_deadline: datetime | None
    refund_eligible: bool


class PackagePurchaseHistoryRead(BaseModel):
    purchases: list[PackagePurchaseRead]
    receipt_email: str


def _stripe_settings_ready() -> bool:
    settings = get_settings()
    return bool(
        not settings.demo_mode_enabled
        and settings.stripe_secret_key
        and settings.stripe_webhook_secret
    )


def _stripe_url(value: Any) -> str:
    url = value if isinstance(value, str) else None
    parsed = urlparse(url or "")
    if parsed.scheme != "https" or parsed.hostname != "checkout.stripe.com":
        raise HTTPException(status_code=502, detail="The billing provider returned an invalid URL.")
    return url


def _package_price_id(settings: Any, package_size: int) -> str | None:
    name = f"stripe_price_id_attempt_credits_{package_size}"
    value = getattr(settings, name, None)
    return value.strip() if isinstance(value, str) and value.strip() else None


def _format_one_time_price(price: Any) -> str | None:
    if not isinstance(price, dict) and not hasattr(price, "get"):
        return None
    amount = price.get("unit_amount")
    currency = price.get("currency")
    if (
        not isinstance(amount, int)
        or isinstance(amount, bool)
        or amount <= 0
        or not isinstance(currency, str)
        or price.get("recurring") is not None
        or price.get("active") is not True
    ):
        return None
    currency_code = currency.upper()
    if currency_code in ZERO_DECIMAL_CURRENCIES:
        decimals, divisor = 0, 1
    elif currency_code in THREE_DECIMAL_CURRENCIES:
        decimals, divisor = 3, 1000
    else:
        decimals, divisor = 2, 100
    whole, fraction = divmod(amount, divisor)
    formatted = f"${whole:,}" if currency_code == "USD" else f"{currency_code} {whole:,}"
    if decimals:
        formatted += f".{fraction:0{decimals}d}"
    return formatted


def _catalog_price_is_valid(price: Any, package_size: int) -> bool:
    catalog = PACKAGE_CATALOG.get(package_size)
    if catalog is None:
        return False
    return (
        _format_one_time_price(price) is not None
        and price.get("unit_amount") == catalog["price_amount"]
        and str(price.get("currency", "")).lower() == catalog["currency"]
        and price.get("tax_behavior") in {"exclusive", "inclusive"}
    )


def _load_configured_price(price_id: str, package_size: int, settings: Any) -> Any | None:
    if package_size_for_price(settings, price_id) != package_size:
        return None
    try:
        price = stripe.Price.retrieve(price_id, api_key=settings.stripe_secret_key)
    except stripe.StripeError as error:
        logger.error("Configured Stripe package price could not be loaded (%s).", type(error).__name__)
        return None
    return price if _catalog_price_is_valid(price, package_size) else None


@router.get("/packages", response_model=AttemptCreditPackagesRead)
def list_attempt_credit_packages() -> AttemptCreditPackagesRead:
    settings = get_settings()
    checkout_ready = _stripe_settings_ready()
    packages = []
    for package_size in PACKAGE_SIZES:
        price_id = _package_price_id(settings, package_size)
        price_text = None
        available = False
        if checkout_ready and price_id:
            price = _load_configured_price(price_id, package_size, settings)
            if price is not None:
                price_text = f"USD {_format_one_time_price(price)} before applicable tax"
                available = price_text is not None
        packages.append(
            AttemptCreditPackageRead(
                credits=package_size,
                price=price_text,
                available=available,
            )
        )
    return AttemptCreditPackagesRead(
        packages=packages,
        checkout_configured=checkout_ready,
    )


def _authorized_case(db: Session, user: User, case_id: UUID) -> Case:
    membership = db.scalar(
        select(CaseMembership).where(
            CaseMembership.case_id == case_id,
            CaseMembership.user_id == user.id,
            CaseMembership.revoked_at.is_(None),
            CaseMembership.suspended_at.is_(None),
        )
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    return case


def _has_verified_package_purchase(db: Session, user_id: UUID) -> bool:
    purchase_id = db.scalar(
        select(DocumentCreditLedgerEntry.id)
        .where(
            DocumentCreditLedgerEntry.user_id == user_id,
            DocumentCreditLedgerEntry.source_type == "package_purchase",
            DocumentCreditLedgerEntry.delta > 0,
        )
        .limit(1)
    )
    return purchase_id is not None


@router.get("/account/entitlement", response_model=AccountEntitlementRead)
def read_account_entitlement(
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AccountEntitlementRead:
    return AccountEntitlementRead(
        status="paid" if _has_verified_package_purchase(db, user.id) else "free"
    )


@router.post("/account/downgrade-to-free")
def reject_paid_account_downgrade(
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    locked_user_id = db.scalar(select(User.id).where(User.id == user.id).with_for_update())
    if locked_user_id is None:
        raise HTTPException(status_code=404, detail="Account not found.")
    if _has_verified_package_purchase(db, user.id):
        raise HTTPException(
            status_code=409,
            detail=(
                "An account with a verified one-time attempt-credit purchase cannot switch to "
                "Free. No entitlement, credits, or case access were changed."
            ),
        )
    return {"status": "free"}


@router.post("/cases/{case_id}/checkout")
def create_checkout_session(
    case_id: UUID,
    payload: CheckoutCreate,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    settings = get_settings()
    case = _authorized_case(db, user, case_id)
    case = db.scalar(select(Case).where(Case.id == case.id).with_for_update())
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    if case.attempt_credit_balance > 0:
        raise HTTPException(
            status_code=409,
            detail="Use the attempt credits already in this case before buying another package.",
        )
    pending = db.scalar(
        select(AttemptCreditPackagePurchase.id)
        .where(
            AttemptCreditPackagePurchase.case_id == case.id,
            AttemptCreditPackagePurchase.status == "pending",
        )
        .limit(1)
    )
    if pending is not None:
        raise HTTPException(
            status_code=409,
            detail="A package checkout is already pending for this case.",
        )
    price_id = _package_price_id(settings, payload.package_size)
    if not _stripe_settings_ready() or not price_id:
        raise HTTPException(
            status_code=503,
            detail="Attempt-credit packages are not configured. No credits have been added.",
        )
    price = _load_configured_price(price_id, payload.package_size, settings)
    if price is None:
        raise HTTPException(status_code=503, detail="The selected credit package is unavailable.")

    purchase = AttemptCreditPackagePurchase(
        id=uuid4(),
        user_id=user.id,
        case_id=case.id,
        package_size=payload.package_size,
        price_amount=PACKAGE_CATALOG[payload.package_size]["price_amount"],
        currency=PACKAGE_CATALOG[payload.package_size]["currency"],
        stripe_price_id=price_id,
        status="pending",
    )
    db.add(purchase)
    db.commit()

    customer_id = user.stripe_customer_id
    try:
        if customer_id is None:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={"user_id": str(user.id)},
                api_key=settings.stripe_secret_key,
            )
            customer_id = customer.get("id")
            if not isinstance(customer_id, str):
                raise HTTPException(status_code=502, detail="Billing customer could not be created.")
            user.stripe_customer_id = customer_id
            db.commit()
        base_url = settings.auth_public_base_url.rstrip("/")
        checkout_metadata = {
            "user_id": str(user.id),
            "case_id": str(case.id),
            "package_size": str(payload.package_size),
            "purchase_id": str(purchase.id),
        }
        session = stripe.checkout.Session.create(
            mode="payment",
            customer=customer_id,
            client_reference_id=str(user.id),
            line_items=[{"price": price_id, "quantity": 1}],
            metadata=checkout_metadata,
            payment_intent_data={
                "receipt_email": user.email,
                "metadata": {"purchase_id": str(purchase.id)},
            },
            automatic_tax={"enabled": True},
            billing_address_collection="required",
            customer_update={"address": "auto", "name": "auto"},
            custom_text={
                "submit": {
                    "message": (
                        f"One-time purchase: {payload.package_size} credits for USD "
                        f"${PACKAGE_CATALOG[payload.package_size]['price_amount'] / 100:.2f}, "
                        "plus applicable tax calculated, displayed, and collected by Stripe Tax. "
                        "A full refund is available within 30 days only if no credit from this "
                        "package has been used. No package refund is available after any package "
                        "credit is used. Stripe emails the receipt; no monthly subscription."
                    )
                }
            },
            success_url=f"{base_url}/?attempt_credits=pending",
            cancel_url=f"{base_url}/?attempt_credits=cancelled",
            idempotency_key=f"attempt-credit-checkout:{purchase.id}",
            api_key=settings.stripe_secret_key,
        )
        session_id = session.get("id")
        if not isinstance(session_id, str):
            raise HTTPException(status_code=502, detail="The billing provider returned an invalid session.")
        purchase.stripe_checkout_session_id = session_id
        checkout_url = _stripe_url(session.get("url"))
        db.commit()
    except stripe.StripeError as error:
        db.rollback()
        failed_purchase = db.get(AttemptCreditPackagePurchase, purchase.id)
        if failed_purchase is not None:
            failed_purchase.status = "payment_failed"
            db.commit()
        logger.error("Stripe package Checkout failed (%s).", type(error).__name__)
        raise HTTPException(
            status_code=502, detail="The billing provider is unavailable."
        ) from error
    except HTTPException:
        db.rollback()
        failed_purchase = db.get(AttemptCreditPackagePurchase, purchase.id)
        if failed_purchase is not None:
            failed_purchase.status = "payment_failed"
            db.commit()
        raise
    return {
        "checkout_url": checkout_url,
        "payment_status": "pending_webhook_confirmation",
    }


def _dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict_recursive"):
        return value.to_dict_recursive()
    return {}


def _paid_package_size(session: dict[str, Any], settings: Any) -> int | None:
    session_id = session.get("id")
    if not isinstance(session_id, str):
        return None
    try:
        line_items = stripe.checkout.Session.list_line_items(
            session_id,
            limit=2,
            api_key=settings.stripe_secret_key,
        )
    except stripe.StripeError as error:
        logger.error("Paid Checkout line items could not be verified (%s).", type(error).__name__)
        raise
    rows = _dict(line_items).get("data", [])
    if not isinstance(rows, list) or len(rows) != 1:
        return None
    line = _dict(rows[0])
    quantity = line.get("quantity")
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity != 1:
        return None
    price_id = _dict(line.get("price")).get("id")
    package_size = package_size_for_price(settings, price_id)
    if package_size is None:
        return None
    configured_price = _load_configured_price(price_id, package_size, settings)
    if configured_price is None or _dict(session.get("automatic_tax")).get("enabled") is not True:
        return None
    metadata_size = _dict(session.get("metadata")).get("package_size")
    if metadata_size != str(package_size):
        return None
    return package_size


def _apply_checkout_completed(
    db: Session,
    session: dict[str, Any],
    *,
    paid_at: datetime | None = None,
) -> bool:
    if (
        session.get("mode") != "payment"
        or session.get("status") != "complete"
        or session.get("payment_status") != "paid"
    ):
        return True
    user_id = session.get("client_reference_id")
    metadata = _dict(session.get("metadata"))
    if not isinstance(user_id, str) or user_id != metadata.get("user_id"):
        return False
    session_id = session.get("id")
    customer_id = session.get("customer")
    case_id = metadata.get("case_id")
    purchase_id = metadata.get("purchase_id")
    if not all(
        isinstance(value, str) and value
        for value in (session_id, customer_id, case_id, purchase_id)
    ):
        return False
    try:
        parsed_user_id = UUID(user_id)
        parsed_case_id = UUID(case_id)
        parsed_purchase_id = UUID(purchase_id)
    except ValueError:
        return False

    user = db.scalar(select(User).where(User.id == parsed_user_id).with_for_update())
    case = db.scalar(select(Case).where(Case.id == parsed_case_id).with_for_update())
    purchase = db.scalar(
        select(AttemptCreditPackagePurchase)
        .where(AttemptCreditPackagePurchase.id == parsed_purchase_id)
        .with_for_update()
    )
    if user is None or case is None or purchase is None:
        return False
    if (
        purchase.user_id != user.id
        or purchase.case_id != case.id
        or purchase.stripe_checkout_session_id != session_id
        or metadata.get("package_size") != str(purchase.package_size)
        or user.stripe_customer_id not in {None, customer_id}
    ):
        return False

    package_size = _paid_package_size(session, get_settings())
    if package_size is None:
        return False
    if package_size != purchase.package_size:
        return False
    if purchase.status == "paid":
        return True
    if purchase.status != "pending":
        return False
    amount_subtotal = session.get("amount_subtotal")
    amount_total = session.get("amount_total")
    if (
        session.get("currency") != "usd"
        or amount_subtotal != purchase.price_amount
        or not isinstance(amount_total, int)
        or isinstance(amount_total, bool)
        or amount_total < amount_subtotal
    ):
        return False
    user.stripe_customer_id = customer_id
    payment_intent = session.get("payment_intent")
    payment_intent_id = payment_intent if isinstance(payment_intent, str) else _dict(payment_intent).get("id")
    if not isinstance(payment_intent_id, str) or not payment_intent_id:
        return False
    purchase.status = "paid"
    purchase.amount_paid = amount_total
    purchase.stripe_payment_intent_id = payment_intent_id
    purchase.paid_at = paid_at or datetime.now(UTC)
    grant_package_credits(
        db,
        case,
        user,
        package_size=package_size,
        checkout_session_id=session_id,
        purchase=purchase,
    )
    return True


def _finish_package_refund(
    db: Session,
    case: Case,
    purchase: AttemptCreditPackagePurchase,
    refund_id: str,
) -> None:
    if purchase.status == "refunded":
        return
    if (
        purchase.status != "refund_pending"
        or purchase.credits_used != 0
        or case.attempt_credit_balance != purchase.package_size
    ):
        raise HTTPException(status_code=409, detail="This package is no longer eligible for refund.")
    case.attempt_credit_balance -= purchase.package_size
    purchase.status = "refunded"
    purchase.stripe_refund_id = refund_id
    purchase.refunded_at = datetime.now(UTC)
    db.add(
        DocumentCreditLedgerEntry(
            id=uuid4(),
            user_id=purchase.user_id,
            case_id=case.id,
            package_purchase_id=purchase.id,
            proposal_version_id=None,
            idempotency_key=f"stripe-refund:{refund_id}",
            source_type="package_refund",
            source_reference=refund_id,
            delta=-purchase.package_size,
            balance_after=case.attempt_credit_balance,
        )
    )


def _apply_checkout_terminal_event(db: Session, session: dict[str, Any], status: str) -> bool:
    session_id = session.get("id")
    if not isinstance(session_id, str):
        return False
    purchase = db.scalar(
        select(AttemptCreditPackagePurchase)
        .where(AttemptCreditPackagePurchase.stripe_checkout_session_id == session_id)
        .with_for_update()
    )
    if purchase is None:
        return True
    if purchase.status == "pending":
        purchase.status = status
    return True


def _apply_refund_event(db: Session, refund: dict[str, Any]) -> bool:
    purchase_id = _dict(refund.get("metadata")).get("purchase_id")
    refund_id = refund.get("id")
    payment_intent = refund.get("payment_intent")
    payment_intent_id = payment_intent if isinstance(payment_intent, str) else _dict(payment_intent).get("id")
    if not all(isinstance(value, str) and value for value in (purchase_id, refund_id, payment_intent_id)):
        return False
    try:
        parsed_purchase_id = UUID(purchase_id)
    except ValueError:
        return False
    purchase = db.scalar(
        select(AttemptCreditPackagePurchase)
        .where(AttemptCreditPackagePurchase.id == parsed_purchase_id)
        .with_for_update()
    )
    if purchase is None or purchase.stripe_payment_intent_id != payment_intent_id:
        return False
    if refund.get("amount") != purchase.amount_paid:
        return False
    if purchase.status == "refunded":
        return purchase.stripe_refund_id == refund_id
    if purchase.status != "refund_pending":
        return False
    if refund.get("status") == "succeeded":
        case = db.scalar(select(Case).where(Case.id == purchase.case_id).with_for_update())
        if case is None:
            return False
        _finish_package_refund(db, case, purchase, refund_id)
    elif refund.get("status") == "failed":
        purchase.status = "paid"
        purchase.stripe_refund_id = None
    else:
        purchase.stripe_refund_id = refund_id
    return True


@router.get(
    "/cases/{case_id}/purchases",
    response_model=PackagePurchaseHistoryRead,
)
def list_package_purchases(
    case_id: UUID,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PackagePurchaseHistoryRead:
    case = _authorized_case(db, user, case_id)
    purchases = db.scalars(
        select(AttemptCreditPackagePurchase)
        .where(
            AttemptCreditPackagePurchase.case_id == case.id,
            AttemptCreditPackagePurchase.user_id == user.id,
        )
        .order_by(AttemptCreditPackagePurchase.created_at.desc())
    ).all()
    now = datetime.now(UTC)
    results = []
    for purchase in purchases:
        deadline = purchase.paid_at + timedelta(days=30) if purchase.paid_at else None
        results.append(
            PackagePurchaseRead(
                id=purchase.id,
                credits=purchase.package_size,
                amount=(
                    f"USD ${(purchase.amount_paid or purchase.price_amount) / 100:.2f}"
                    if purchase.price_amount is not None
                    else "Historical amount not recorded"
                ),
                status=purchase.status,
                purchased_at=purchase.paid_at,
                credits_used=purchase.credits_used,
                refund_deadline=deadline,
                refund_eligible=bool(
                    purchase.status == "paid"
                    and purchase.credits_used == 0
                    and deadline is not None
                    and now <= deadline
                    and case.attempt_credit_balance == purchase.package_size
                ),
            )
        )
    return PackagePurchaseHistoryRead(purchases=results, receipt_email=user.email)


@router.post("/cases/{case_id}/purchases/{purchase_id}/refund")
def refund_package_purchase(
    case_id: UUID,
    purchase_id: UUID,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    settings = get_settings()
    if not _stripe_settings_ready():
        raise HTTPException(status_code=503, detail="Refund processing is not configured.")
    case = _authorized_case(db, user, case_id)
    case = db.scalar(select(Case).where(Case.id == case.id).with_for_update())
    purchase = db.scalar(
        select(AttemptCreditPackagePurchase)
        .where(
            AttemptCreditPackagePurchase.id == purchase_id,
            AttemptCreditPackagePurchase.case_id == case_id,
            AttemptCreditPackagePurchase.user_id == user.id,
        )
        .with_for_update()
    )
    if case is None or purchase is None:
        raise HTTPException(status_code=404, detail="Purchase not found.")
    if purchase.status == "refunded":
        return {"status": "refunded"}
    if purchase.status == "paid":
        deadline = purchase.paid_at + timedelta(days=30) if purchase.paid_at else None
        if (
            purchase.credits_used != 0
            or deadline is None
            or datetime.now(UTC) > deadline
            or case.attempt_credit_balance != purchase.package_size
        ):
            raise HTTPException(
                status_code=409,
                detail="A package refund is available within 30 days only when no package credits have been used.",
            )
        if not purchase.stripe_payment_intent_id:
            raise HTTPException(status_code=409, detail="The verified payment reference is unavailable.")
        purchase.status = "refund_pending"
        db.commit()
    elif purchase.status != "refund_pending":
        raise HTTPException(status_code=409, detail="This purchase is not refundable.")

    try:
        refund = stripe.Refund.create(
            payment_intent=purchase.stripe_payment_intent_id,
            metadata={"purchase_id": str(purchase.id)},
            idempotency_key=f"attempt-credit-refund:{purchase.id}",
            api_key=settings.stripe_secret_key,
        )
    except stripe.StripeError as error:
        logger.error("Stripe package refund could not be completed (%s).", type(error).__name__)
        raise HTTPException(
            status_code=502,
            detail="The refund provider could not confirm the refund. Credits remain locked while it is reconciled.",
        ) from error

    refund_id = refund.get("id")
    refund_status = refund.get("status")
    if not isinstance(refund_id, str):
        raise HTTPException(status_code=502, detail="The refund provider returned an invalid reference.")
    if refund_status == "succeeded":
        if refund.get("amount") != purchase.amount_paid:
            raise HTTPException(
                status_code=502,
                detail="The refund provider did not confirm a full package refund.",
            )
        _finish_package_refund(db, case, purchase, refund_id)
        db.commit()
        return {"status": "refunded"}
    if refund_status == "failed":
        purchase.status = "paid"
        purchase.stripe_refund_id = None
        db.commit()
        raise HTTPException(status_code=502, detail="The payment provider declined the refund.")
    purchase.stripe_refund_id = refund_id
    db.commit()
    return {"status": "refund_pending"}


def _process_event(db: Session, event: dict[str, Any]) -> str:
    event_type = event.get("type")
    created = event.get("created")
    paid_at = (
        datetime.fromtimestamp(created, UTC)
        if isinstance(created, int) and not isinstance(created, bool) and created > 0
        else None
    )
    if event_type in {
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
    }:
        processed = _apply_checkout_completed(
            db, _dict(_dict(event.get("data")).get("object")), paid_at=paid_at
        )
    elif event_type == "checkout.session.expired":
        processed = _apply_checkout_terminal_event(
            db, _dict(_dict(event.get("data")).get("object")), "expired"
        )
    elif event_type == "checkout.session.async_payment_failed":
        processed = _apply_checkout_terminal_event(
            db, _dict(_dict(event.get("data")).get("object")), "payment_failed"
        )
    elif event_type == "refund.updated":
        processed = _apply_refund_event(db, _dict(_dict(event.get("data")).get("object")))
    else:
        return "ignored"
    if not processed:
        raise HTTPException(status_code=503, detail="Billing event could not be matched to an account.")
    return "processed"


@router.post("/webhook")
async def receive_stripe_webhook(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, bool]:
    settings = get_settings()
    if settings.demo_mode_enabled or not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Billing webhooks are not configured.")
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Billing signature is required.")
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_WEBHOOK_BYTES:
            raise HTTPException(status_code=413, detail="Billing webhook is too large.")
        body.extend(chunk)
    try:
        event = stripe.Webhook.construct_event(
            bytes(body),
            signature,
            settings.stripe_webhook_secret,
            tolerance=300,
        )
    except (ValueError, stripe.SignatureVerificationError) as error:
        raise HTTPException(status_code=400, detail="Billing webhook signature is invalid.") from error
    event_data = _dict(event)
    event_id = event_data.get("id")
    event_type = event_data.get("type")
    if not isinstance(event_id, str) or not isinstance(event_type, str):
        raise HTTPException(status_code=400, detail="Billing webhook event is malformed.")
    claimed_id = db.scalar(
        insert(BillingWebhookEvent)
        .values(event_id=event_id, event_type=event_type, status="processing")
        .on_conflict_do_nothing(index_elements=[BillingWebhookEvent.event_id])
        .returning(BillingWebhookEvent.event_id)
    )
    if claimed_id is None:
        db.rollback()
        return {"received": True}
    try:
        status = _process_event(db, event_data)
        webhook_record = db.get(BillingWebhookEvent, event_id)
        if webhook_record is None:
            raise HTTPException(status_code=503, detail="Billing event receipt could not be saved.")
        webhook_record.status = status
        from datetime import UTC, datetime

        webhook_record.processed_at = datetime.now(UTC)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except (SQLAlchemyError, stripe.StripeError) as error:
        db.rollback()
        logger.exception("Verified Stripe event could not be committed.")
        raise HTTPException(status_code=503, detail="Billing event could not be processed.") from error
    return {"received": True}
