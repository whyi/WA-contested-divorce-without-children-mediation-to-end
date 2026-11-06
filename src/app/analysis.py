import logging
from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth_routes import require_current_user
from app.config import Settings, get_settings, provider_data_handling_notice
from app.database import get_db
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
    User,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["document analysis"])
ANALYSIS_PURPOSE = "Extract candidate case facts for the user to review."
ANALYSIS_DATA_SENT = (
    "Only extracted text, opaque document IDs, and page locations from the documents you select "
    "are sent. Account details, case-profile data, and negotiation history are not sent."
)


class AnalysisDisclosure(BaseModel):
    available: bool
    provider: str | None
    model_id: str | None
    region: str | None
    notice_version: str | None
    purpose: str
    data_sent: str
    data_handling_notice: str | None


class AnalysisDocumentOption(BaseModel):
    document_id: UUID
    extraction_job_id: UUID | None
    extension: str
    extraction_status: Literal[
        "stored",
        "queued",
        "processing",
        "needs_attention",
        "failed",
        "completed",
    ]
    extraction_error_code: str | None = None
    eligible: bool
    page_count: int | None


class AnalysisOptionsResponse(BaseModel):
    disclosure: AnalysisDisclosure
    documents: list[AnalysisDocumentOption]


class AnalysisRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idempotency_key: UUID
    document_ids: list[UUID] = Field(min_length=1, max_length=50)
    notice_version: str = Field(min_length=1, max_length=100)
    consent: Literal[True]

    @field_validator("document_ids")
    @classmethod
    def document_ids_must_be_unique(cls, values: list[UUID]) -> list[UUID]:
        if len(values) != len(set(values)):
            raise ValueError("Selected document IDs must be unique.")
        return values


class AnalysisDocumentJobRead(BaseModel):
    id: UUID
    document_id: UUID
    status: Literal[
        "queued",
        "processing",
        "completed",
        "partial",
        "failed",
        "cancelled",
    ]
    attempts: int
    error_code: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class AnalysisRequestRead(BaseModel):
    request_id: UUID
    consent_id: UUID
    status: Literal[
        "queued",
        "processing",
        "completed",
        "partial",
        "failed",
        "cancelled",
    ]
    jobs: list[AnalysisDocumentJobRead]


class AnalysisConsentRevocationRead(BaseModel):
    request_id: UUID
    status: Literal[
        "queued",
        "processing",
        "completed",
        "partial",
        "failed",
        "cancelled",
    ]


class AnalysisProposalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    source_sha256: str
    field_key: str
    value: str
    source_quote: str
    source_page_number: int | None
    confidence: Literal["high", "medium", "low"]
    uncertainty: str
    label: Literal["AI suggestion"] = "AI suggestion"


def is_analysis_available(settings: Settings) -> bool:
    return (
        settings.ai_analysis_enabled
        and settings.auth_enabled
        and settings.case_data_enabled
        and settings.case_materials_enabled
        and not settings.demo_mode_enabled
        and bool((settings.bedrock_model_id or "").strip())
        and bool((settings.bedrock_region or "").strip())
        and bool((settings.ai_analysis_notice_version or "").strip())
        and bool((settings.ai_analysis_data_handling_notice or "").strip())
        and settings.production_ai_readiness_passed()
    )


def analysis_disclosure(settings: Settings | None = None) -> AnalysisDisclosure:
    settings = settings or get_settings()
    return AnalysisDisclosure(
        available=is_analysis_available(settings),
        provider="Amazon Bedrock",
        model_id=settings.bedrock_model_id or None,
        region=settings.bedrock_region or None,
        notice_version=settings.ai_analysis_notice_version or None,
        purpose=ANALYSIS_PURPOSE,
        data_sent=ANALYSIS_DATA_SENT,
        data_handling_notice=provider_data_handling_notice(
            settings.ai_analysis_data_handling_notice
        ),
    )


