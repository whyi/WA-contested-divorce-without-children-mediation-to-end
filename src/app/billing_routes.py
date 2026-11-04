import logging
from datetime import UTC, datetime
from typing import Annotated, Any
from urllib.parse import urlparse
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth_routes import require_current_user
from app.config import get_settings
from app.database import get_db
from app.models import BillingWebhookEvent, DocumentCreditLedgerEntry, User
from app.subscription_plans import PLAN_BY_CODE, PLANS, configured_price_id, plan_for_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/billing", tags=["billing"])
MAX_WEBHOOK_BYTES = 1_000_000
PAID_SUBSCRIPTION_STATUSES = {"active", "trialing"}
ZERO_DECIMAL_CURRENCIES = {
    "BIF", "CLP", "DJF", "GNF", "JPY", "KMF", "KRW", "MGA",
    "PYG", "RWF", "UGX", "VND", "VUV", "XAF", "XOF", "XPF",
}
THREE_DECIMAL_CURRENCIES = {"BHD", "JOD", "KWD", "OMR", "TND"}
TWO_DECIMAL_ZERO_VALUE_CURRENCIES = {"ISK", "UGX"}


class CheckoutCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_code: str = Field(pattern=r"^(essential|plus|pro)$")


class BillingPlanRead(BaseModel):
    code: str
    name: str
    description: str
    active_case_limit: int | None
    attempt_limit: int
    monthly_document_credits: int
    monthly_price: str | None
    available: bool


class BillingPlansRead(BaseModel):
    plans: list[BillingPlanRead]
    billing_configured: bool


class BillingStatusRead(BaseModel):
    plan_code: str
    plan_name: str
    subscription_status: str
    active_case_limit: int | None
    attempt_limit: int
    monthly_document_credits: int
    document_credit_balance: int
    period_end: datetime | None
    cancel_at_period_end: bool
    manage_available: bool


def _stripe_settings_ready() -> bool:
    settings = get_settings()
    return bool(
        not settings.demo_mode_enabled
        and settings.stripe_secret_key
        and settings.stripe_webhook_secret
    )


def _stripe_url(value: Any, expected_host: str) -> str:
    url = value if isinstance(value, str) else None
    parsed = urlparse(url or "")
    if parsed.scheme != "https" or parsed.hostname != expected_host:
        raise HTTPException(status_code=502, detail="The billing provider returned an invalid URL.")
    return url


def _stripe_price_plan(price_id: str | None) -> str | None:
    if not price_id:
        return None
    settings = get_settings()
    matches = [
        plan.code for plan in PLANS
        if configured_price_id(settings, plan) == price_id
    ]
    return matches[0] if len(matches) == 1 else None


def _stripe_api_error(error: stripe.StripeError, action: str) -> HTTPException:
    logger.error("Stripe %s failed (%s).", action, type(error).__name__)
    return HTTPException(status_code=502, detail=f"Billing provider {action} is unavailable.")


def _format_monthly_price(price: Any) -> str | None:
    if not isinstance(price, dict) and not hasattr(price, "get"):
        return None
    amount = price.get("unit_amount")
    currency = price.get("currency")
    recurring = price.get("recurring")
    active = price.get("active")
    if (
        not isinstance(amount, int)
        or not isinstance(currency, str)
        or not isinstance(recurring, dict)
        or recurring.get("interval") != "month"
        or active is not True
    ):
        return None
    currency_code = currency.upper()
    if currency_code in TWO_DECIMAL_ZERO_VALUE_CURRENCIES:
        decimals = 0
        divisor = 100
    elif currency_code in ZERO_DECIMAL_CURRENCIES:
        decimals = 0
        divisor = 1
    elif currency_code in THREE_DECIMAL_CURRENCIES:
        decimals = 3
        divisor = 1000
    else:
        decimals = 2
        divisor = 100
    whole, fraction = divmod(amount, divisor)
    if decimals == 0 and fraction:
        return None
    if currency_code == "USD":
        formatted = f"${whole:,}"
    else:
        formatted = f"{currency_code} {whole:,}"
    if decimals:
        formatted += f".{fraction:0{decimals}d}"
    return f"{formatted}/month"


