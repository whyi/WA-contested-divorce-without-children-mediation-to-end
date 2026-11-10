import json
import logging
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal, TypeAlias
from uuid import UUID
from urllib.parse import quote

from botocore.exceptions import BotoCoreError
from fastapi import Depends, FastAPI, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.analysis import router as analysis_router
from app.asset_overview import AssetOverviewRead, AssetOverviewUpdate, OverviewScenarioExport
from app.asset_mediation import record_download, router as asset_mediation_router
from app.offer_documents import render_overview_scenario_draft
from app.auth import verify_token
from app.auth_routes import require_current_user, router as auth_router
from app.billing_routes import router as billing_router
from app.case_access import resolve_case_access
from app.case_lifecycle import lifecycle_write_allowed, router as case_lifecycle_router
from app.case_limits import require_active_case_slot
from app.config import get_settings
from app.database import SessionLocal, get_db
from app.demo import ensure_demo_user
from app.deletion import (
    PermanentDeletionConfirmation,
    delete_document_scope,
    router as deletion_router,
    scope_tombstone,
)
from app.documents import (
    DOCX_MEDIA_TYPE,
    PDF_MEDIA_TYPE,
    convert_docx_to_pdf,
    convert_pdf_to_docx,
    extract_document,
    render_template,
)
from app.extraction import MAX_EXTRACTION_RETRIES, retry_failed_extraction_job
from app.failure_logging import log_failure_event
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
    CaseMembership,
    DeletionTombstone,
    Document,
    DocumentExtraction,
    DocumentExtractionJob,
    NegotiationEvent,
    SettlementNegotiationAttempt,
    SettlementOfferResponse,
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
from app.settlement_routes import _require_real_case_exports, demo_export_router, router as settlement_router
from app.wizard_attempt import router as wizard_attempt_router
from app.wizard_intake import WizardIntakeDraft, router as wizard_intake_router
from app.services import (
    Artifact,
    get_case_or_none,
    get_document_or_none,
    store_artifacts,
)
from app.storage import ObjectStorage
from app.uat_fixtures import track_owner_beta_fixture_case
from app.validation import UploadValidationError, validate_upload

logger = logging.getLogger(__name__)
settings = get_settings()
storage = ObjectStorage(settings)


def _deployment_readiness_errors() -> tuple[str, ...]:
    errors: list[str] = []
    for enabled_attribute, check_attribute, unavailable_code in (
        (
            "production_readiness_required",
            "production_readiness_errors",
            "production_readiness_check_unavailable",
        ),
        (
            "owner_beta_readiness_required",
            "owner_beta_readiness_errors",
            "owner_beta_readiness_check_unavailable",
        ),
    ):
        if not getattr(settings, enabled_attribute, False):
            continue
        readiness_check = getattr(settings, check_attribute, None)
        if not callable(readiness_check):
            errors.append(unavailable_code)
        else:
            errors.extend(readiness_check())
    return tuple(errors)


def _deployment_readiness_detail() -> str:
    if (
        getattr(settings, "owner_beta_readiness_required", False)
        and not getattr(settings, "production_readiness_required", False)
    ):
        return "Owner-beta deployment readiness requirements are unmet."
    return "Production readiness requirements are unmet."


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
    if settings.case_data_enabled:
        from app.deletion_ledger import reconcile_from_environment

        reconcile_from_environment()
    yield


app = FastAPI(
    title="Washington Mediation Document Workflow",
    version="0.1.0",
    description="Local-development foundation for case and document workflows.",
    lifespan=lifespan,
)
app.include_router(auth_router)
app.include_router(deletion_router)
app.include_router(billing_router)
app.include_router(case_lifecycle_router)

app.include_router(export_integrations_router)
app.include_router(materials_router)
app.include_router(existing_offer_router)
app.include_router(offer_response_router)
app.include_router(analysis_router)
app.include_router(review_router)
app.include_router(settlement_router)
app.include_router(wizard_intake_router)
app.include_router(wizard_attempt_router)
app.include_router(demo_export_router)
app.include_router(asset_mediation_router)

DbSession: TypeAlias = Annotated[Session, Depends(get_db)]
LOGIN_PAGE = Path(__file__).parent / "static" / "index.html"

