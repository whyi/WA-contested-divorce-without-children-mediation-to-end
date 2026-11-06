import logging
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.deletion import require_scope_active
from app.models import Case, CaseMembership, User

logger = logging.getLogger(__name__)


def require_active_case_slot(db: Session, user_id: UUID) -> User:
    try:
        user = db.get(User, user_id, with_for_update=True)
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required.")
        if getattr(user, "status", "active") != "active":
            raise HTTPException(status_code=410, detail="This account is unavailable.")
        require_scope_active(db, "account", user_id)
        if getattr(user, "account_type", "party") == "professional":
            raise HTTPException(
                status_code=403,
                detail=(
                    "Professional accounts operate cases their clients own. "
                    "Ask the party to invite you to their case."
                ),
            )
        owned_case_count = db.scalar(
            select(func.count(Case.id))
            .join(CaseMembership, CaseMembership.case_id == Case.id)
            .where(
                CaseMembership.user_id == user_id,
                CaseMembership.role == "owner",
                CaseMembership.revoked_at.is_(None),
            )
        ) or 0
    except SQLAlchemyError as error:
        logger.exception("Active case limit lookup failed.")
        raise HTTPException(
            status_code=503,
            detail="Active case availability could not be checked. Please try again.",
        ) from error
    if owned_case_count >= 1:
        raise HTTPException(
            status_code=409,
            detail=(
                "A party account can own one divorce case. Open or reopen your existing case, "
                "or invite a professional to operate it."
            ),
        )
    return user
