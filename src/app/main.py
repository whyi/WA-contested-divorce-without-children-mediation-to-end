import json
import logging
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal, TypeAlias
from uuid import UUID

from botocore.exceptions import BotoCoreError
from fastapi import Depends, FastAPI, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.analysis import router as analysis_router
from app.auth import verify_token
from app.auth_routes import require_current_user, router as auth_router
from app.billing_routes import router as billing_router
from app.case_delegation import resolve_case_access, router as case_delegation_router
from app.case_lifecycle import lifecycle_write_allowed, router as case_lifecycle_router
from app.case_limits import require_active_case_slot
from app.config import get_settings
from app.database import SessionLocal, get_db
from app.demo import ensure_demo_user
from app.documents import (
    DOCX_MEDIA_TYPE,
    PDF_MEDIA_TYPE,
    convert_docx_to_pdf,
    convert_pdf_to_docx,
    extract_document,
    render_template,
)
from app.extraction import retry_failed_extraction_job
from app.existing_offer import (
    METADATA_KEY as EXISTING_OFFER_METADATA_KEY,
    ExistingOfferCreate,
    build_offer_record,
    router as existing_offer_router,
)
from app.export_integrations import router as export_integrations_router
from app.models import (
    AuthSession,
    Case,
    CaseDelegationInvitation,
    CaseMembership,
    Document,
    DocumentExtraction,
    DocumentExtractionJob,
    NegotiationEvent,
    SettlementNegotiationAttempt,
    User,
)
from app.property_tracing import (
    AssetClassification,
    PropertyAsset,
    PropertyTracingUpdate,
    RelationshipMilestones,
    classify_asset,
)
from app.materials import router as materials_router
from app.offer_response import router as offer_response_router
from app.review import router as review_router
from app.settlement_routes import demo_export_router, router as settlement_router
from app.services import (
    Artifact,
    get_case_or_none,
    get_document_or_none,
    store_artifacts,
)
from app.storage import ObjectStorage
from app.validation import UploadValidationError, validate_upload

logger = logging.getLogger(__name__)
settings = get_settings()
storage = ObjectStorage(settings)


class OAuthCallbackQueryFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        arguments = record.args
        if (
            isinstance(arguments, tuple)
            and len(arguments) > 2
            and isinstance(arguments[2], str)
        ):
            request_path = arguments[2]
            path = request_path.split("?", 1)[0]
            if path.startswith("/api/export-integrations/") and path.endswith("/callback"):
                record.args = (*arguments[:2], path, *arguments[3:])
        return True


logging.getLogger("uvicorn.access").addFilter(OAuthCallbackQueryFilter())


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.demo_mode_enabled:
        with SessionLocal() as db:
            ensure_demo_user(db)
            db.commit()
    yield


app = FastAPI(
    title="Washington Mediation Document Workflow",
    version="0.1.0",
    description="Local-development foundation for case and document workflows.",
    lifespan=lifespan,
)
app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(case_lifecycle_router)
app.include_router(case_delegation_router)
app.include_router(export_integrations_router)
app.include_router(materials_router)
app.include_router(existing_offer_router)
app.include_router(offer_response_router)
app.include_router(analysis_router)
app.include_router(review_router)
app.include_router(settlement_router)
app.include_router(demo_export_router)

DbSession: TypeAlias = Annotated[Session, Depends(get_db)]
LOGIN_PAGE = Path(__file__).parent / "static" / "index.html"


