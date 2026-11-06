import logging
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Case, Document, DocumentCreditLedgerEntry

logger = logging.getLogger(__name__)

MAX_ATTACHMENT_BYTES = 2 * 1024 * 1024
FREE_ATTACHMENT_LIMIT = 5
PAID_ATTACHMENT_LIMIT = 100


def attachment_limit(db: Session, case_id: UUID) -> int:
    purchased = db.scalar(
        select(DocumentCreditLedgerEntry.id)
        .where(
            DocumentCreditLedgerEntry.case_id == case_id,
            DocumentCreditLedgerEntry.source_type == "package_purchase",
        )
        .limit(1)
    )
    return PAID_ATTACHMENT_LIMIT if purchased is not None else FREE_ATTACHMENT_LIMIT


def attachment_count(db: Session, case_id: UUID) -> int:
    return db.scalar(select(func.count(Document.id)).where(Document.case_id == case_id)) or 0


def attachment_usage(db: Session, case_id: UUID) -> tuple[int, int]:
    try:
        return attachment_count(db, case_id), attachment_limit(db, case_id)
    except SQLAlchemyError as error:
        logger.exception("Attachment usage lookup failed.")
        raise HTTPException(
            status_code=503,
            detail="Attachment usage could not be checked. Please try again.",
        ) from error


def enforce_attachment_quota(db: Session, case_id: UUID, incoming: int = 1) -> None:
    """Serialize on the case row, then reject uploads beyond the stored-attachment quota."""
    try:
        db.scalar(select(Case.id).where(Case.id == case_id).with_for_update())
        count = attachment_count(db, case_id)
        limit = attachment_limit(db, case_id)
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Attachment quota check failed.")
        raise HTTPException(
            status_code=503,
            detail="Attachment limits could not be checked. Please try again.",
        ) from error
    if count + incoming > limit:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                f"This case already has {count} of {limit} allowed attachments. "
                "Remove an attachment to free a slot, then try again."
            ),
        )
