from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class SubscriptionPlan:
    code: str
    name: str
    active_case_limit: int | None
    attempt_limit: int
    monthly_document_credits: int
    price_setting: str | None
    suggested_monthly_price_cents: int
    description: str


PLANS: tuple[SubscriptionPlan, ...] = (
    SubscriptionPlan(
        code="free",
        name="Free",
        active_case_limit=1,
        attempt_limit=1,
        monthly_document_credits=0,
        price_setting=None,
        suggested_monthly_price_cents=0,
        description="Preview and edit for free.",
    ),
    SubscriptionPlan(
        code="essential",
        name="Essential",
        active_case_limit=3,
        attempt_limit=3,
        monthly_document_credits=2,
        price_setting="stripe_price_id_essential",
        suggested_monthly_price_cents=1900,
        description="A few cases with room to revise.",
    ),
    SubscriptionPlan(
        code="plus",
        name="Plus",
        active_case_limit=10,
        attempt_limit=5,
        monthly_document_credits=5,
        price_setting="stripe_price_id_plus",
        suggested_monthly_price_cents=3900,
        description="More negotiations and document versions.",
    ),
    SubscriptionPlan(
        code="pro",
        name="Pro",
        active_case_limit=None,
        attempt_limit=10,
        monthly_document_credits=10,
        price_setting="stripe_price_id_pro",
        suggested_monthly_price_cents=7900,
        description="The highest limits for active casework.",
    ),
)
PLAN_BY_CODE = {plan.code: plan for plan in PLANS}
LEGACY_PLAN_BY_ATTEMPT_LIMIT = {3: "essential", 5: "plus", 10: "pro"}


def configured_price_id(settings: Any, plan: SubscriptionPlan) -> str | None:
    if plan.price_setting is None:
        return None
    value = getattr(settings, plan.price_setting, None)
    return value.strip() if isinstance(value, str) and value.strip() else None


def effective_plan_code(user: Any, now: datetime | None = None) -> str:
    plan_code = getattr(user, "subscription_plan", "free")
    status = getattr(user, "subscription_status", "free")
    if status == "legacy":
        return LEGACY_PLAN_BY_ATTEMPT_LIMIT.get(
            getattr(user, "settlement_attempt_limit", 1),
            "free",
        )
    if plan_code not in PLAN_BY_CODE or plan_code == "free":
        return "free"
    if status not in {"active", "trialing"}:
        return "free"
    period_end = getattr(user, "subscription_period_end", None)
    if period_end is not None:
        current = now or datetime.now(UTC)
        if period_end.tzinfo is None:
            period_end = period_end.replace(tzinfo=UTC)
        if period_end <= current:
            return "free"
    return plan_code


def plan_for_user(user: Any, now: datetime | None = None) -> SubscriptionPlan:
    return PLAN_BY_CODE[effective_plan_code(user, now)]


def user_settlement_attempt_limit(user: Any) -> int:
    status = getattr(user, "subscription_status", None)
    if status in {None, "legacy"}:
        limit = getattr(user, "settlement_attempt_limit", 1)
        return limit if isinstance(limit, int) and not isinstance(limit, bool) and limit in {
            1, 3, 5, 10
        } else 1
    return plan_for_user(user).attempt_limit