@app.middleware("http")
async def authenticate_and_authorize_case_data(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    path = request.url.path
    is_case_data_path = (
        path == "/cases"
        or path.startswith("/cases/")
        or path == "/documents"
        or path.startswith("/documents/")
    )
    if is_case_data_path:
        if (
            not settings.auth_enabled
            or not settings.case_data_enabled
            or not settings.auth_jwt_secret
            or len(settings.auth_jwt_secret.encode()) < 32
        ):
            return JSONResponse(
                status_code=503,
                content={"detail": "Authentication is not configured. Case data APIs are unavailable."},
            )
        token = request.cookies.get("auth_access")
        authorization = request.headers.get("authorization", "")
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        if not token:
            return JSONResponse(status_code=401, content={"detail": "Authentication required."})
        if request.cookies.get("auth_access") and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            csrf_cookie = request.cookies.get("auth_csrf")
            csrf_header = request.headers.get("x-csrf-token")
            if (
                not csrf_cookie
                or not csrf_header
                or not secrets.compare_digest(csrf_cookie, csrf_header)
            ):
                return JSONResponse(status_code=403, content={"detail": "CSRF validation failed."})
        try:
            claims = verify_token(token, settings, "access")
            user_id = UUID(claims["sub"])
            session_id = UUID(claims["sid"])
        except (ValueError, KeyError):
            return JSONResponse(status_code=401, content={"detail": "Authentication required."})
        try:
            with SessionLocal() as db:
                session = db.get(AuthSession, session_id)
                user = db.get(User, user_id)
                now = datetime.now(UTC)
                if (
                    session is None
                    or user is None
                    or session.user_id != user.id
                    or session.revoked_at is not None
                    or session.idle_expires_at <= now
                    or session.absolute_expires_at <= now
                    or user.status != "active"
                ):
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Authentication required."},
                    )
                session.last_used_at = now
                session.idle_expires_at = min(
                    now + timedelta(days=settings.auth_idle_session_days),
                    session.absolute_expires_at,
                )
                request.state.user_id = user.id
                if path.startswith("/cases/"):
                    case_id = UUID(path.split("/")[2])
                elif path.startswith("/documents/"):
                    document_id = UUID(path.split("/")[2])
                    document = db.get(Document, document_id)
                    if document is None:
                        return JSONResponse(status_code=404, content={"detail": "Document not found."})
                    case_id = document.case_id
                else:
                    case_id = None
                if case_id is not None:
                    membership, denial = resolve_case_access(db, case_id, user_id, path)
                    if denial is not None:
                        return JSONResponse(status_code=denial[0], content={"detail": denial[1]})
                    if request.method != "GET" and membership.role == "viewer":
                        return JSONResponse(status_code=403, content={"detail": "Case is read-only."})
                    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
                        case = db.get(Case, case_id)
                        if case is not None and not lifecycle_write_allowed(case, path):
                            return JSONResponse(
                                status_code=409,
                                content={"detail": "This case is closed and read-only. Reopen it to make changes."},
                            )
                db.commit()
        except ValueError:
            return JSONResponse(status_code=404, content={"detail": "Case not found."})
        except SQLAlchemyError:
            logger.exception("Case authentication or authorization lookup failed.")
            return JSONResponse(
                status_code=503,
                content={"detail": "Authentication services are unavailable."},
            )
    return await call_next(request)


class CaseCreate(BaseModel):
    status: Literal["draft", "mediation", "settlement", "finalized"] = "draft"
    metadata: dict = Field(default_factory=dict)
    case_title: str | None = Field(default=None, max_length=120)
    workflow_mode: Literal["upload", "wizard"] | None = None
    asset_liability_inventory: dict = Field(default_factory=dict)
    relationship_milestones: RelationshipMilestones = Field(
        default_factory=RelationshipMilestones
    )
    property_assets: list[PropertyAsset] = Field(default_factory=list, max_length=250)
    existing_offer: ExistingOfferCreate | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_cannot_set_existing_offer(cls, value: dict) -> dict:
        if EXISTING_OFFER_METADATA_KEY in value:
            raise ValueError("Use existing_offer to record an existing offer.")
        return value


class CaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    metadata_json: dict
    asset_liability_inventory: dict
    relationship_milestones: dict
    property_assets: list[dict]


class ClassifiedPropertyAsset(PropertyAsset):
    classification: AssetClassification


class PropertyTracingRead(BaseModel):
    relationship_milestones: RelationshipMilestones
    assets: list[ClassifiedPropertyAsset]
    classification_notice: str = (
        "Property classifications are organizational candidates only, not legal determinations."
    )


