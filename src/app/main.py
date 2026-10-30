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
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

from app.auth import verify_token
from app.auth_routes import require_current_user, router as auth_router
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
from app.models import (
    AuthSession,
    Case,
    CaseMembership,
    Document,
    NegotiationEvent,
    User,
)
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
                    membership = db.scalar(
                        select(CaseMembership).where(
                            CaseMembership.case_id == case_id,
                            CaseMembership.user_id == user_id,
                            CaseMembership.revoked_at.is_(None),
                        )
                    )
                    if membership is None:
                        return JSONResponse(status_code=404, content={"detail": "Case not found."})
                    if request.method != "GET" and membership.role == "viewer":
                        return JSONResponse(status_code=403, content={"detail": "Case is read-only."})
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
    asset_liability_inventory: dict = Field(default_factory=dict)


class CaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    metadata_json: dict
    asset_liability_inventory: dict


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


class RenderResponse(BaseModel):
    docx: DocumentRead
    pdf: DocumentRead


class ConversionResponse(BaseModel):
    document: DocumentRead
    extraction: ExtractionRead


class DashboardCaseStatus(BaseModel):
    id: UUID
    status: str


class DashboardData(BaseModel):
    has_cases: bool
    case_count: int
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


@app.get("/onboarding/upload", response_class=HTMLResponse, include_in_schema=False)
@app.get("/onboarding/wizard", response_class=HTMLResponse, include_in_schema=False)
def onboarding_page() -> HTMLResponse:
    return home()


@app.get("/api/v1/dashboard/status", response_model=DashboardStatus)
def dashboard_status(
    user: Annotated[User, Depends(require_current_user)],
    db: DbSession,
) -> DashboardStatus:
    try:
        rows = db.execute(
            select(Case.id, Case.status)
            .join(CaseMembership, CaseMembership.case_id == Case.id)
            .where(
                CaseMembership.user_id == user.id,
                CaseMembership.revoked_at.is_(None),
            )
            .order_by(Case.created_at.desc(), Case.id)
        ).all()
    except SQLAlchemyError as error:
        logger.exception("Dashboard case-status lookup failed.")
        raise HTTPException(
            status_code=503,
            detail="Dashboard status is unavailable. Please try again.",
        ) from error

    cases = [DashboardCaseStatus(id=case_id, status=case_status) for case_id, case_status in rows]
    return DashboardStatus(
        data=DashboardData(
            has_cases=bool(cases),
            case_count=len(cases),
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
    case = Case(
        status=payload.status,
        metadata_json=payload.metadata,
        asset_liability_inventory=payload.asset_liability_inventory,
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
    document = get_document_or_none(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    content = storage.get(document.object_key)
    return Response(
        content=content,
        media_type=document.media_type,
        headers={"Content-Disposition": f'attachment; filename="{document.id}.{document.extension}"'},
    )