def aggregate_analysis_status(statuses: list[str]) -> str:
    if not statuses:
        return "failed"
    if "processing" in statuses:
        return "processing"
    if "queued" in statuses:
        return "queued"
    if all(status == "completed" for status in statuses):
        return "completed"
    if all(status == "failed" for status in statuses):
        return "failed"
    if all(status == "cancelled" for status in statuses):
        return "cancelled"
    return "partial"


def case_analysis_options(
    db: Session,
    case_id: UUID,
    settings: Settings | None = None,
) -> AnalysisOptionsResponse:
    settings = settings or get_settings()
    documents = db.scalars(
        select(Document)
        .where(Document.case_id == case_id)
        .order_by(Document.created_at, Document.id)
    ).all()
    options = []
    for document in documents:
        extraction_job = _current_extraction_job(db, document)
        extraction = _latest_extraction(db, document.id)
        extraction_status = extraction_job.status if extraction_job is not None else "stored"
        options.append(
            AnalysisDocumentOption(
                document_id=document.id,
                extraction_job_id=(
                    extraction_job.id if extraction_job is not None else None
                ),
                extension=document.extension,
                extraction_status=extraction_status,
                extraction_error_code=(
                    extraction_job.error_code
                    if extraction_job is not None
                    else None
                ),
                eligible=(
                    is_analysis_available(settings)
                    and extraction_job is not None
                    and extraction_job.status == "completed"
                    and extraction is not None
                    and bool(extraction.extracted_text.strip())
                ),
                page_count=extraction.page_count if extraction is not None else None,
            )
        )
    return AnalysisOptionsResponse(
        disclosure=analysis_disclosure(settings),
        documents=options,
    )


def create_analysis_request(
    db: Session,
    case_id: UUID,
    user_id: UUID,
    payload: AnalysisRequestCreate,
    settings: Settings | None = None,
) -> DocumentAnalysisRequest:
    settings = settings or get_settings()
    disclosure = analysis_disclosure(settings)
    if not disclosure.available:
        raise HTTPException(
            status_code=503,
            detail="Document analysis is unavailable until provider and consent-notice settings are configured.",
        )
    if payload.notice_version != disclosure.notice_version:
        raise HTTPException(
            status_code=409,
            detail="The analysis notice has changed. Review the current notice before continuing.",
        )

    existing = db.get(DocumentAnalysisRequest, payload.idempotency_key)
    if existing is not None:
        return _existing_idempotent_request(
            db,
            existing,
            case_id,
            user_id,
            payload.document_ids,
            payload.notice_version,
        )

    documents = db.scalars(
        select(Document).where(
            Document.case_id == case_id,
            Document.id.in_(payload.document_ids),
        )
    ).all()
    documents_by_id = {document.id: document for document in documents}
    if len(documents_by_id) != len(payload.document_ids):
        raise HTTPException(
            status_code=404,
            detail="One or more selected documents are unavailable.",
        )

    for document_id in payload.document_ids:
        document = documents_by_id[document_id]
        extraction_job = _current_extraction_job(db, document)
        extraction = _latest_extraction(db, document.id)
        if (
            extraction_job is None
            or extraction_job.status != "completed"
            or extraction is None
            or not extraction.extracted_text.strip()
        ):
            raise HTTPException(
                status_code=409,
                detail="One or more selected documents are not ready for analysis.",
            )

    request_id = payload.idempotency_key
    consent = DocumentAnalysisConsent(
        id=uuid4(),
        case_id=case_id,
        user_id=user_id,
        request_id=request_id,
        notice_version=disclosure.notice_version,
        provider=disclosure.provider,
        model_id=disclosure.model_id,
        region=disclosure.region,
        purpose=disclosure.purpose,
        data_sent=disclosure.data_sent,
        data_handling_notice=disclosure.data_handling_notice,
        consented_at=datetime.now(UTC),
    )
    request = DocumentAnalysisRequest(
        id=request_id,
        case_id=case_id,
        user_id=user_id,
        consent_id=consent.id,
        status="queued",
    )
    jobs = [
        DocumentAnalysisJob(
            request_id=request_id,
            document_id=document_id,
            source_sha256=documents_by_id[document_id].sha256,
            status="queued",
        )
        for document_id in payload.document_ids
    ]
    db.add_all([consent, request, *jobs])
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.get(DocumentAnalysisRequest, request_id)
        if existing is None:
            raise
        return _existing_idempotent_request(
            db,
            existing,
            case_id,
            user_id,
            payload.document_ids,
            payload.notice_version,
        )
    except SQLAlchemyError:
        db.rollback()
        raise
    return request


