import logging
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Case, CaseMembership, User
from app.subscription_plans import plan_for_user

logger = logging.getLogger(__name__)


def require_active_case_slot(db: Session, user_id: UUID) -> User:
    try:
        user = db.get(User, user_id, with_for_update=True)
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required.")
        plan = plan_for_user(user)
        active_case_count = db.scalar(
            select(func.count(Case.id))
            .join(CaseMembership, CaseMembership.case_id == Case.id)
            .where(
                CaseMembership.user_id == user_id,
                CaseMembership.role == "owner",
                CaseMembership.revoked_at.is_(None),
                Case.status != "finalized",
            )
        ) or 0
    except SQLAlchemyError as error:
        logger.exception("Active case limit lookup failed.")
        raise HTTPException(
            status_code=503,
            detail="Active case availability could not be checked. Please try again.",
        ) from error
    if plan.active_case_limit is not None and active_case_count >= plan.active_case_limit:
        raise HTTPException(
            status_code=409,
            detail=(
                f"The {plan.name} plan allows {plan.active_case_limit} active case"
                f"{'' if plan.active_case_limit == 1 else 's'}. Upgrade your plan to create another."
            ),
        )
    return user
