import json
import logging
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

from botocore.exceptions import BotoCoreError
from fastapi import Depends, FastAPI, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

from app.config import get_settings
from app.database import SessionLocal, get_db
from app.documents import (
    DOCX_MEDIA_TYPE,
    PDF_MEDIA_TYPE,
    convert_docx_to_pdf,
    convert_pdf_to_docx,
    extract_document,
    render_template,
)
from app.models import Case, NegotiationEvent
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

app = FastAPI(
    title="Washington Mediation Document Workflow",
    version="0.1.0",
    description="Local-development foundation for case and document workflows.",
)

DbSession = Annotated[Session, Depends(get_db)]
LOGIN_PAGE = Path(__file__).parent / "static" / "index.html"


@app.middleware("http")
async def disable_case_data_until_authentication(
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
        return JSONResponse(
            status_code=503,
            content={"detail": "Authentication is not configured. Case data APIs are unavailable."},
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
def create_case(payload: CaseCreate, db: DbSession) -> Case:
    case = Case(
        status=payload.status,
        metadata_json=payload.metadata,
        asset_liability_inventory=payload.asset_liability_inventory,
    )
    db.add(case)
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
