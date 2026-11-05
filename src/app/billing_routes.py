import logging
from typing import Annotated, Any, Literal
from urllib.parse import urlparse
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.attempt_credits import PACKAGE_SIZES, grant_package_credits, package_size_for_price
from app.auth_routes import require_current_user
from app.config import get_settings
from app.database import get_db
from app.models import BillingWebhookEvent, Case, CaseMembership, User

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


def _load_configured_price(price_id: str, package_size: int, settings: Any) -> Any | None:
    if package_size_for_price(settings, price_id) != package_size:
        return None
    try:
        price = stripe.Price.retrieve(price_id, api_key=settings.stripe_secret_key)
    except stripe.StripeError as error:
        logger.error("Configured Stripe package price could not be loaded (%s).", type(error).__name__)
        return None
    return price if _format_one_time_price(price) is not None else None


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
                price_text = _format_one_time_price(price)
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


@router.post("/cases/{case_id}/checkout")
def create_checkout_session(
    case_id: UUID,
    payload: CheckoutCreate,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    settings = get_settings()
    case = _authorized_case(db, user, case_id)
    price_id = _package_price_id(settings, payload.package_size)
    if not _stripe_settings_ready() or not price_id:
        raise HTTPException(
            status_code=503,
            detail="Attempt-credit packages are not configured. No credits have been added.",
        )
    price = _load_configured_price(price_id, payload.package_size, settings)
    if price is None:
        raise HTTPException(status_code=503, detail="The selected credit package is unavailable.")

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
        session = stripe.checkout.Session.create(
            mode="payment",
            customer=customer_id,
            client_reference_id=str(user.id),
            line_items=[{"price": price_id, "quantity": 1}],
            metadata={
                "user_id": str(user.id),
                "case_id": str(case.id),
                "package_size": str(payload.package_size),
            },
            success_url=f"{base_url}/?attempt_credits=pending",
            cancel_url=f"{base_url}/?attempt_credits=cancelled",
            api_key=settings.stripe_secret_key,
        )
    except stripe.StripeError as error:
        db.rollback()
        logger.error("Stripe package Checkout failed (%s).", type(error).__name__)
        raise HTTPException(
            status_code=502, detail="The billing provider is unavailable."
        ) from error
    return {
        "checkout_url": _stripe_url(session.get("url")),
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
    if line.get("quantity") != 1:
        return None
    price_id = _dict(line.get("price")).get("id")
    package_size = package_size_for_price(settings, price_id)
    if package_size is None:
        return None
    metadata_size = _dict(session.get("metadata")).get("package_size")
    if metadata_size != str(package_size):
        return None
    return package_size


def _apply_checkout_completed(db: Session, session: dict[str, Any]) -> bool:
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
    if not all(isinstance(value, str) and value for value in (session_id, customer_id, case_id)):
        return False
    try:
        parsed_user_id = UUID(user_id)
        parsed_case_id = UUID(case_id)
    except ValueError:
        return False

    user = db.scalar(select(User).where(User.id == parsed_user_id).with_for_update())
    case = db.scalar(select(Case).where(Case.id == parsed_case_id).with_for_update())
    if user is None or case is None:
        return False
    if user.stripe_customer_id not in {None, customer_id}:
        return False
    owner_exists = db.scalar(
        select(CaseMembership.id).where(
            CaseMembership.case_id == case.id,
            CaseMembership.role == "owner",
            CaseMembership.revoked_at.is_(None),
        )
    )
    if owner_exists is None:
        return False

    package_size = _paid_package_size(session, get_settings())
    if package_size is None:
        return True
    user.stripe_customer_id = customer_id
    grant_package_credits(
        db,
        case,
        user,
        package_size=package_size,
        checkout_session_id=session_id,
    )
    return True


def _process_event(db: Session, event: dict[str, Any]) -> str:
    event_type = event.get("type")
    if event_type in {
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
    }:
        processed = _apply_checkout_completed(
            db, _dict(_dict(event.get("data")).get("object"))
        )
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