@router.get("/plans", response_model=BillingPlansRead)
def list_billing_plans() -> BillingPlansRead:
    settings = get_settings()
    stripe_ready = _stripe_settings_ready()
    rows = []
    for plan in PLANS:
        price_id = configured_price_id(settings, plan)
        if plan.code == "free":
            rows.append(
                BillingPlanRead(
                    code=plan.code,
                    name=plan.name,
                    description=plan.description,
                    active_case_limit=plan.active_case_limit,
                    attempt_limit=plan.attempt_limit,
                    monthly_document_credits=plan.monthly_document_credits,
                    monthly_price="$0/month",
                    available=True,
                )
            )
            continue
        price_text = None
        available = False
        if stripe_ready and price_id:
            try:
                price = stripe.Price.retrieve(price_id, api_key=settings.stripe_secret_key)
            except stripe.StripeError as error:
                logger.error("Configured Stripe price could not be loaded (%s).", type(error).__name__)
            else:
                price_text = _format_monthly_price(price)
                available = bool(
                    stripe_ready
                    and price_text
                    and _stripe_price_plan(price_id) == plan.code
                )
        rows.append(
            BillingPlanRead(
                code=plan.code,
                name=plan.name,
                description=plan.description,
                active_case_limit=plan.active_case_limit,
                attempt_limit=plan.attempt_limit,
                monthly_document_credits=plan.monthly_document_credits,
                monthly_price=price_text,
                available=available,
            )
        )
    return BillingPlansRead(plans=rows, billing_configured=stripe_ready)


@router.get("/me", response_model=BillingStatusRead)
def get_billing_status(
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
) -> BillingStatusRead:
    plan = plan_for_user(user)
    response.headers["Cache-Control"] = "no-store"
    return BillingStatusRead(
        plan_code=plan.code,
        plan_name=plan.name,
        subscription_status=user.subscription_status,
        active_case_limit=plan.active_case_limit,
        attempt_limit=plan.attempt_limit,
        monthly_document_credits=plan.monthly_document_credits,
        document_credit_balance=user.document_credit_balance,
        period_end=user.subscription_period_end,
        cancel_at_period_end=user.subscription_cancel_at_period_end,
        manage_available=bool(user.stripe_customer_id and _stripe_settings_ready()),
    )


@router.post("/checkout")
def create_checkout_session(
    payload: CheckoutCreate,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    settings = get_settings()
    plan = PLAN_BY_CODE[payload.plan_code]
    price_id = configured_price_id(settings, plan)
    if not _stripe_settings_ready() or not price_id:
        raise HTTPException(
            status_code=503,
            detail="Subscriptions are not configured. Your current plan has not changed.",
        )
    price_plan = _stripe_price_plan(price_id)
    if price_plan != plan.code:
        raise HTTPException(status_code=503, detail="The selected subscription plan is unavailable.")
    try:
        price = stripe.Price.retrieve(price_id, api_key=settings.stripe_secret_key)
    except stripe.StripeError as error:
        raise _stripe_api_error(error, "price lookup") from error
    if _format_monthly_price(price) is None:
        raise HTTPException(
            status_code=503,
            detail="The selected monthly subscription price is unavailable.",
        )
    if user.subscription_status == "legacy":
        raise HTTPException(
            status_code=409,
            detail="Contact support to move this legacy account to a subscription.",
        )
    if (
        user.subscription_status in PAID_SUBSCRIPTION_STATUSES | {"past_due", "unpaid", "incomplete"}
        and user.stripe_subscription_id
    ):
        raise HTTPException(
            status_code=409,
            detail="Manage or resolve your existing subscription before starting another checkout.",
        )
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
            mode="subscription",
            customer=customer_id,
            client_reference_id=str(user.id),
            line_items=[{"price": price_id, "quantity": 1}],
            subscription_data={
                "metadata": {"user_id": str(user.id), "plan_code": plan.code}
            },
            metadata={"user_id": str(user.id), "plan_code": plan.code},
            success_url=f"{base_url}/?billing=success",
            cancel_url=f"{base_url}/?billing=cancel",
            api_key=settings.stripe_secret_key,
        )
    except stripe.StripeError as error:
        db.rollback()
        raise _stripe_api_error(error, "checkout") from error
    return {
        "checkout_url": _stripe_url(session.get("url"), "checkout.stripe.com"),
        "payment_status": "pending_webhook_confirmation",
    }


