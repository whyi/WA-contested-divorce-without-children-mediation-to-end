from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CaseMembership


def resolve_case_access(db: Session, case_id: UUID, user_id: UUID) -> CaseMembership | None:
    """Return the caller's membership for the case, or None when they have no access."""
    return db.scalar(
        select(CaseMembership).where(
            CaseMembership.case_id == case_id,
            CaseMembership.user_id == user_id,
            CaseMembership.revoked_at.is_(None),
        )
    )