class NegotiationCreate(BaseModel):
    event_type: str = Field(min_length=1, max_length=80)
    payload: dict


class NegotiationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    event_type: str
    payload: dict


class DocumentRead(BaseModel):
    id: UUID
    extension: str
    media_type: str
    sha256: str
    size_bytes: int


class ExtractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    extracted_text: str
    page_count: int
    review_status: str


class DocumentExtractionStatus(BaseModel):
    document_id: UUID
    job_id: UUID | None
    status: Literal[
        "stored",
        "queued",
        "processing",
        "needs_attention",
        "failed",
        "completed",
    ]
    error_code: str | None
    page_count: int | None


class RenderResponse(BaseModel):
    docx: DocumentRead
    pdf: DocumentRead


class ConversionResponse(BaseModel):
    document: DocumentRead
    extraction: ExtractionRead


class DashboardCaseStatus(BaseModel):
    id: UUID
    status: str
    title: str
    workflow_mode: Literal["upload", "wizard"] | None
    attempt_ordinal: int
    delegated_to: str | None = None


class DashboardData(BaseModel):
    has_cases: bool
    case_count: int
    active_case_count: int
    account_type: Literal["party", "professional"] = "party"
    cases: list[DashboardCaseStatus]


class DashboardStatus(BaseModel):
    status: Literal["success"] = "success"
    data: DashboardData


def _document_response(document) -> DocumentRead:
    return DocumentRead(
        id=document.id,
        extension=document.extension,
        media_type=document.media_type,
        sha256=document.sha256,
        size_bytes=document.size_bytes,
    )


def _read_upload(upload: UploadFile) -> bytes:
    content = upload.file.read(settings.max_upload_bytes + 1)
    try:
        validate_upload(
            upload.filename or "",
            content,
            "docx" if (upload.filename or "").lower().endswith(".docx") else "pdf",
            settings.max_upload_bytes,
        )
    except UploadValidationError as error:
        status = 413 if len(content) > settings.max_upload_bytes else 415
        raise HTTPException(status_code=status, detail=str(error)) from error
    return content