def retry_analysis_job(
    db: Session,
    case_id: UUID,
    request_id: UUID,
    document_id: UUID,
    settings: Settings | None = None,
) -> DocumentAnalysisJob:
    request = _request_for_case(db, case_id, request_id)
    consent = db.get(DocumentAnalysisConsent, request.consent_id)
    job = db.scalar(
        select(DocumentAnalysisJob)
        .where(
            DocumentAnalysisJob.request_id == request.id,
            DocumentAnalysisJob.document_id == document_id,
        )
        .with_for_update()
    )
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    if (
        consent is None
        or consent.revoked_at is not None
        or consent.request_id != request.id
        or consent.case_id != case_id
    ):
        raise HTTPException(status_code=409, detail="Analysis consent is no longer active.")
    if job.status != "failed":
        raise HTTPException(status_code=409, detail="Only failed analysis jobs can be retried.")
    if not is_analysis_available(settings or get_settings()):
        raise HTTPException(status_code=503, detail="Document analysis is unavailable.")
    document = db.get(Document, document_id)
    extraction_job = _current_extraction_job(db, document) if document is not None else None
    extraction = _latest_extraction(db, document_id)
    if (
        document is None
        or document.case_id != case_id
        or document.sha256 != job.source_sha256
        or extraction_job is None
        or extraction_job.status != "completed"
        or extraction is None
        or not extraction.extracted_text.strip()
    ):
        raise HTTPException(
            status_code=409,
            detail="The source document is no longer eligible for analysis.",
        )

    job.status = "queued"
    job.attempts = 0
    job.error_code = None
    job.lease_token = None
    job.lease_expires_at = None
    job.completed_at = None
    request.status = "queued"
    db.commit()
    return job


def revoke_analysis_consent(
    db: Session,
    case_id: UUID,
    consent_id: UUID,
    user_id: UUID,
) -> DocumentAnalysisRequest:
    consent = db.scalar(
        select(DocumentAnalysisConsent).where(
            DocumentAnalysisConsent.id == consent_id,
            DocumentAnalysisConsent.case_id == case_id,
            DocumentAnalysisConsent.user_id == user_id,
        ).with_for_update()
    )
    if consent is None:
        raise HTTPException(status_code=404, detail="Analysis consent not found.")
    request = db.scalar(
        select(DocumentAnalysisRequest)
        .where(
            DocumentAnalysisRequest.consent_id == consent.id,
            DocumentAnalysisRequest.id == consent.request_id,
            DocumentAnalysisRequest.case_id == case_id,
        )
        .with_for_update()
    )
    if request is None:
        raise HTTPException(status_code=404, detail="Analysis request not found.")
    if consent.revoked_at is None:
        consent.revoked_at = datetime.now(UTC)
        jobs = db.scalars(
            select(DocumentAnalysisJob)
            .where(
                DocumentAnalysisJob.request_id == request.id,
                DocumentAnalysisJob.status == "queued",
            )
            .with_for_update()
        ).all()
        for job in jobs:
            _finish_job(job, "cancelled", "consent_revoked")
        request.status = _request_status(db, request.id)
        db.commit()
    return request