@router.post("/portal")
def create_customer_portal_session(
    user: Annotated[User, Depends(require_current_user)],
) -> dict[str, str]:
    settings = get_settings()
    if not _stripe_settings_ready() or not user.stripe_customer_id:
        raise HTTPException(status_code=503, detail="Subscription management is not available.")
    try:
        session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=f"{settings.auth_public_base_url.rstrip('/')}/",
            api_key=settings.stripe_secret_key,
        )
    except stripe.StripeError as error:
        raise _stripe_api_error(error, "customer portal") from error
    return {"portal_url": _stripe_url(session.get("url"), "billing.stripe.com")}


def _dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict_recursive"):
        return value.to_dict_recursive()
    return {}


def _period_end(value: Any) -> datetime | None:
    if not isinstance(value, (int, float)):
        return None
    return datetime.fromtimestamp(value, tz=UTC)


def _event_plan_code(subscription: dict[str, Any]) -> str | None:
    items = _dict(subscription.get("items")).get("data", [])
    price_ids = set()
    if isinstance(items, list):
        for item in items:
            price = _dict(item).get("price")
            price_id = price if isinstance(price, str) else _dict(price).get("id")
            if isinstance(price_id, str):
                price_ids.add(price_id)
    if len(price_ids) != 1:
        return None
    return _stripe_price_plan(next(iter(price_ids)))


def _customer_for_event(db: Session, customer_id: Any) -> User | None:
    if not isinstance(customer_id, str):
        return None
    return db.scalar(
        select(User).where(User.stripe_customer_id == customer_id).with_for_update()
    )


def _apply_subscription_event(db: Session, event: dict[str, Any], event_created: datetime) -> bool:
    subscription = _dict(_dict(event.get("data")).get("object"))
    user = _customer_for_event(db, subscription.get("customer"))
    if user is None:
        return False
    last_applied = user.billing_state_event_created_at
    if last_applied is not None and last_applied >= event_created:
        return True
    event_type = event.get("type")
    subscription_id = subscription.get("id")
    if event_type == "customer.subscription.deleted":
        user.subscription_plan = "free"
        user.subscription_status = "canceled"
        user.settlement_attempt_limit = PLAN_BY_CODE["free"].attempt_limit
        user.stripe_subscription_id = None
        user.subscription_period_end = _period_end(subscription.get("current_period_end"))
        user.subscription_cancel_at_period_end = False
    else:
        plan_code = _event_plan_code(subscription)
        status = subscription.get("status")
        if plan_code is None:
            logger.warning("Stripe subscription has no configured single-tier price (%s).", event_type)
            user.subscription_plan = "free"
            user.subscription_status = "unpaid"
            user.settlement_attempt_limit = PLAN_BY_CODE["free"].attempt_limit
        else:
            user.subscription_plan = plan_code
            user.subscription_status = (
                status if status in {
                    "incomplete",
                    "active",
                    "trialing",
                    "past_due",
                    "unpaid",
                    "canceled",
                    "incomplete_expired",
                } else "unpaid"
            )
            user.settlement_attempt_limit = (
                PLAN_BY_CODE[plan_code].attempt_limit
                if user.subscription_status in PAID_SUBSCRIPTION_STATUSES
                else PLAN_BY_CODE["free"].attempt_limit
            )
        if isinstance(subscription_id, str):
            user.stripe_subscription_id = subscription_id
        user.subscription_period_end = _period_end(
            subscription.get("current_period_end")
        )
        user.subscription_cancel_at_period_end = bool(
            subscription.get("cancel_at_period_end", False)
        )
    user.billing_state_event_created_at = event_created
    return True


def _invoice_subscription_id(invoice: dict[str, Any]) -> str | None:
    subscription_id = invoice.get("subscription")
    if isinstance(subscription_id, str):
        return subscription_id
    parent = _dict(invoice.get("parent"))
    details = _dict(parent.get("subscription_details"))
    subscription_id = details.get("subscription")
    return subscription_id if isinstance(subscription_id, str) else None


