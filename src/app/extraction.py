import hashlib
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from botocore.exceptions import BotoCoreError
from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.documents import DocumentExtractionError, extract_document
from app.models import Document, DocumentExtraction, DocumentExtractionJob
from app.storage import ObjectStorage
from app.validation import UploadValidationError

logger = logging.getLogger(__name__)
MAX_EXTRACTION_ATTEMPTS = 3
EXTRACTION_LEASE = timedelta(minutes=10)


@dataclass(frozen=True)
class ExtractionLease:
    job_id: UUID
    token: UUID


def enqueue_extraction_jobs(
    db: Session,
    document_ids: list[UUID],
    request_id: UUID,
) -> list[DocumentExtractionJob]:
    jobs = []
    for document_id in document_ids:
        document = db.get(Document, document_id)
        if document is None:
            raise ValueError("A requested source document is unavailable.")
        statement = select(DocumentExtractionJob).where(
            DocumentExtractionJob.document_id == document.id,
            DocumentExtractionJob.source_sha256 == document.sha256,
            DocumentExtractionJob.request_id == request_id,
        )
        existing = db.scalar(statement)
        if existing is not None:
            jobs.append(existing)
            continue

        job = DocumentExtractionJob(
            document_id=document.id,
            source_sha256=document.sha256,
            request_id=request_id,
            status="queued",
        )
        db.add(job)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            existing = db.scalar(statement)
            if existing is None:
                raise
            job = existing
        except SQLAlchemyError:
            db.rollback()
            raise
        jobs.append(job)
    return jobs


def retry_failed_extraction_job(
    db: Session,
    job_id: UUID,
    request_id: UUID,
) -> DocumentExtractionJob | None:
    job = db.scalar(
        select(DocumentExtractionJob)
        .where(
            DocumentExtractionJob.id == job_id,
            DocumentExtractionJob.request_id == request_id,
        )
        .with_for_update()
    )
    if job is None or job.status != "failed":
        return job
    job.status = "queued"
    job.attempts = 0
    job.error_code = None
    job.lease_token = None
    job.lease_expires_at = None
    job.completed_at = None
    db.commit()
    return job


def claim_next_extraction_job(
    db: Session,
    now: datetime | None = None,
) -> ExtractionLease | None:
    now = now or datetime.now(UTC)
    expired = and_(
        DocumentExtractionJob.status == "processing",
        DocumentExtractionJob.lease_expires_at <= now,
    )
    exhausted_jobs = db.scalars(
        select(DocumentExtractionJob)
        .where(
            expired,
            DocumentExtractionJob.attempts >= MAX_EXTRACTION_ATTEMPTS,
        )
        .with_for_update(skip_locked=True)
    ).all()
    for exhausted_job in exhausted_jobs:
        _finish_job(exhausted_job, "failed", "worker_interrupted")
    job = db.scalar(
        select(DocumentExtractionJob)
        .where(
            or_(
                DocumentExtractionJob.status == "queued",
                and_(
                    expired,
                    DocumentExtractionJob.attempts < MAX_EXTRACTION_ATTEMPTS,
                ),
            )
        )
        .order_by(DocumentExtractionJob.created_at, DocumentExtractionJob.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if job is None:
        db.commit()
        return None

    token = uuid4()
    job.status = "processing"
    job.attempts += 1
    job.lease_token = token
    job.lease_expires_at = now + EXTRACTION_LEASE
    job.error_code = None
    db.commit()
    return ExtractionLease(job_id=job.id, token=token)


def process_extraction_job(
    db: Session,
    storage: ObjectStorage,
    lease: ExtractionLease,
) -> None:
    try:
        job = db.get(
            DocumentExtractionJob,
            lease.job_id,
            with_for_update=True,
        )
        if (
            job is None
            or job.status != "processing"
            or job.lease_token != lease.token
        ):
            return
        document = db.get(Document, job.document_id)
        if document is None:
            _finish_job(job, "needs_attention", "source_unavailable")
            db.commit()
            return
        if document.sha256 != job.source_sha256:
            _finish_job(job, "needs_attention", "source_changed")
            db.commit()
            return
        if document.extension not in {"pdf", "docx"}:
            _finish_job(job, "needs_attention", "unsupported_file")
            db.commit()
            return

        try:
            content = storage.get(document.object_key)
        except BotoCoreError as error:
            _finish_job(job, "failed", "storage_unavailable")
            db.commit()
            logger.error("Extraction storage read failed (%s).", type(error).__name__)
            return
        if hashlib.sha256(content).hexdigest() != job.source_sha256:
            _finish_job(job, "needs_attention", "source_integrity_error")
            db.commit()
            return

        try:
            extracted = extract_document(content, document.extension, get_settings())
        except DocumentExtractionError as error:
            _finish_job(job, "needs_attention", error.error_code)
            db.commit()
            return
        except UploadValidationError as error:
            _finish_job(job, "needs_attention", error.error_code)
            db.commit()
            return
        except ValueError:
            _finish_job(job, "needs_attention", "unreadable_file")
            db.commit()
            return

        extraction = db.scalar(
            select(DocumentExtraction)
            .where(DocumentExtraction.document_id == document.id)
            .order_by(DocumentExtraction.created_at.desc(), DocumentExtraction.id)
            .limit(1)
        )
        page_data = [
            {"page_number": page.page_number, "text": page.text}
            for page in extracted.pages
        ]
        if extraction is None:
            extraction = DocumentExtraction(
                document_id=document.id,
                extracted_text=extracted.text,
                page_count=extracted.page_count,
                pages_json=page_data,
                review_status="pending_review",
            )
            db.add(extraction)
        else:
            extraction.extracted_text = extracted.text
            extraction.page_count = extracted.page_count
            extraction.pages_json = page_data
            extraction.review_status = "pending_review"
        _finish_job(
            job,
            "needs_attention" if extracted.needs_attention else "completed",
            extracted.error_code,
        )
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        logger.error("Extraction job persistence failed (%s).", type(error).__name__)


def _finish_job(job: DocumentExtractionJob, status: str, error_code: str | None) -> None:
    now = datetime.now(UTC)
    job.status = status
    job.error_code = error_code
    job.lease_token = None
    job.lease_expires_at = None
    job.completed_at = now