def analysis_request_read(db: Session, request: DocumentAnalysisRequest) -> AnalysisRequestRead:
    jobs = db.scalars(
        select(DocumentAnalysisJob)
        .where(DocumentAnalysisJob.request_id == request.id)
        .order_by(DocumentAnalysisJob.created_at, DocumentAnalysisJob.id)
    ).all()
    job_reads = [
        AnalysisDocumentJobRead(
            id=job.id,
            document_id=job.document_id,
            status=job.status,
            attempts=job.attempts,
            error_code=job.error_code,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
        )
        for job in jobs
    ]
    status = aggregate_analysis_status([job.status for job in jobs])
    return AnalysisRequestRead(
        request_id=request.id,
        consent_id=request.consent_id,
        status=status,
        jobs=job_reads,
    )


def proposals_for_request(
    db: Session,
    case_id: UUID,
    request_id: UUID,
) -> list[DocumentAnalysisProposal]:
    _request_for_case(db, case_id, request_id)
    return db.scalars(
        select(DocumentAnalysisProposal)
        .join(
            DocumentAnalysisJob,
            DocumentAnalysisProposal.job_id == DocumentAnalysisJob.id,
        )
        .where(DocumentAnalysisJob.request_id == request_id)
        .order_by(DocumentAnalysisProposal.created_at, DocumentAnalysisProposal.id)
    ).all()


def _authorize_case(
    db: Session,
    user: User,
    case_id: UUID,
    *,
    write: bool,
) -> None:
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
    if write and membership.role == "viewer":
        raise HTTPException(status_code=403, detail="Case is read-only.")


def _current_extraction_job(
    db: Session,
    document: Document,
) -> DocumentExtractionJob | None:
    return db.scalar(
        select(DocumentExtractionJob)
        .where(
            DocumentExtractionJob.document_id == document.id,
            DocumentExtractionJob.source_sha256 == document.sha256,
        )
        .order_by(
            DocumentExtractionJob.updated_at.desc(),
            DocumentExtractionJob.id.desc(),
        )
        .limit(1)
    )


def _latest_extraction(db: Session, document_id: UUID) -> DocumentExtraction | None:
    return db.scalar(
        select(DocumentExtraction)
        .where(DocumentExtraction.document_id == document_id)
        .order_by(
            DocumentExtraction.created_at.desc(),
            DocumentExtraction.id.desc(),
        )
        .limit(1)
    )


def _existing_idempotent_request(
    db: Session,
    request: DocumentAnalysisRequest,
    case_id: UUID,
    user_id: UUID,
    document_ids: list[UUID],
    notice_version: str,
) -> DocumentAnalysisRequest:
    consent = db.get(DocumentAnalysisConsent, request.consent_id)
    existing_document_ids = set(
        db.scalars(
            select(DocumentAnalysisJob.document_id).where(
                DocumentAnalysisJob.request_id == request.id
            )
        ).all()
    )
    if (
        request.case_id != case_id
        or request.user_id != user_id
        or consent is None
        or consent.notice_version != notice_version
        or consent.request_id != request.id
        or consent.case_id != request.case_id
        or consent.user_id != request.user_id
        or existing_document_ids != set(document_ids)
    ):
        raise HTTPException(
            status_code=409,
            detail="The analysis idempotency key was already used for a different request.",
        )
    return request


def _request_for_case(
    db: Session,
    case_id: UUID,
    request_id: UUID,
) -> DocumentAnalysisRequest:
    request = db.scalar(
        select(DocumentAnalysisRequest).where(
            DocumentAnalysisRequest.id == request_id,
            DocumentAnalysisRequest.case_id == case_id,
        )
    )
    if request is None:
        raise HTTPException(status_code=404, detail="Analysis request not found.")
    return request


def _request_status(db: Session, request_id: UUID) -> str:
    statuses = db.scalars(
        select(DocumentAnalysisJob.status).where(
            DocumentAnalysisJob.request_id == request_id
        )
    ).all()
    return aggregate_analysis_status(statuses)


def _finish_job(job: DocumentAnalysisJob, status: str, error_code: str | None) -> None:
    job.status = status
    job.error_code = error_code
    job.lease_token = None
    job.lease_expires_at = None
    job.completed_at = datetime.now(UTC)


