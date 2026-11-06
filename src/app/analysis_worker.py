import logging
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from botocore.exceptions import BotoCoreError
from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.ai import BedrockConverseClient, analyze_document_pages
from app.analysis import aggregate_analysis_status, analysis_disclosure, is_analysis_available
from app.config import Settings, get_settings
from app.database import SessionLocal
from app.deletion import scope_is_tombstoned
from app.failure_logging import log_failure_event
from app.models import (
    CaseMembership,
    Document,
    DocumentAnalysisConsent,
    DocumentAnalysisJob,
    DocumentAnalysisProposal,
    DocumentAnalysisRequest,
    DocumentExtraction,
    DocumentExtractionJob,
)

logger = logging.getLogger(__name__)
ANALYSIS_LEASE = timedelta(minutes=10)
POLL_INTERVAL_SECONDS = 2
MAX_ANALYSIS_ATTEMPTS = 3
MAX_ANALYSIS_INPUT_CHARACTERS = 200_000


@dataclass(frozen=True)
class AnalysisLease:
    job_id: UUID
    token: UUID


def claim_next_analysis_job(
    db: Session,
    now: datetime | None = None,
) -> AnalysisLease | None:
    now = now or datetime.now(UTC)
    expired = and_(
        DocumentAnalysisJob.status == "processing",
        DocumentAnalysisJob.lease_expires_at <= now,
    )
    exhausted_jobs = db.scalars(
        select(DocumentAnalysisJob)
        .where(
            expired,
            DocumentAnalysisJob.attempts >= MAX_ANALYSIS_ATTEMPTS,
        )
        .with_for_update(skip_locked=True)
    ).all()
    for job in exhausted_jobs:
        _finish_job(job, "failed", "worker_interrupted")
        request = db.get(DocumentAnalysisRequest, job.request_id)
        if request is not None:
            _refresh_request_status(db, request)

    job = db.scalar(
        select(DocumentAnalysisJob)
        .where(
            or_(
                DocumentAnalysisJob.status == "queued",
                and_(
                    expired,
                    DocumentAnalysisJob.attempts < MAX_ANALYSIS_ATTEMPTS,
                ),
            )
        )
        .order_by(DocumentAnalysisJob.created_at, DocumentAnalysisJob.id)
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
    job.lease_expires_at = now + ANALYSIS_LEASE
    job.error_code = None
    request = db.get(DocumentAnalysisRequest, job.request_id)
    if request is not None:
        request.status = "processing"
    db.commit()
    return AnalysisLease(job_id=job.id, token=token)


def process_analysis_job(
    db: Session,
    lease: AnalysisLease,
    settings: Settings | None = None,
    client: BedrockConverseClient | None = None,
) -> None:
    settings = settings or get_settings()
    try:
        job = db.get(DocumentAnalysisJob, lease.job_id, with_for_update=True)
        if (
            job is None
            or job.status != "processing"
            or job.lease_token != lease.token
        ):
            return
        request = db.get(DocumentAnalysisRequest, job.request_id)
        consent = (
            db.scalar(
                select(DocumentAnalysisConsent)
                .where(DocumentAnalysisConsent.id == request.consent_id)
                .with_for_update()
            )
            if request is not None
            else None
        )
        if (
            request is None
            or consent is None
            or consent.revoked_at is not None
            or consent.request_id != request.id
            or consent.case_id != request.case_id
            or consent.user_id != request.user_id
        ):
            _complete_without_provider(db, job, request, "cancelled", "consent_revoked")
            return
        if not is_analysis_available(settings):
            _complete_without_provider(db, job, request, "cancelled", "analysis_unavailable")
            return
        if (
            consent.notice_version != settings.ai_analysis_notice_version
            or consent.model_id != settings.bedrock_model_id
            or consent.region != settings.bedrock_region
            or consent.data_handling_notice
            != analysis_disclosure(settings).data_handling_notice
        ):
            _complete_without_provider(db, job, request, "cancelled", "consent_notice_changed")
            return
        membership = db.scalar(
            select(CaseMembership)
            .where(
                CaseMembership.case_id == request.case_id,
                CaseMembership.user_id == request.user_id,
                CaseMembership.revoked_at.is_(None),
                CaseMembership.suspended_at.is_(None),
            )
            .with_for_update()
        )
        if membership is None or membership.role == "viewer":
            _complete_without_provider(db, job, request, "cancelled", "membership_revoked")
            return

        if scope_is_tombstoned(db, "account", request.user_id) or scope_is_tombstoned(
            db, "case", request.case_id
        ):
            _complete_without_provider(db, job, request, "cancelled", "scope_deleted")
            return

        document = db.get(Document, job.document_id, with_for_update=True)
        if (
            document is None
            or document.case_id != request.case_id
            or document.sha256 != job.source_sha256
        ):
            _complete_without_provider(db, job, request, "failed", "source_unavailable")
            return
        if scope_is_tombstoned(db, "document", document.id):
            _complete_without_provider(db, job, request, "cancelled", "scope_deleted")
            return
        extraction_job = db.scalar(
            select(DocumentExtractionJob)
            .where(
                DocumentExtractionJob.document_id == document.id,
                DocumentExtractionJob.source_sha256 == document.sha256,
                DocumentExtractionJob.status == "completed",
            )
            .order_by(
                DocumentExtractionJob.updated_at.desc(),
                DocumentExtractionJob.id.desc(),
            )
            .limit(1)
        )
        extraction = db.scalar(
            select(DocumentExtraction)
            .where(DocumentExtraction.document_id == document.id)
            .order_by(
                DocumentExtraction.created_at.desc(),
                DocumentExtraction.id.desc(),
            )
            .limit(1)
        )
        if extraction_job is None or extraction is None or not extraction.extracted_text.strip():
            _complete_without_provider(db, job, request, "failed", "extraction_unavailable")
            return
        if len(extraction.extracted_text) > MAX_ANALYSIS_INPUT_CHARACTERS:
            _complete_without_provider(db, job, request, "failed", "analysis_input_too_large")
            return
        try:
            page_texts = _page_texts(extraction.pages_json)
        except ValueError:
            _complete_without_provider(
                db,
                job,
                request,
                "failed",
                "source_provenance_unavailable",
            )
            return
        result = analyze_document_pages(
            str(document.id),
            page_texts,
            settings,
            client,
            consent_granted=True,
        )
        if (
            scope_is_tombstoned(db, "account", request.user_id)
            or scope_is_tombstoned(db, "case", request.case_id)
            or scope_is_tombstoned(db, "document", document.id)
        ):
            db.rollback()
            return
        for field in result.proposals:
            db.add(
                DocumentAnalysisProposal(
                    job_id=job.id,
                    document_id=document.id,
                    source_sha256=document.sha256,
                    field_key=field.field_key,
                    value=field.value,
                    source_quote=field.source_quote,
                    source_page_number=field.source_page_number,
                    confidence=field.confidence,
                    uncertainty=field.uncertainty,
                )
            )
        status = "partial" if result.rejected_count else "completed"
        error_code = "unverified_proposals" if result.rejected_count else None
        _finish_job(job, status, error_code)
        _refresh_request_status(db, request)
        db.commit()
    except BotoCoreError as error:
        _fail_job(db, lease.job_id, "provider_unavailable", type(error).__name__)
    except (RuntimeError, ValueError) as error:
        _fail_job(db, lease.job_id, "invalid_provider_response", type(error).__name__)
    except SQLAlchemyError as error:
        db.rollback()
        log_failure_event(logger, "analysis_persistence_failed", error)


def run_once(
    session_factory: Callable[[], Session] = SessionLocal,
) -> bool:
    with session_factory() as db:
        lease = claim_next_analysis_job(db)
    if lease is None:
        return False
    with session_factory() as db:
        process_analysis_job(db, lease)
    return True


def main() -> None:
    if get_settings().case_data_enabled:
        from app.deletion_ledger import reconcile_from_environment

        reconcile_from_environment()
    while True:
        try:
            worked = run_once()
        except SQLAlchemyError as error:
            log_failure_event(logger, "analysis_worker_database_failed", error)
            worked = False
        except Exception as error:
            log_failure_event(logger, "analysis_worker_iteration_failed", error)
            worked = False
        if not worked:
            time.sleep(POLL_INTERVAL_SECONDS)


def _page_texts(pages_json: object) -> dict[int | None, str]:
    if not isinstance(pages_json, list) or not pages_json:
        raise ValueError("Extracted page provenance is unavailable.")
    pages: dict[int | None, str] = {}
    for page in pages_json:
        if not isinstance(page, Mapping):
            raise ValueError("Extracted page provenance is invalid.")
        page_number = page.get("page_number")
        text = page.get("text")
        if (
            (
                page_number is not None
                and (
                    not isinstance(page_number, int)
                    or isinstance(page_number, bool)
                    or page_number < 1
                )
            )
            or not isinstance(text, str)
            or not text.strip()
            or page_number in pages
        ):
            raise ValueError("Extracted page provenance is invalid.")
        pages[page_number] = text
    if None in pages and len(pages) != 1:
        raise ValueError("Extracted page provenance is inconsistent.")
    return pages


if __name__ == "__main__":
    main()


def _complete_without_provider(
    db: Session,
    job: DocumentAnalysisJob,
    request: DocumentAnalysisRequest | None,
    status: str,
    error_code: str,
) -> None:
    _finish_job(job, status, error_code)
    if request is not None:
        _refresh_request_status(db, request)
    db.commit()


def _fail_job(db: Session, job_id: UUID, error_code: str, error_type: str) -> None:
    db.rollback()
    job = db.get(DocumentAnalysisJob, job_id, with_for_update=True)
    if job is None or job.status != "processing":
        return
    request = db.get(DocumentAnalysisRequest, job.request_id)
    _finish_job(job, "failed", error_code)
    if request is not None:
        _refresh_request_status(db, request)
    db.commit()
    log_failure_event(logger, "analysis_job_failed", error_type)


def _finish_job(job: DocumentAnalysisJob, status: str, error_code: str | None) -> None:
    job.status = status
    job.error_code = error_code
    job.lease_token = None
    job.lease_expires_at = None
    job.completed_at = datetime.now(UTC)


def _refresh_request_status(
    db: Session,
    request: DocumentAnalysisRequest,
) -> None:
    statuses = db.scalars(
        select(DocumentAnalysisJob.status).where(
            DocumentAnalysisJob.request_id == request.id
        )
    ).all()
    request.status = aggregate_analysis_status(statuses)