def is_working_page_path(path: str) -> bool:
    normalized = path.rstrip("/")
    return normalized in {"/settlement-completion", "/rejection-completion", "/case", "/onboarding"} or normalized.startswith(("/case/", "/onboarding/"))


@app.middleware("http")
async def authenticate_and_authorize_case_data(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    path = request.url.path
    if request.method in {"GET", "HEAD"} and is_working_page_path(path):
        try:
            with SessionLocal() as db:
                require_current_user(request, db)
        except HTTPException as error:
            if error.status_code == 401 or (
                error.status_code == 503 and error.detail == "Authentication is not configured."
            ):
                return RedirectResponse("/", status_code=303, headers={"Cache-Control": "no-store"})
            return JSONResponse(status_code=error.status_code, content={"detail": error.detail}, headers={"Cache-Control": "no-store"})
        except SQLAlchemyError as error:
            log_failure_event(logger, "working_page_session_check_failed", error)
            return JSONResponse(status_code=503, content={"detail": "Your session could not be verified. Please retry."}, headers={"Cache-Control": "no-store"})
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response
    is_case_data_path = (
        path == "/cases"
        or path.startswith("/cases/")
        or path == "/documents"
        or path.startswith("/documents/")
    )
    is_owner_beta_data_path = (
        getattr(settings, "owner_beta_readiness_required", False)
        and (
            path == "/api/v1/dashboard/status"
            or path.startswith("/api/billing/")
        )
    )
    if is_case_data_path or is_owner_beta_data_path:
        if _deployment_readiness_errors():
            return JSONResponse(
                status_code=503,
                content={"detail": _deployment_readiness_detail()},
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
                account_tombstone = db.scalar(
                    select(DeletionTombstone).where(
                        DeletionTombstone.scope_type == "account",
                        DeletionTombstone.scope_id == user_id,
                    )
                )
                if account_tombstone is not None:
                    return JSONResponse(
                        status_code=410,
                        content={"detail": "This account has been permanently deleted."},
                    )
                if path.startswith("/cases/"):
                    case_id = UUID(path.split("/")[2])
                elif path.startswith("/documents/"):
                    document_id = UUID(path.split("/")[2])
                    document_tombstone = scope_tombstone(db, "document", document_id)
                    if document_tombstone is not None:
                        return JSONResponse(
                            status_code=410,
                            content={"detail": "This material has been permanently deleted."},
                        )
                    document = db.get(Document, document_id)
                    if document is None:
                        return JSONResponse(status_code=404, content={"detail": "Document not found."})
                    case_id = document.case_id
                else:
                    case_id = None
                if case_id is not None:
                    case_tombstone = scope_tombstone(db, "case", case_id)
                    is_delete_retry = (
                        path == f"/cases/{case_id}/permanent-deletion"
                        and case_tombstone is not None
                        and case_tombstone.initiated_by == user_id
                    )
                    if case_tombstone is not None and not is_delete_retry:
                        return JSONResponse(
                            status_code=410,
                            content={"detail": "This case has been permanently deleted."},
                        )
                    if is_delete_retry and db.get(Case, case_id) is None:
                        db.commit()
                        return await call_next(request)
                    membership = resolve_case_access(db, case_id, user_id)
                    if membership is None:
                        return JSONResponse(status_code=404, content={"detail": "Case not found."})
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
            log_failure_event(logger, "case_authorization_lookup_failed", error)
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
        if "asset_overview" in value:
            raise ValueError("Use the asset-overview endpoint to record dated balances.")
        return value


class CaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    closed_at: datetime | None
    closed_reason: str | None
    attempts_locked_at: datetime | None
    metadata_json: dict
    asset_liability_inventory: dict
    relationship_milestones: dict
    property_assets: list[dict]


class WorkspaceDocumentRead(BaseModel):
    id: UUID
    extension: str
    size_bytes: int
    created_at: datetime
    original_filename: str | None = None


class WorkspaceAttemptRead(BaseModel):
    ordinal: int
    frozen: bool
    profile: dict | None


class CaseWorkspaceRead(BaseModel):
    case: CaseRead
    intake: WizardIntakeDraft
    attempts: list[WorkspaceAttemptRead]
    documents: list[WorkspaceDocumentRead]
    asset_overview: AssetOverviewRead
    accepted_offer_url: str | None = None


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
    workspace_started: bool


class DashboardData(BaseModel):
    has_cases: bool
    case_count: int
    active_case_count: int
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


@app.get("/api/v1/support/config", include_in_schema=False)
def support_configuration(response: Response) -> dict[str, str | None]:
    response.headers["Cache-Control"] = "no-store"
    return {"contact_url": settings.support_contact_url}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/pricing", response_class=HTMLResponse, include_in_schema=False)
def home() -> HTMLResponse:
    return HTMLResponse(LOGIN_PAGE.read_text(encoding="utf-8"))


@app.get("/terms", response_class=HTMLResponse, include_in_schema=False)
@app.get("/privacy", response_class=HTMLResponse, include_in_schema=False)
def account_notices() -> HTMLResponse:
    return HTMLResponse(
        LOGIN_PAGE.with_name("auth-notices.html").read_text(encoding="utf-8"),
        headers={"Cache-Control": "no-store"},
    )


@app.get("/demo", response_class=HTMLResponse, include_in_schema=False)
def demo_asset_overview(request: Request) -> Response:
    source = request.query_params.get("source", "demo2")
    case_id = request.query_params.get("demo_case_id")
    if source not in {"demo1", "demo2"}:
        raise HTTPException(status_code=400, detail="Invalid demo source.")
    if not case_id:
        return RedirectResponse(f"/demo/start?source={source}")
    return home()


@app.get("/demo/start", response_class=HTMLResponse, include_in_schema=False)
def demo_start_page(request: Request) -> Response:
    source = request.query_params.get("source", "demo1")
    if source not in {"demo1", "demo2"}:
        raise HTTPException(status_code=400, detail="Invalid demo source.")
    return home()


@app.get(
    "/demo/settlement-completion",
    response_class=HTMLResponse,
    include_in_schema=False,
)
@app.get(
    "/demo/rejection-completion",
    response_class=HTMLResponse,
    include_in_schema=False,
)
@app.get("/demo/documents", response_class=HTMLResponse, include_in_schema=False)
@app.get("/demo/wizard", response_class=HTMLResponse, include_in_schema=False)
@app.get("/demo/files", response_class=HTMLResponse, include_in_schema=False)
@app.get("/settlement-completion", response_class=HTMLResponse, include_in_schema=False)
@app.get("/rejection-completion", response_class=HTMLResponse, include_in_schema=False)
@app.get("/onboarding/upload", response_class=HTMLResponse, include_in_schema=False)
@app.get("/onboarding/wizard", response_class=HTMLResponse, include_in_schema=False)
@app.get("/case/assets", response_class=HTMLResponse, include_in_schema=False)
@app.get("/case/files", response_class=HTMLResponse, include_in_schema=False)
def onboarding_page() -> HTMLResponse:
    return home()


@app.get("/demo/1", include_in_schema=False)
@app.get("/demo/1/dashboard", include_in_schema=False)
def demo_one_entry() -> RedirectResponse:
    return RedirectResponse("/demo/start?source=demo1")


@app.get("/demo/2", include_in_schema=False)
@app.get("/demo/2/dashboard", include_in_schema=False)
@app.get("/demo/dashboard", include_in_schema=False)
def demo_two_entry() -> RedirectResponse:
    return RedirectResponse("/demo/start?source=demo2")


@app.get("/api/v1/dashboard/status", response_model=DashboardStatus)
def dashboard_status(
    user: Annotated[User, Depends(require_current_user)],
    response: Response,
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
                select(Document.id).where(
                    Document.case_id == Case.id,
                    ~select(DeletionTombstone.id).where(
                        DeletionTombstone.scope_type == "document",
                        DeletionTombstone.scope_id == Document.id,
                    ).exists(),
                ).exists(),
                func.count(SettlementNegotiationAttempt.id),
            )
            .join(CaseMembership, CaseMembership.case_id == Case.id)
            .outerjoin(
                SettlementNegotiationAttempt,
                SettlementNegotiationAttempt.case_id == Case.id,
            )
            .where(
                CaseMembership.user_id == user.id,
                CaseMembership.revoked_at.is_(None),
                ~select(DeletionTombstone.id)
                .where(
                    DeletionTombstone.scope_type == "case",
                    DeletionTombstone.scope_id == Case.id,
                )
                .exists(),
                Case.status != "finalized",
                Case.closed_at.is_(None),
            )
            .group_by(Case.id, CaseMembership.role)
            .order_by(Case.created_at.desc(), Case.id)
        ).all()
    except SQLAlchemyError as error:
        log_failure_event(logger, "dashboard_case_status_failed", error)
        raise HTTPException(
            status_code=503,
            detail="Dashboard status is unavailable. Please try again.",
        ) from error

    cases = []
    active_case_count = 0
    for case_id, case_status, metadata, attempt_ordinal, role, has_documents, attempt_count in rows:
        metadata = metadata if isinstance(metadata, dict) else {}
        case_title = metadata.get("case_title")
        if not isinstance(case_title, str) or not case_title.strip():
            case_title = "New case"
        workflow_mode = metadata.get("workflow_mode")
        asset_overview = metadata.get("asset_overview")
        overview = asset_overview.get("overview") if isinstance(asset_overview, dict) else None
        snapshots = overview.get("snapshots") if isinstance(overview, dict) else None
        cases.append(
            DashboardCaseStatus(
                id=case_id,
                status=case_status,
                title=case_title.strip(),
                workflow_mode=workflow_mode if workflow_mode in {"upload", "wizard"} else None,
                attempt_ordinal=attempt_ordinal,
                workspace_started=(
                    metadata.get("workspace_started") is True
                    or bool(has_documents)
                    or attempt_count > 0
                    or (isinstance(snapshots, list) and bool(snapshots))
                ),
            )
        )
        if role == "owner":
            active_case_count += 1
    response.headers["Cache-Control"] = "no-store"
    return DashboardStatus(
        data=DashboardData(
            has_cases=bool(cases),
            case_count=len(cases),
            active_case_count=active_case_count,
            cases=cases,
        )
    )


@app.get("/readyz")
def readiness() -> dict[str, str]:
    readiness_errors = _deployment_readiness_errors()
    if readiness_errors:
        logger.error(
            "Deployment readiness requirements are unmet (checks=%s).",
            ",".join(readiness_errors),
        )
        raise HTTPException(
            status_code=503,
            detail=_deployment_readiness_detail(),
        )
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        storage.check_ready()
    except SQLAlchemyError as error:
        log_failure_event(logger, "database_readiness_failed", error, severity="SEV1")
        raise HTTPException(status_code=503, detail="Database is unavailable.") from error
    except BotoCoreError as error:
        log_failure_event(logger, "object_storage_readiness_failed", error, severity="SEV1")
        raise HTTPException(status_code=503, detail="Object storage is unavailable.") from error
    except RuntimeError as error:
        logger.exception("Permanent-deletion ledger readiness check failed.")
        raise HTTPException(
            status_code=503,
            detail="Permanent-deletion protection is unavailable.",
        ) from error
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
    track_owner_beta_fixture_case(db, request.state.user_id, case, settings)
    db.commit()
    db.refresh(case)
    return case


@app.get("/cases/{case_id}", response_model=CaseRead)
def read_case(case_id: UUID, db: DbSession) -> Case:
    return _require_case(db, case_id)

@app.get("/cases/{case_id}/workspace", response_model=CaseWorkspaceRead)
def read_case_workspace(case_id: UUID, response: Response, db: DbSession) -> CaseWorkspaceRead:
    try:
        case = _require_case(db, case_id)
        attempts = db.scalars(
            select(SettlementNegotiationAttempt)
            .where(SettlementNegotiationAttempt.case_id == case_id)
            .order_by(SettlementNegotiationAttempt.attempt_ordinal)
        ).all()
        latest = attempts[-1] if attempts else None
        ordinal = latest.attempt_ordinal if latest is not None else 1
        mediation = (case.metadata_json or {}).get("asset_mediation", {}).get(str(ordinal), {})
        accepted_offer_url = None
        if case.closed_reason != "stopped" and not mediation.get("stopped"):
            if mediation.get("sent") and mediation.get("outcome") == "accepted":
                accepted_offer_url = f"/settlement-completion?case_id={case.id}&asset_attempt={ordinal}"
            elif latest is not None and latest.sent_confirmed_at is not None:
                outcome = db.scalar(
                    select(SettlementOfferResponse.outcome).where(
                        SettlementOfferResponse.case_id == case.id,
                        SettlementOfferResponse.selection_id == latest.selection_id,
                    )
                )
                if outcome == "accepted":
                    accepted_offer_url = f"/settlement-completion?case_id={case.id}&selection_id={latest.selection_id}"
        documents = db.scalars(
            select(Document)
            .where(
                Document.case_id == case_id,
                ~select(DeletionTombstone.id).where(
                    DeletionTombstone.scope_type == "document",
                    DeletionTombstone.scope_id == Document.id,
                ).exists(),
            )
            .order_by(Document.created_at, Document.id)
        ).all()
        response.headers["Cache-Control"] = "no-store"
        return CaseWorkspaceRead(
            case=CaseRead.model_validate(case),
            intake=WizardIntakeDraft.model_validate(case.wizard_intake_json or {}),
            asset_overview=AssetOverviewRead.model_validate(
                (case.metadata_json or {}).get("asset_overview", {})
            ),
            accepted_offer_url=accepted_offer_url,
            attempts=[
                WorkspaceAttemptRead(
                    ordinal=attempt.attempt_ordinal,
                    frozen=attempt.frozen_at is not None or attempt.finalized_at is not None,
                    profile=(
                        attempt.finalized_snapshot_json
                        or attempt.frozen_snapshot_json
                        or attempt.snapshot_json
                    ).get("case_profile"),
                )
                for attempt in attempts
            ],
            documents=[
                WorkspaceDocumentRead(
                    id=document.id,
                    extension=document.extension,
                    size_bytes=document.size_bytes,
                    created_at=document.created_at,
                    original_filename=document.original_filename,
                )
                for document in documents
            ],
        )
    except SQLAlchemyError as error:
        log_failure_event(logger, "case_workspace_lookup_failed", error)
        raise HTTPException(status_code=503, detail="Your saved case information is unavailable. Please retry.") from error


@app.put("/cases/{case_id}/asset-overview", response_model=AssetOverviewRead)
def save_case_asset_overview(
    case_id: UUID,
    payload: AssetOverviewUpdate,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: DbSession,
) -> AssetOverviewRead:
    try:
        case = db.scalar(select(Case).where(Case.id == case_id).with_for_update())
        membership = resolve_case_access(db, case_id, user.id)
        if case is None or membership is None:
            raise HTTPException(status_code=404, detail="Case not found.")
        if membership.role != "owner":
            raise HTTPException(status_code=403, detail="Only the case owner can edit asset values.")
        if case.closed_at is not None or case.status == "finalized":
            raise HTTPException(status_code=409, detail="This case is read-only.")
        latest = db.scalar(
            select(SettlementNegotiationAttempt)
            .where(SettlementNegotiationAttempt.case_id == case_id)
            .order_by(SettlementNegotiationAttempt.attempt_ordinal.desc()).limit(1)
        )
        if latest is not None and (latest.frozen_at is not None or latest.finalized_at is not None):
            raise HTTPException(status_code=409, detail="The latest attempt is read-only.")
        metadata = dict(case.metadata_json or {})
        current = AssetOverviewRead.model_validate(metadata.get("asset_overview", {}))
        if current.revision != payload.expected_revision:
            raise HTTPException(status_code=409, detail="Asset values changed. Reload before saving.")
        result = AssetOverviewRead(revision=current.revision + 1, overview=payload.overview)
        metadata["asset_overview"] = result.model_dump(mode="json")
        case.metadata_json = metadata
        db.commit()
        response.headers["Cache-Control"] = "no-store"
        return result
    except SQLAlchemyError as error:
        db.rollback()
        log_failure_event(logger, "asset_overview_save_failed", error)
        raise HTTPException(status_code=503, detail="Asset values were not saved. Please retry.") from error


@app.post("/cases/{case_id}/asset-overview/exports/{format}")
def download_asset_overview_scenario(
    case_id: UUID,
    format: Literal["docx", "xlsx"],
    payload: OverviewScenarioExport,
    user: Annotated[User, Depends(require_current_user)],
    db: DbSession,
) -> Response:
    try:
        _require_real_case_exports()
        case = db.scalar(select(Case).where(Case.id == case_id).with_for_update())
        if case is None:
            raise HTTPException(status_code=404, detail="Case not found.")
        membership = resolve_case_access(db, case_id, user.id)
        if membership is None:
            raise HTTPException(status_code=404, detail="Case not found.")
        if membership.role != "owner":
            raise HTTPException(status_code=403, detail="Only the owner can download case proposal drafts.")
        latest = db.scalar(
            select(SettlementNegotiationAttempt)
            .where(SettlementNegotiationAttempt.case_id == case_id)
            .order_by(SettlementNegotiationAttempt.attempt_ordinal.desc()).limit(1)
        )
        current_ordinal = latest.attempt_ordinal if latest is not None else 1
        if payload.attempt_ordinal > current_ordinal:
            raise HTTPException(status_code=409, detail="This attempt is not available.")
        attempt = latest if payload.attempt_ordinal == current_ordinal else db.scalar(
            select(SettlementNegotiationAttempt).where(
                SettlementNegotiationAttempt.case_id == case_id,
                SettlementNegotiationAttempt.attempt_ordinal == payload.attempt_ordinal,
            )
        )
        if payload.attempt_ordinal < current_ordinal and attempt is None:
            raise HTTPException(status_code=409, detail="The saved attempt is unavailable.")
        metadata = case.metadata_json or {}
        if attempt is not None and (
            payload.attempt_ordinal < current_ordinal
            or attempt.frozen_at is not None or attempt.finalized_at is not None
        ):
            snapshot = attempt.finalized_snapshot_json or attempt.frozen_snapshot_json or attempt.snapshot_json
            profile = snapshot.get("case_profile")
            if not isinstance(profile, dict) or not isinstance(profile.get("metadata"), dict):
                raise HTTPException(status_code=409, detail="The saved attempt profile is unavailable.")
            metadata = profile["metadata"]
        saved = AssetOverviewRead.model_validate(metadata.get("asset_overview", {}))
        if payload.expected_revision != saved.revision:
            raise HTTPException(status_code=409, detail="Asset values changed. Reload before downloading.")
        content = render_overview_scenario_draft(saved.overview, payload, format)
        if len(content) > get_settings().max_upload_bytes:
            raise HTTPException(status_code=413, detail="Generated draft exceeds the file size limit.")
        media_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if format == "docx"
            else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = "cr2a-proposal-draft.docx" if format == "docx" else "property-schedule-draft.xlsx"
        record_download(db, case, payload, format)
        return Response(content=content, media_type=media_type, headers={
            "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
            "Content-Disposition": f'attachment; filename="{filename}"',
        })
    except ValueError as error:
        log_failure_event(logger, "asset_scenario_export_invalid", error)
        raise HTTPException(status_code=422, detail=str(error)) from error
    except SQLAlchemyError as error:
        db.rollback()
        log_failure_event(logger, "asset_scenario_export_failed", error)
        raise HTTPException(status_code=503, detail="Draft download failed. Your work is unchanged; retry.") from error


class WorkspaceEntryRead(BaseModel):
    workspace_started: Literal[True] = True


@app.post("/cases/{case_id}/workspace-entry", response_model=WorkspaceEntryRead)
def record_workspace_entry(
    case_id: UUID,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: DbSession,
) -> WorkspaceEntryRead:
    try:
        case = db.scalar(select(Case).where(Case.id == case_id).with_for_update())
        membership = resolve_case_access(db, case_id, user.id)
        if case is None or membership is None:
            raise HTTPException(status_code=404, detail="Case not found.")
        if membership.role != "owner":
            raise HTTPException(status_code=403, detail="Only the case owner can continue onboarding.")
        if case.closed_at is not None or case.status == "finalized":
            raise HTTPException(status_code=409, detail="This case is closed or read-only.")
        metadata = dict(case.metadata_json or {})
        if metadata.get("onboarding_reset"):
            raise HTTPException(status_code=409, detail="Finish discarding onboarding before entering an attempt.")
        metadata["workspace_started"] = True
        case.metadata_json = metadata
        db.commit()
        response.headers["Cache-Control"] = "no-store"
        return WorkspaceEntryRead()
    except SQLAlchemyError as error:
        db.rollback()
        log_failure_event(logger, "case_workspace_entry_failed", error)
        raise HTTPException(status_code=503, detail="Case progress was not saved. Please retry.") from error


class WorkflowModeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_mode: Literal["upload", "wizard"]


class OnboardingStateRead(BaseModel):
    workflow_mode: Literal["upload", "wizard"] | None
    has_work: bool
    reset_pending: bool
    reset_target: Literal["upload", "wizard"] | None = None


@app.get("/cases/{case_id}/onboarding-state", response_model=OnboardingStateRead)
def read_onboarding_state(case_id: UUID, response: Response, db: DbSession) -> OnboardingStateRead:
    try:
        case = _require_case(db, case_id)
        metadata = case.metadata_json or {}
        mode = metadata.get("workflow_mode")
        has_documents = db.scalar(select(Document.id).where(Document.case_id == case_id).limit(1)) is not None
        intake = WizardIntakeDraft.model_validate(case.wizard_intake_json or {})
        offer = metadata.get(EXISTING_OFFER_METADATA_KEY)
        has_offer = isinstance(offer, dict) and bool(
            offer.get("exists") is True or offer.get("notes") or offer.get("document_ids")
        )
        response.headers["Cache-Control"] = "no-store"
        return OnboardingStateRead(
            workflow_mode=mode if mode in {"upload", "wizard"} else None,
            has_work=(
                has_documents or intake != WizardIntakeDraft()
                or has_offer
            ),
            reset_pending=bool(metadata.get("onboarding_reset")),
            reset_target=metadata.get("onboarding_reset"),
        )
    except SQLAlchemyError as error:
        log_failure_event(logger, "onboarding_state_failed", error)
        raise HTTPException(status_code=503, detail="Your saved work could not be checked. Please retry.") from error


class OnboardingResetRequest(WorkflowModeUpdate):
    confirmation: Literal["DISCARD ONBOARDING"]


@app.post("/cases/{case_id}/onboarding-reset", response_model=OnboardingStateRead)
def reset_onboarding(
    case_id: UUID,
    payload: OnboardingResetRequest,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: DbSession,
) -> OnboardingStateRead:
    try:
        case = db.scalar(select(Case).where(Case.id == case_id).with_for_update())
        membership = resolve_case_access(db, case_id, user.id)
        if case is None or membership is None:
            raise HTTPException(status_code=404, detail="Case not found.")
        if membership.role != "owner":
            raise HTTPException(status_code=403, detail="Only the case owner can discard onboarding.")
        if case.closed_at is not None or case.status == "finalized":
            raise HTTPException(status_code=409, detail="This case is closed or read-only.")
        if db.scalar(select(SettlementNegotiationAttempt.id).where(
            SettlementNegotiationAttempt.case_id == case_id,
        ).limit(1)) is not None or (case.metadata_json or {}).get("workspace_started") is True:
            raise HTTPException(status_code=409, detail="Onboarding cannot be discarded after entering an attempt.")
        metadata = dict(case.metadata_json or {})
        pending = metadata.get("onboarding_reset")
        if pending and pending != payload.workflow_mode:
            raise HTTPException(status_code=409, detail="Finish the pending mode change before choosing another mode.")
        metadata["onboarding_reset"] = payload.workflow_mode
        case.metadata_json = metadata
        db.commit()
        document_ids = list(db.scalars(select(Document.id).where(Document.case_id == case_id)))
        for document_id in document_ids:
            delete_document_scope(db, user, case_id, document_id, storage)
        case = db.scalar(select(Case).where(Case.id == case_id).with_for_update())
        metadata = dict(case.metadata_json or {})
        for key in [EXISTING_OFFER_METADATA_KEY, "asset_overview", "workspace_started", "onboarding_reset"]:
            metadata.pop(key, None)
        metadata["workflow_mode"] = payload.workflow_mode
        case.metadata_json = metadata
        case.wizard_intake_json = WizardIntakeDraft().model_dump(mode="json")
        case.wizard_intake_revision = (case.wizard_intake_revision or 0) + 1
        case.property_assets = []
        case.relationship_milestones = {}
        case.asset_liability_inventory = {}
        db.commit()
        response.headers["Cache-Control"] = "no-store"
        return OnboardingStateRead(workflow_mode=payload.workflow_mode, has_work=False, reset_pending=False)
    except SQLAlchemyError as error:
        db.rollback()
        log_failure_event(logger, "onboarding_reset_failed", error)
        raise HTTPException(status_code=503, detail="Discarding onboarding is incomplete. Please retry the same mode change.") from error


@app.put("/cases/{case_id}/workflow-mode", response_model=CaseRead)
def update_case_workflow_mode(
    case_id: UUID,
    payload: WorkflowModeUpdate,
    user: Annotated[User, Depends(require_current_user)],
    db: DbSession,
) -> Case:
    case = _require_case(db, case_id)
    membership = resolve_case_access(db, case_id, user.id)
    if membership is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    if membership.role != "owner":
        raise HTTPException(status_code=403, detail="Only the case owner can change how it starts.")
    try:
        metadata = dict(case.metadata_json or {})
        if metadata.get("onboarding_reset"):
            raise HTTPException(status_code=409, detail="Finish discarding onboarding before changing its start path.")
        metadata["workflow_mode"] = payload.workflow_mode
        case.metadata_json = metadata
        db.commit()
        db.refresh(case)
    except SQLAlchemyError as error:
        db.rollback()
        log_failure_event(logger, "case_workflow_mode_update_failed", error)
        raise HTTPException(
            status_code=503, detail="The start path could not be changed. Please try again."
        ) from error
    return case


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
        log_failure_event(logger, "case_property_update_failed", error)
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
        log_failure_event(logger, "extraction_status_lookup_failed", error)
        raise HTTPException(
            status_code=503,
            detail="Document processing status is unavailable. Please try again.",
        ) from error

    if job is not None:
        if job.status == "completed" and extraction is None:
            log_failure_event(logger, "extraction_result_missing", severity="SEV1")
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
        if retried.status == "failed":
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Extraction retry limit reached ({MAX_EXTRACTION_RETRIES} retries). "
                    "The original source remains stored; contact support for help."
                ),
            )
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
        log_failure_event(logger, "extraction_retry_persistence_failed", error)
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
        [Artifact(content, extension, media_type, original_filename=upload.filename)],
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
        log_failure_event(logger, "document_download_metadata_failed", error)
        raise HTTPException(
            status_code=503,
            detail="Document retrieval is unavailable. Please try again.",
        ) from error
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    try:
        content = storage.get(document.object_key)
    except BotoCoreError as error:
        log_failure_event(logger, "document_download_failed", error)
        raise HTTPException(
            status_code=503,
            detail="Document retrieval is unavailable. Please try again.",
        ) from error
    return Response(
        content=content,
        media_type=document.media_type,
        headers={"Content-Disposition": (
            f"attachment; filename*=UTF-8''{quote(document.original_filename, safe='')}"
            if document.original_filename else f'attachment; filename="{document.id}.{document.extension}"'
        )},
    )


