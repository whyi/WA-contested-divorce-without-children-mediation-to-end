import hashlib
import logging
from pathlib import PurePath
from typing import Literal
from uuid import UUID, uuid4

from botocore.exceptions import BotoCoreError
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth_routes import require_current_user
from app.config import get_settings
from app.database import get_db
from app.models import (
    Case,
    Document,
    SettlementOfferResponse,
    SettlementOfferResponseAttachment,
    SettlementScenarioSelection,
    User,
)
from app.settlement_routes import _authorize_case
from app.storage import ObjectStorage
from app.validation import UploadValidationError, validate_upload

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/cases/{case_id}/settlement-planning/selections/{selection_id}/offer-response",
    tags=["settlement offer response"],
)
storage = ObjectStorage()

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PDF_MEDIA_TYPE = "application/pdf"
ATTACHMENT_TYPES = {
    "sent_docx": {"docx"},
    "sent_xlsx": {"xlsx"},
    "counteroffer": {"docx", "xlsx", "pdf"},
    "accepted_offer": {"docx", "xlsx", "pdf"},
}


class OfferResponseAttachmentRead(BaseModel):
    kind: Literal["sent_docx", "sent_xlsx", "counteroffer", "accepted_offer"]
    filename: str
    extension: Literal["docx", "xlsx", "pdf"]
    size_bytes: int


class OfferResponseRead(BaseModel):
    selection_id: UUID
    outcome: Literal["counteroffer", "rejected", "accepted"] | None
    attachments: list[OfferResponseAttachmentRead]
    sent_documents_complete: bool
    counteroffer_attachment_present: bool


class OfferOutcomeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: Literal["counteroffer", "rejected", "accepted"]


def _require_secure_case_storage() -> None:
    config = get_settings()
    if (
        not config.auth_enabled
        or not config.case_data_enabled
        or not config.case_materials_enabled
        or config.demo_mode_enabled
    ):
        raise HTTPException(
            status_code=503,
            detail="Secure case-material storage is unavailable.",
        )


def _selection(
    db: Session,
    case_id: UUID,
    selection_id: UUID,
) -> SettlementScenarioSelection:
    selection = db.scalar(
        select(SettlementScenarioSelection).where(
            SettlementScenarioSelection.id == selection_id,
            SettlementScenarioSelection.case_id == case_id,
        )
    )
    if selection is None:
        raise HTTPException(status_code=404, detail="Settlement selection not found.")
    return selection


def _response_record(
    db: Session,
    selection: SettlementScenarioSelection,
) -> SettlementOfferResponse | None:
    return db.scalar(
        select(SettlementOfferResponse).where(
            SettlementOfferResponse.selection_id == selection.id,
            SettlementOfferResponse.case_id == selection.case_id,
        )
    )


def _read_response(
    db: Session,
    selection: SettlementScenarioSelection,
    response_record: SettlementOfferResponse | None,
) -> OfferResponseRead:
    attachments = []
    if response_record is not None:
        rows = db.execute(
            select(SettlementOfferResponseAttachment, Document)
            .join(Document, Document.id == SettlementOfferResponseAttachment.document_id)
            .where(
                SettlementOfferResponseAttachment.response_id == response_record.id,
                Document.case_id == selection.case_id,
            )
            .order_by(SettlementOfferResponseAttachment.created_at, SettlementOfferResponseAttachment.id)
        ).all()
        attachments = [
            {
                "kind": item.kind,
                "filename": item.filename,
                "extension": document.extension,
                "size_bytes": document.size_bytes,
            }
            for item, document in rows
        ]
    kinds = {item["kind"] for item in attachments}
    return OfferResponseRead(
        selection_id=selection.id,
        outcome=response_record.outcome if response_record is not None else None,
        attachments=attachments,
        sent_documents_complete={"sent_docx", "sent_xlsx"}.issubset(kinds),
        counteroffer_attachment_present="counteroffer" in kinds,
    )


def _authorized_selection(
    case_id: UUID,
    selection_id: UUID,
    user: User,
    db: Session,
    *,
    write: bool,
) -> tuple[Case, SettlementScenarioSelection]:
    case = _authorize_case(db, user, case_id, write=write)
    return case, _selection(db, case_id, selection_id)


