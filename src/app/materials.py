import hashlib
import logging
from uuid import UUID, uuid4

from botocore.exceptions import BotoCoreError
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth_routes import require_current_user
from app.config import get_settings
from app.database import get_db
from app.models import Case, CaseMembership, Document, MaterialImportBatch, MaterialImportItem, User
from app.storage import ObjectStorage
from app.validation import UploadValidationError, validate_upload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/materials", tags=["materials"])
storage = ObjectStorage()


class ProviderAvailability(BaseModel):
    google_drive: bool
    dropbox: bool


class MaterialsConfig(BaseModel):
    max_upload_bytes: int
    supported_extensions: list[str]
    import_enabled: bool
    providers: ProviderAvailability


class ImportedDocument(BaseModel):
    id: UUID
    extension: str
    media_type: str
    size_bytes: int


class ImportedFile(BaseModel):
    status: str = "success"
    item_id: UUID
    case_id: UUID
    document: ImportedDocument


class ImportBatchStatus(BaseModel):
    batch_id: UUID
    case_id: UUID
    items: list[ImportedFile]


def _require_import_enabled() -> None:
    config = get_settings()
    if not config.auth_enabled or not config.case_data_enabled or config.demo_mode_enabled:
        raise HTTPException(
            status_code=503,
            detail="Case-material imports are unavailable until case-data access is enabled.",
        )


def _document_response(item_id: UUID, case_id: UUID, document: Document) -> ImportedFile:
    return ImportedFile(
        item_id=item_id,
        case_id=case_id,
        document=ImportedDocument(
            id=document.id,
            extension=document.extension,
            media_type=document.media_type,
            size_bytes=document.size_bytes,
        ),
    )


def _existing_item(
    db: Session,
    batch_id: UUID,
    item_id: UUID,
) -> tuple[MaterialImportBatch, Document | None] | None:
    batch = db.get(MaterialImportBatch, batch_id)
    if batch is None:
        return None
    item = db.scalar(
        select(MaterialImportItem).where(
            MaterialImportItem.batch_id == batch_id,
            MaterialImportItem.item_id == item_id,
        )
    )
    if item is None:
        return batch, None
    document = db.get(Document, item.document_id)
    if document is None:
        logger.error("Material import item references a missing document: %s", item.id)
        raise HTTPException(status_code=503, detail="Import status is unavailable. Please try again.")
    return batch, document


def _delete_uploaded_object(key: str | None) -> None:
    if key is None:
        return
    try:
        storage.delete(key)
    except BotoCoreError:
        logger.exception("Could not clean up an object after a failed material import: %s", key)


@router.get("/config", response_model=MaterialsConfig)
def materials_config(_: User = Depends(require_current_user)) -> MaterialsConfig:
    config = get_settings()
    return MaterialsConfig(
        max_upload_bytes=config.max_upload_bytes,
        supported_extensions=["pdf", "docx"],
        import_enabled=(
            config.auth_enabled and config.case_data_enabled and not config.demo_mode_enabled
        ),
        providers=ProviderAvailability(google_drive=False, dropbox=False),
    )