def _require_case(db: Session, case_id: UUID) -> Case:
    case = get_case_or_none(db, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    return case


def _extract(content: bytes, extension: str):
    try:
        return extract_document(content, extension, settings)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home() -> HTMLResponse:
    return HTMLResponse(LOGIN_PAGE.read_text(encoding="utf-8"))


@app.get("/demo", response_class=HTMLResponse, include_in_schema=False)
@app.get("/demo/dashboard", response_class=HTMLResponse, include_in_schema=False)
@app.get("/demo/1/dashboard", response_class=HTMLResponse, include_in_schema=False)
@app.get("/demo/2/dashboard", response_class=HTMLResponse, include_in_schema=False)
@app.get(
    "/demo/settlement-completion",
    response_class=HTMLResponse,
    include_in_schema=False,
)
@app.get("/demo/documents", response_class=HTMLResponse, include_in_schema=False)
@app.get("/demo/wizard", response_class=HTMLResponse, include_in_schema=False)
@app.get("/demo/files", response_class=HTMLResponse, include_in_schema=False)
@app.get("/settlement-completion", response_class=HTMLResponse, include_in_schema=False)
@app.get("/onboarding/upload", response_class=HTMLResponse, include_in_schema=False)
@app.get("/onboarding/wizard", response_class=HTMLResponse, include_in_schema=False)
def onboarding_page() -> HTMLResponse:
    return home()


@app.get("/demo/1", include_in_schema=False)
def demo_one_entry() -> RedirectResponse:
    return RedirectResponse("/demo/1/dashboard")


@app.get("/demo/2", include_in_schema=False)
def demo_two_entry() -> RedirectResponse:
    return RedirectResponse("/demo/2/dashboard")


@app.get("/api/v1/dashboard/status", response_model=DashboardStatus)
def dashboard_status(
    user: Annotated[User, Depends(require_current_user)],
    db: DbSession,
) -> DashboardStatus:
    try:
        rows = db.execute(
            select(
                Case.id,
                Case.status,
                Case.metadata_json,
                func.coalesce(func.max(SettlementNegotiationAttempt.attempt_ordinal), 1),
                CaseMembership.role,
                CaseMembership.suspended_at,
            )
            .join(CaseMembership, CaseMembership.case_id == Case.id)
            .outerjoin(
                SettlementNegotiationAttempt,
                SettlementNegotiationAttempt.case_id == Case.id,
            )
            .where(
                CaseMembership.user_id == user.id,
                CaseMembership.revoked_at.is_(None),
                or_(
                    CaseMembership.suspended_at.is_not(None),
                    and_(Case.status != "finalized", Case.closed_at.is_(None)),
                ),
            )
            .group_by(Case.id, CaseMembership.role, CaseMembership.suspended_at)
            .order_by(Case.created_at.desc(), Case.id)
        ).all()
    except SQLAlchemyError as error:
        logger.exception("Dashboard case-status lookup failed.")
        raise HTTPException(
            status_code=503,
            detail="Dashboard status is unavailable. Please try again.",
        ) from error

    delegates: dict[UUID, str] = {}
    suspended_ids = [row[0] for row in rows if row[5] is not None]
    if suspended_ids:
        try:
            delegates = dict(
                db.execute(
                    select(
                        CaseDelegationInvitation.case_id,
                        CaseDelegationInvitation.invitee_email,
                    ).where(
                        CaseDelegationInvitation.case_id.in_(suspended_ids),
                        CaseDelegationInvitation.status == "accepted",
                    )
                ).all()
            )
        except SQLAlchemyError as error:
            logger.exception("Dashboard delegation lookup failed.")
            raise HTTPException(
                status_code=503,
                detail="Dashboard status is unavailable. Please try again.",
            ) from error

    cases = []
    active_case_count = 0
    for case_id, case_status, metadata, attempt_ordinal, role, suspended_at in rows:
        metadata = metadata if isinstance(metadata, dict) else {}
        case_title = metadata.get("case_title")
        if not isinstance(case_title, str) or not case_title.strip():
            case_title = "New case"
        workflow_mode = metadata.get("workflow_mode")
        cases.append(
            DashboardCaseStatus(
                id=case_id,
                status=case_status,
                title=case_title.strip(),
                workflow_mode=workflow_mode if workflow_mode in {"upload", "wizard"} else None,
                attempt_ordinal=attempt_ordinal,
                delegated_to=(
                    delegates.get(case_id, "your delegate") if suspended_at is not None else None
                ),
            )
        )
        if role == "owner":
            active_case_count += 1
    return DashboardStatus(
        data=DashboardData(
            has_cases=bool(cases),
            case_count=len(cases),
            active_case_count=active_case_count,
            account_type="professional" if getattr(user, "account_type", None) == "professional" else "party",
            cases=cases,
        )
    )


@app.get("/readyz")
def readiness() -> dict[str, str]:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        storage.check_ready()
    except SQLAlchemyError as error:
        logger.exception("Database readiness check failed.")
        raise HTTPException(status_code=503, detail="Database is unavailable.") from error
    except BotoCoreError as error:
        logger.exception("Object-storage readiness check failed.")
        raise HTTPException(status_code=503, detail="Object storage is unavailable.") from error
    return {"status": "ready"}


@app.post("/cases", response_model=CaseRead, status_code=201)
def create_case(payload: CaseCreate, request: Request, db: DbSession) -> Case:
    user_id = request.state.user_id
    require_active_case_slot(db, user_id)
    case_metadata = dict(payload.metadata)
    if payload.case_title and payload.case_title.strip():
        case_metadata["case_title"] = payload.case_title.strip()
    if payload.workflow_mode:
        case_metadata["workflow_mode"] = payload.workflow_mode
    if payload.existing_offer is not None:
        case_metadata[EXISTING_OFFER_METADATA_KEY] = build_offer_record(
            payload.existing_offer.exists, payload.existing_offer.notes, []
        )
    case = Case(
        status=payload.status,
        metadata_json=case_metadata,
        asset_liability_inventory=payload.asset_liability_inventory,
        relationship_milestones=payload.relationship_milestones.model_dump(mode="json"),
        property_assets=[asset.model_dump(mode="json") for asset in payload.property_assets],
    )
    db.add(case)
    db.flush()
    db.add(CaseMembership(case_id=case.id, user_id=request.state.user_id, role="owner"))
    db.commit()
    db.refresh(case)
    return case


@app.get("/cases/{case_id}", response_model=CaseRead)
def read_case(case_id: UUID, db: DbSession) -> Case:
    return _require_case(db, case_id)


def _property_tracing_response(case: Case) -> PropertyTracingRead:
    milestones = RelationshipMilestones.model_validate(case.relationship_milestones or {})
    assets = [
        PropertyAsset.model_validate(asset)
        for asset in (case.property_assets or [])
    ]
    return PropertyTracingRead(
        relationship_milestones=milestones,
        assets=[
            ClassifiedPropertyAsset(
                **asset.model_dump(),
                classification=classify_asset(asset, milestones),
            )
            for asset in assets
        ],
    )


@app.get(
    "/cases/{case_id}/property-tracing",
    response_model=PropertyTracingRead,
)
def read_property_tracing(case_id: UUID, db: DbSession) -> PropertyTracingRead:
    return _property_tracing_response(_require_case(db, case_id))


@app.put(
    "/cases/{case_id}/property-tracing",
    response_model=PropertyTracingRead,
)
def update_property_tracing(
    case_id: UUID,
    payload: PropertyTracingUpdate,
    db: DbSession,
) -> PropertyTracingRead:
    case = _require_case(db, case_id)
    case.relationship_milestones = payload.relationship_milestones.model_dump(mode="json")
    case.property_assets = [
        asset.model_dump(mode="json") for asset in payload.assets
    ]
    try:
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Case property-tracing update failed.")
        raise HTTPException(
            status_code=503,
            detail="Property-tracing data could not be saved. Please try again.",
        ) from error
    return _property_tracing_response(case)


@app.get(
    "/cases/{case_id}/documents/{document_id}/extraction-status",
    response_model=DocumentExtractionStatus,
)
def document_extraction_status(
    case_id: UUID,
    document_id: UUID,
    db: DbSession,
) -> DocumentExtractionStatus:
    try:
        document = get_document_or_none(db, document_id)
        if document is None or document.case_id != case_id:
            raise HTTPException(status_code=404, detail="Document not found.")
        job = db.scalar(
            select(DocumentExtractionJob)
            .where(
                DocumentExtractionJob.document_id == document.id,
                DocumentExtractionJob.source_sha256 == document.sha256,
            )
            .order_by(DocumentExtractionJob.updated_at.desc(), DocumentExtractionJob.id)
            .limit(1)
        )
        extraction = db.scalar(
            select(DocumentExtraction)
            .where(DocumentExtraction.document_id == document.id)
            .order_by(DocumentExtraction.created_at.desc(), DocumentExtraction.id)
            .limit(1)
        )
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        logger.exception("Document extraction status lookup failed.")
        raise HTTPException(
            status_code=503,
            detail="Document processing status is unavailable. Please try again.",
        ) from error

    if job is not None:
        if job.status == "completed" and extraction is None:
            logger.error("Completed extraction job has no persisted extraction result.")
            raise HTTPException(
                status_code=503,
                detail="Document processing status is unavailable. Please try again.",
            )
        status = job.status
    else:
        status = "completed" if extraction is not None else "stored"
    return DocumentExtractionStatus(
        document_id=document.id,
        job_id=job.id if job is not None else None,
        status=status,
        error_code=job.error_code if job is not None else None,
        page_count=extraction.page_count if extraction is not None else None,
    )


@app.post(
    "/cases/{case_id}/documents/{document_id}/extraction-jobs/{job_id}/retry",
    response_model=DocumentExtractionStatus,
)
def retry_case_document_extraction(
    case_id: UUID,
    document_id: UUID,
    job_id: UUID,
    response: Response,
    db: DbSession,
) -> DocumentExtractionStatus:
    response.headers["Cache-Control"] = "no-store"
    try:
        document = db.get(Document, document_id)
        if document is None or document.case_id != case_id:
            raise HTTPException(status_code=404, detail="Document not found.")
        job = db.get(DocumentExtractionJob, job_id)
        if (
            job is None
            or job.document_id != document.id
            or job.source_sha256 != document.sha256
        ):
            raise HTTPException(status_code=404, detail="Extraction job not found.")
        if job.status != "failed":
            raise HTTPException(
                status_code=409,
                detail="Only failed extraction jobs can be retried.",
            )
        retried = retry_failed_extraction_job(db, job.id, job.request_id)
        if retried is None:
            raise HTTPException(status_code=404, detail="Extraction job not found.")
        return DocumentExtractionStatus(
            document_id=document.id,
            job_id=retried.id,
            status=retried.status,
            error_code=retried.error_code,
            page_count=None,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Document extraction retry could not be persisted.")
        raise HTTPException(
            status_code=503,
            detail="Document extraction retry is unavailable. Please try again.",
        ) from error


@app.post(
    "/cases/{case_id}/negotiations",
    response_model=NegotiationRead,
    status_code=201,
)
def add_negotiation(case_id: UUID, payload: NegotiationCreate, db: DbSession) -> NegotiationEvent:
    _require_case(db, case_id)
    event = NegotiationEvent(
        case_id=case_id,
        event_type=payload.event_type.strip(),
        payload=payload.payload,
    )
    if not event.event_type:
        raise HTTPException(status_code=422, detail="Negotiation event type cannot be blank.")
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@app.post("/cases/{case_id}/documents/render", response_model=RenderResponse, status_code=201)
def render_case_document(
    case_id: UUID,
    db: DbSession,
    template_file: Annotated[UploadFile, File()],
    context: Annotated[str, Form()],
) -> RenderResponse:
    _require_case(db, case_id)
    if not (template_file.filename or "").lower().endswith(".docx"):
        raise HTTPException(status_code=415, detail="Expected a .docx template.")
    template_bytes = _read_upload(template_file)
    if len(context.encode("utf-8")) > 64 * 1024:
        raise HTTPException(status_code=413, detail="Template context exceeds the 64 KiB limit.")
    try:
        render_context = json.loads(context)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=422, detail="Template context must be valid JSON.") from error
    if not isinstance(render_context, dict):
        raise HTTPException(status_code=422, detail="Template context must be a JSON object.")

    try:
        docx_bytes = render_template(template_bytes, render_context)
        pdf_bytes = convert_docx_to_pdf(docx_bytes, settings)
    except TimeoutError as error:
        raise HTTPException(status_code=504, detail=str(error)) from error
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    documents, _ = store_artifacts(
        db,
        storage,
        case_id,
        [
            Artifact(docx_bytes, "docx", DOCX_MEDIA_TYPE),
            Artifact(pdf_bytes, "pdf", PDF_MEDIA_TYPE),
        ],
    )
    docx, pdf = documents
    return RenderResponse(docx=_document_response(docx), pdf=_document_response(pdf))


@app.post(
    "/cases/{case_id}/documents/pdf-to-docx",
    response_model=ConversionResponse,
    status_code=201,
)
def convert_case_pdf(
    case_id: UUID,
    db: DbSession,
    upload: Annotated[UploadFile, File()],
) -> ConversionResponse:
    _require_case(db, case_id)
    pdf_bytes = _read_upload(upload)
    if not (upload.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Expected a .pdf file.")
    try:
        docx_bytes = convert_pdf_to_docx(pdf_bytes, settings)
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    extracted = _extract(docx_bytes, "docx")
    documents, extraction = store_artifacts(
        db,
        storage,
        case_id,
        [Artifact(docx_bytes, "docx", DOCX_MEDIA_TYPE)],
        extraction_data=(extracted.text, extracted.page_count),
    )
    document = documents[0]
    if extraction is None:
        raise RuntimeError("The document extraction was not persisted.")
    return ConversionResponse(
        document=_document_response(document),
        extraction=ExtractionRead.model_validate(extraction),
    )


@app.post(
    "/cases/{case_id}/documents/extract",
    response_model=ConversionResponse,
    status_code=201,
)
def extract_case_document(
    case_id: UUID,
    db: DbSession,
    upload: Annotated[UploadFile, File()],
) -> ConversionResponse:
    _require_case(db, case_id)
    extension = "docx" if (upload.filename or "").lower().endswith(".docx") else "pdf"
    content = _read_upload(upload)
    extracted = _extract(content, extension)
    media_type = DOCX_MEDIA_TYPE if extension == "docx" else PDF_MEDIA_TYPE
    documents, extraction = store_artifacts(
        db,
        storage,
        case_id,
        [Artifact(content, extension, media_type)],
        extraction_data=(extracted.text, extracted.page_count),
    )
    document = documents[0]
    if extraction is None:
        raise RuntimeError("The document extraction was not persisted.")
    return ConversionResponse(
        document=_document_response(document),
        extraction=ExtractionRead.model_validate(extraction),
    )


@app.get("/documents/{document_id}/download")
def download_document(document_id: UUID, db: DbSession) -> Response:
    try:
        document = get_document_or_none(db, document_id)
    except SQLAlchemyError as error:
        logger.exception("Document metadata lookup failed.")
        raise HTTPException(
            status_code=503,
            detail="Document retrieval is unavailable. Please try again.",
        ) from error
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    try:
        content = storage.get(document.object_key)
    except BotoCoreError as error:
        logger.error("Document retrieval from object storage failed (%s).", type(error).__name__)
        raise HTTPException(
            status_code=503,
            detail="Document retrieval is unavailable. Please try again.",
        ) from error
    return Response(
        content=content,
        media_type=document.media_type,
        headers={"Content-Disposition": f'attachment; filename="{document.id}.{document.extension}"'},
    )


@app.get("/documents/{document_id}/preview")
def preview_document(document_id: UUID, db: DbSession) -> Response:
    try:
        document = db.get(Document, document_id)
    except SQLAlchemyError as error:
        logger.exception("Document metadata lookup failed for preview.")
        raise HTTPException(
            status_code=503,
            detail="Document preview is unavailable. Please try again.",
        ) from error
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    if document.extension != "pdf":
        raise HTTPException(
            status_code=415,
            detail="Inline preview is available for PDF documents; use the extracted-text view for DOCX.",
        )
    try:
        content = storage.get(document.object_key)
    except BotoCoreError as error:
        logger.error("Document preview from object storage failed (%s).", type(error).__name__)
        raise HTTPException(
            status_code=503,
            detail="Document preview is unavailable. Please try again.",
        ) from error
    return Response(
        content=content,
        media_type=document.media_type,
        headers={
            "Content-Disposition": f'inline; filename="{document.id}.pdf"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: UUID, db: DbSession) -> Response:
    try:
        document = get_document_or_none(db, document_id)
    except SQLAlchemyError as error:
        logger.exception("Document metadata lookup failed before deletion.")
        raise HTTPException(
            status_code=503,
            detail="Document deletion is unavailable. Please try again.",
        ) from error
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    try:
        storage.delete(document.object_key)
    except BotoCoreError as error:
        logger.error("Document deletion from object storage failed (%s).", type(error).__name__)
        raise HTTPException(
            status_code=503,
            detail="Document deletion is unavailable. Please try again.",
        ) from error
    try:
        db.delete(document)
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Document metadata deletion failed after object removal.")
        raise HTTPException(
            status_code=503,
            detail="Document deletion is incomplete. Please retry to finish cleanup.",
        ) from error
    return Response(status_code=204)