@router.get("", response_model=OfferResponseRead)
def read_offer_response(
    case_id: UUID,
    selection_id: UUID,
    response: Response,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> OfferResponseRead:
    _, selection = _authorized_selection(case_id, selection_id, user, db, write=False)
    response.headers["Cache-Control"] = "no-store"
    return _read_response(db, selection, _response_record(db, selection))


@router.post("/attachments/{kind}", response_model=OfferResponseRead, status_code=201)
async def upload_offer_response_attachment(
    case_id: UUID,
    selection_id: UUID,
    kind: str,
    response: Response,
    upload: UploadFile = File(),
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> OfferResponseRead:
    _require_secure_case_storage()
    _authorized_selection(case_id, selection_id, user, db, write=True)
    allowed_extensions = ATTACHMENT_TYPES.get(kind)
    if allowed_extensions is None:
        await upload.close()
        raise HTTPException(status_code=422, detail="Unsupported response attachment type.")

    filename = PurePath((upload.filename or "").replace("\\", "/")).name
    extension = filename.rpartition(".")[2].lower()
    if (
        not filename
        or len(filename) > 255
        or any(ord(char) < 32 or ord(char) == 127 for char in filename)
        or extension not in allowed_extensions
    ):
        await upload.close()
        accepted = ", ".join(f".{item}" for item in sorted(allowed_extensions))
        raise HTTPException(status_code=415, detail=f"Choose a supported file ({accepted}).")

    config = get_settings()
    try:
        content = await upload.read(config.max_upload_bytes + 1)
        validate_upload(filename, content, extension, config.max_upload_bytes)
    except UploadValidationError as error:
        status_code = 413 if len(content) > config.max_upload_bytes else 415
        raise HTTPException(status_code=status_code, detail=str(error)) from error
    finally:
        await upload.close()

    _, selection = _authorized_selection(case_id, selection_id, user, db, write=True)
    response_record = _response_record(db, selection)
    if response_record is None:
        response_record = SettlementOfferResponse(
            case_id=case_id,
            selection_id=selection_id,
            user_id=user.id,
            user_id_snapshot=user.id,
        )
        db.add(response_record)
        db.flush()

    media_type = {
        "docx": DOCX_MEDIA_TYPE,
        "xlsx": XLSX_MEDIA_TYPE,
        "pdf": PDF_MEDIA_TYPE,
    }[extension]
    document_id = uuid4()
    object_key = f"{case_id}/offer-responses/{document_id}.{extension}"
    document = Document(
        id=document_id,
        case_id=case_id,
        object_key=object_key,
        extension=extension,
        media_type=media_type,
        sha256=hashlib.sha256(content).hexdigest(),
        size_bytes=len(content),
    )
    db.add(document)

    old_objects: list[str] = []
    if kind in {"sent_docx", "sent_xlsx"}:
        existing_rows = db.scalars(
            select(SettlementOfferResponseAttachment).where(
                SettlementOfferResponseAttachment.response_id == response_record.id,
                SettlementOfferResponseAttachment.kind == kind,
            )
        ).all()
        for item in existing_rows:
            old_document = db.get(Document, item.document_id)
            if old_document is not None and old_document.case_id == case_id:
                old_objects.append(old_document.object_key)
                db.delete(old_document)
            db.delete(item)
    db.add(
        SettlementOfferResponseAttachment(
            response_id=response_record.id,
            document_id=document.id,
            kind=kind,
            filename=filename,
        )
    )

    try:
        storage.put(object_key, content, media_type)
        db.commit()
        db.refresh(response_record)
    except (BotoCoreError, RuntimeError) as error:
        db.rollback()
        try:
            storage.delete(object_key)
        except BotoCoreError:
            logger.error("Could not clean up a failed offer-response upload.")
        logger.error("Offer-response object storage failed (%s).", type(error).__name__)
        raise HTTPException(status_code=503, detail="This file could not be stored. Please retry it.") from error
    except SQLAlchemyError as error:
        db.rollback()
        try:
            storage.delete(object_key)
        except BotoCoreError:
            logger.error("Could not clean up a failed offer-response upload.")
        logger.error("Offer-response database write failed (%s).", type(error).__name__)
        raise HTTPException(status_code=503, detail="This file could not be stored. Please retry it.") from error

    for old_object in old_objects:
        try:
            storage.delete(old_object)
        except BotoCoreError:
            logger.error("Could not remove a replaced offer-response file from storage.")
    response.headers["Cache-Control"] = "no-store"
    return _read_response(db, selection, response_record)


@router.put("", response_model=OfferResponseRead)
def update_offer_response(
    case_id: UUID,
    selection_id: UUID,
    payload: OfferOutcomeUpdate,
    response: Response,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> OfferResponseRead:
    _, selection = _authorized_selection(case_id, selection_id, user, db, write=True)
    response_record = _response_record(db, selection)
    current = _read_response(db, selection, response_record)
    if not current.sent_documents_complete:
        raise HTTPException(status_code=409, detail="Attach the final sent DOCX and XLSX before choosing an outcome.")
    if response_record is None:
        raise HTTPException(status_code=409, detail="Offer response record is unavailable.")
    response_record.outcome = payload.outcome
    try:
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        logger.error("Offer-response outcome write failed (%s).", type(error).__name__)
        raise HTTPException(status_code=503, detail="The response could not be saved.") from error
    response.headers["Cache-Control"] = "no-store"
    return _read_response(db, selection, response_record)


@router.post("/continue")
def continue_offer_response(
    case_id: UUID,
    selection_id: UUID,
    response: Response,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    _, selection = _authorized_selection(case_id, selection_id, user, db, write=False)
    current = _read_response(db, selection, _response_record(db, selection))
    if not current.sent_documents_complete:
        raise HTTPException(status_code=409, detail="Attach the final sent DOCX and XLSX before continuing.")
    if current.outcome is None:
        raise HTTPException(status_code=409, detail="Choose a response outcome before continuing.")
    if current.outcome == "counteroffer" and not current.counteroffer_attachment_present:
        raise HTTPException(status_code=409, detail="Attach the received counteroffer before continuing.")
    response.headers["Cache-Control"] = "no-store"
    return {
        "next_step": "final_checklist" if current.outcome == "accepted" else "future_placeholder",
    }