@router.post(
    "/imports/{batch_id}/files/{item_id}",
    response_model=ImportedFile,
    status_code=201,
)
async def import_material_file(
    batch_id: UUID,
    item_id: UUID,
    upload: UploadFile = File(),
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> ImportedFile:
    config = get_settings()
    filename = upload.filename or ""
    extension = filename.rpartition(".")[2].lower()
    try:
        _require_import_enabled()
        if extension not in {"pdf", "docx"}:
            raise HTTPException(status_code=415, detail="Only PDF and DOCX files are supported.")
        content = await upload.read(config.max_upload_bytes + 1)
        validate_upload(filename, content, extension, config.max_upload_bytes)
    except UploadValidationError as error:
        status_code = 413 if len(content) > config.max_upload_bytes else 415
        raise HTTPException(status_code=status_code, detail=str(error)) from error
    finally:
        await upload.close()

    try:
        existing = _existing_item(db, batch_id, item_id)
    except SQLAlchemyError as error:
        logger.exception("Material import status lookup failed.")
        raise HTTPException(
            status_code=503,
            detail="Import status is unavailable. Please try again.",
        ) from error
    if existing is not None:
        batch, document = existing
        if batch.user_id != user.id:
            raise HTTPException(status_code=404, detail="Import batch not found.")
        try:
            membership = db.scalar(
                select(CaseMembership).where(
                    CaseMembership.case_id == batch.case_id,
                    CaseMembership.user_id == user.id,
                    CaseMembership.revoked_at.is_(None),
                )
            )
        except SQLAlchemyError as error:
            logger.exception("Material import membership lookup failed.")
            raise HTTPException(
                status_code=503,
                detail="Import authorization is unavailable. Please try again.",
            ) from error
        if membership is None:
            raise HTTPException(status_code=404, detail="Import batch not found.")
        if document is not None:
            return _document_response(item_id, batch.case_id, document)
        case_id = batch.case_id
    else:
        case_id = uuid4()
        case = Case(id=case_id, status="draft")
        new_batch = MaterialImportBatch(id=batch_id, user_id=user.id, case_id=case_id)
        db.add_all(
            [
                case,
                CaseMembership(case_id=case_id, user_id=user.id, role="owner"),
                new_batch,
            ]
        )

    document_id = uuid4()
    object_key = f"{case_id}/{document_id}.{extension}"
    media_type = (
        "application/pdf"
        if extension == "pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
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
    db.add(MaterialImportItem(batch_id=batch_id, item_id=item_id, document_id=document_id))

    upload_attempted = False
    try:
        upload_attempted = True
        storage.put(object_key, content, media_type)
        db.commit()
    except BotoCoreError as error:
        db.rollback()
        _delete_uploaded_object(object_key if upload_attempted else None)
        logger.exception("Material object storage failed.")
        raise HTTPException(
            status_code=503,
            detail="This file could not be stored. Please retry it.",
        ) from error
    except SQLAlchemyError as error:
        db.rollback()
        _delete_uploaded_object(object_key if upload_attempted else None)
        if isinstance(error, IntegrityError):
            recovered = _existing_item(db, batch_id, item_id)
            if recovered is not None:
                recovered_batch, recovered_document = recovered
                if recovered_batch.user_id != user.id:
                    raise HTTPException(status_code=404, detail="Import batch not found.") from error
                if recovered_document is not None:
                    membership = db.scalar(
                        select(CaseMembership).where(
                            CaseMembership.case_id == recovered_batch.case_id,
                            CaseMembership.user_id == user.id,
                            CaseMembership.revoked_at.is_(None),
                        )
                    )
                    if membership is None:
                        raise HTTPException(
                            status_code=404, detail="Import batch not found."
                        ) from error
                    return _document_response(item_id, recovered_batch.case_id, recovered_document)
                raise HTTPException(
                    status_code=409,
                    detail="Another file in this import is being saved. Please retry.",
                ) from error
        logger.exception("Material import database transaction failed.")
        raise HTTPException(
            status_code=503,
            detail="This file could not be recorded. Please retry it.",
        ) from error

    return _document_response(item_id, case_id, document)


@router.get("/imports/{batch_id}", response_model=ImportBatchStatus)
def import_batch_status(
    batch_id: UUID,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> ImportBatchStatus:
    _require_import_enabled()
    try:
        batch = db.get(MaterialImportBatch, batch_id)
        if batch is None or batch.user_id != user.id:
            raise HTTPException(status_code=404, detail="Import batch not found.")
        membership = db.scalar(
            select(CaseMembership).where(
                CaseMembership.case_id == batch.case_id,
                CaseMembership.user_id == user.id,
                CaseMembership.revoked_at.is_(None),
            )
        )
        if membership is None:
            raise HTTPException(status_code=404, detail="Import batch not found.")
        rows = db.execute(
            select(MaterialImportItem.item_id, Document)
            .join(Document, Document.id == MaterialImportItem.document_id)
            .where(MaterialImportItem.batch_id == batch.id)
            .order_by(MaterialImportItem.id)
        ).all()
    except SQLAlchemyError as error:
        logger.exception("Material import status retrieval failed.")
        raise HTTPException(
            status_code=503,
            detail="Import status is unavailable. Please try again.",
        ) from error
    return ImportBatchStatus(
        batch_id=batch.id,
        case_id=batch.case_id,
        items=[
            _document_response(item_id, batch.case_id, document)
            for item_id, document in rows
        ],
    )