def _invoice_plan_code(invoice: dict[str, Any]) -> str | None:
    lines = _dict(invoice.get("lines")).get("data", [])
    price_ids: set[str] = set()
    if isinstance(lines, list):
        for line in lines:
            price = _dict(_dict(line).get("pricing")).get("price_details")
            price_id = _dict(price).get("price")
            if not isinstance(price_id, str):
                legacy_price = _dict(line).get("price")
                price_id = legacy_price if isinstance(legacy_price, str) else _dict(legacy_price).get("id")
            if isinstance(price_id, str):
                price_ids.add(price_id)
    if len(price_ids) != 1:
        return None
    return _stripe_price_plan(next(iter(price_ids)))


def _apply_invoice_paid(db: Session, invoice: dict[str, Any]) -> bool:
    if invoice.get("billing_reason") not in {"subscription_create", "subscription_cycle"}:
        return True
    amount_paid = invoice.get("amount_paid")
    if (
        not isinstance(amount_paid, int)
        or isinstance(amount_paid, bool)
        or amount_paid <= 0
    ):
        return True
    user = _customer_for_event(db, invoice.get("customer"))
    if user is None:
        return False
    subscription_id = _invoice_subscription_id(invoice)
    if not subscription_id:
        return False
    if user.stripe_subscription_id and user.stripe_subscription_id != subscription_id:
        return True
    if not user.stripe_subscription_id and user.subscription_status not in {"free", "incomplete"}:
        return True
    plan_code = _invoice_plan_code(invoice)
    if plan_code is None:
        logger.warning("Paid subscription invoice did not match one configured plan.")
        return True
    plan = PLAN_BY_CODE[plan_code]
    cap = plan.monthly_document_credits * 2
    grant = max(0, min(plan.monthly_document_credits, cap - user.document_credit_balance))
    user.stripe_subscription_id = subscription_id
    user.subscription_plan = plan_code
    user.subscription_status = "active"
    user.settlement_attempt_limit = plan.attempt_limit
    if grant:
        user.document_credit_balance += grant
        invoice_id = invoice.get("id")
        if not isinstance(invoice_id, str):
            return False
        db.add(
            DocumentCreditLedgerEntry(
                user_id=user.id,
                proposal_version_id=None,
                idempotency_key=f"stripe-invoice:{invoice_id}",
                source_type="subscription_cycle",
                source_reference=invoice_id,
                delta=grant,
                balance_after=user.document_credit_balance,
            )
        )
    return True


def _apply_checkout_completed(db: Session, session: dict[str, Any]) -> bool:
    user_id = session.get("client_reference_id")
    metadata_user = _dict(session.get("metadata")).get("user_id")
    if not isinstance(user_id, str) or user_id != metadata_user:
        return False
    try:
        parsed_user_id = UUID(user_id)
    except ValueError:
        return False
    user = db.scalar(select(User).where(User.id == parsed_user_id).with_for_update())
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")
    if user is None or not isinstance(customer_id, str):
        return False
    if user.stripe_customer_id not in {None, customer_id}:
        return False
    user.stripe_customer_id = customer_id
    if isinstance(subscription_id, str):
        user.stripe_subscription_id = subscription_id
    if user.subscription_status == "free":
        user.subscription_status = "incomplete"
    return True


def _process_event(db: Session, event: dict[str, Any]) -> str:
    event_type = event.get("type")
    event_created = _period_end(event.get("created")) or datetime.now(UTC)
    data = _dict(event.get("data"))
    obj = _dict(data.get("object"))
    if event_type == "checkout.session.completed":
        processed = _apply_checkout_completed(db, obj)
    elif event_type in {
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    }:
        processed = _apply_subscription_event(db, event, event_created)
    elif event_type == "invoice.paid":
        processed = _apply_invoice_paid(db, obj)
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
        webhook_record.processed_at = datetime.now(UTC)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Verified Stripe event could not be committed.")
        raise HTTPException(status_code=503, detail="Billing event could not be processed.") from error
    return {"received": True}