@router.get("/cases/{case_id}/analysis/options", response_model=AnalysisOptionsResponse)
def get_case_analysis_options(
    case_id: UUID,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AnalysisOptionsResponse:
    try:
        _authorize_case(db, user, case_id, write=False)
        return case_analysis_options(db, case_id)
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        log_failure_event(logger, "analysis_options_lookup_failed", error)
        raise HTTPException(
            status_code=503,
            detail="Document analysis options are unavailable. Please try again.",
        ) from error


@router.post(
    "/cases/{case_id}/analysis-requests",
    response_model=AnalysisRequestRead,
    status_code=202,
)
def start_case_analysis(
    case_id: UUID,
    payload: AnalysisRequestCreate,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AnalysisRequestRead:
    try:
        _authorize_case(db, user, case_id, write=True)
        request = create_analysis_request(db, case_id, user.id, payload)
        return analysis_request_read(db, request)
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        log_failure_event(logger, "analysis_request_persistence_failed", error)
        raise HTTPException(
            status_code=503,
            detail="Document analysis could not be started. Please try again.",
        ) from error


@router.get(
    "/cases/{case_id}/analysis-requests/{request_id}",
    response_model=AnalysisRequestRead,
)
def get_case_analysis_request(
    case_id: UUID,
    request_id: UUID,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AnalysisRequestRead:
    try:
        _authorize_case(db, user, case_id, write=False)
        request = _request_for_case(db, case_id, request_id)
        return analysis_request_read(db, request)
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        log_failure_event(logger, "analysis_status_lookup_failed", error)
        raise HTTPException(
            status_code=503,
            detail="Document analysis status is unavailable. Please try again.",
        ) from error


@router.post(
    "/cases/{case_id}/analysis-requests/{request_id}/documents/{document_id}/retry",
    response_model=AnalysisDocumentJobRead,
)
def retry_case_analysis_document(
    case_id: UUID,
    request_id: UUID,
    document_id: UUID,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AnalysisDocumentJobRead:
    try:
        _authorize_case(db, user, case_id, write=True)
        job = retry_analysis_job(db, case_id, request_id, document_id)
        return AnalysisDocumentJobRead(
            id=job.id,
            document_id=job.document_id,
            status=job.status,
            attempts=job.attempts,
            error_code=job.error_code,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        log_failure_event(logger, "analysis_retry_persistence_failed", error)
        raise HTTPException(
            status_code=503,
            detail="Document analysis retry is unavailable. Please try again.",
        ) from error


@router.post(
    "/cases/{case_id}/analysis-consents/{consent_id}/revoke",
    response_model=AnalysisConsentRevocationRead,
)
def revoke_case_analysis_consent(
    case_id: UUID,
    consent_id: UUID,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AnalysisConsentRevocationRead:
    try:
        _authorize_case(db, user, case_id, write=True)
        request = revoke_analysis_consent(db, case_id, consent_id, user.id)
        return AnalysisConsentRevocationRead(
            request_id=request.id,
            status=analysis_request_read(db, request).status,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        log_failure_event(logger, "analysis_consent_revocation_failed", error)
        raise HTTPException(
            status_code=503,
            detail="Document analysis consent could not be revoked. Please try again.",
        ) from error


@router.get(
    "/cases/{case_id}/analysis-requests/{request_id}/proposals",
    response_model=list[AnalysisProposalRead],
)
def get_case_analysis_proposals(
    case_id: UUID,
    request_id: UUID,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AnalysisProposalRead]:
    try:
        _authorize_case(db, user, case_id, write=False)
        proposals = proposals_for_request(db, case_id, request_id)
        return [AnalysisProposalRead.model_validate(proposal) for proposal in proposals]
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        log_failure_event(logger, "analysis_proposals_lookup_failed", error)
        raise HTTPException(
            status_code=503,
            detail="Document analysis proposals are unavailable. Please try again.",
        ) from error