@app.get("/documents/{document_id}/preview")
def preview_document(document_id: UUID, db: DbSession) -> Response:
    try:
        document = db.get(Document, document_id)
    except SQLAlchemyError as error:
        log_failure_event(logger, "document_preview_metadata_failed", error)
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
        log_failure_event(logger, "document_preview_failed", error)
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
def delete_document(
    document_id: UUID,
    payload: PermanentDeletionConfirmation,
    request: Request,
    db: DbSession,
) -> Response:
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if payload.confirmation != "DELETE MATERIAL":
        raise HTTPException(
            status_code=422,
            detail='Type "DELETE MATERIAL" to confirm material deletion.',
        )
    existing_tombstone = scope_tombstone(db, "document", document_id)
    if existing_tombstone is not None and existing_tombstone.initiated_by == user_id:
        if existing_tombstone.status == "completed":
            return Response(status_code=204, headers={"Cache-Control": "no-store"})
    try:
        document = get_document_or_none(db, document_id)
    except SQLAlchemyError as error:
        log_failure_event(logger, "document_deletion_metadata_failed", error)
        raise HTTPException(
            status_code=503,
            detail="Document deletion is unavailable. Please try again.",
        ) from error
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    delete_document_scope(db, user, document.case_id, document.id, storage)
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
