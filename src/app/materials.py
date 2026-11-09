import hashlib
import logging
from typing import Annotated
from uuid import UUID, uuid4

from botocore.exceptions import BotoCoreError
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.attachment_limits import (
    FREE_ATTACHMENT_LIMIT,
    attachment_usage,
    enforce_attachment_quota,
)
from app.auth_routes import require_current_user
from app.case_limits import require_active_case_slot
from app.config import get_settings
from app.database import get_db
from app.deletion import (
    delete_document_scope,
    import_item_tombstone_id,
    require_scope_active,
    scope_tombstone,
)
from app.failure_logging import log_failure_event
from app.models import (
    Case,
    CaseMembership,
    DeletionTombstone,
    Document,
    MaterialImportBatch,
    MaterialImportItem,
    User,
)
from app.storage import ObjectStorage
from app.uat_fixtures import track_owner_beta_fixture_case
from app.validation import UploadValidationError, validate_upload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/materials", tags=["materials"])
storage = ObjectStorage()


class ProviderAvailability(BaseModel):
    google_drive: bool
    dropbox: bool


class MaterialsConfig(BaseModel):
    max_upload_bytes: int
    max_attachments: int
    attachment_count: int
    supported_extensions: list[str]
    max_pdf_pages: int
    ocr_supported: bool
    import_enabled: bool
    providers: ProviderAvailability


class ImportedDocument(BaseModel):
    id: UUID
    extension: str
    media_type: str
    size_bytes: int
    original_filename: str | None = None
    overwrite_pending: bool = False


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
    if (
        not config.auth_enabled
        or not config.case_data_enabled
        or not config.case_materials_enabled
        or config.demo_mode_enabled
    ):
        raise HTTPException(
            status_code=503,
            detail="Case-material imports are unavailable until secure material storage is enabled.",
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
            original_filename=document.original_filename,
            overwrite_pending=document.overwrite_document_id is not None,
        ),
    )

def _finish_overwrite(db: Session, user: User, document: Document) -> None:
    target = document.overwrite_document_id
    if target is None:
        return
    delete_document_scope(db, user, document.case_id, target, storage)
    try:
        case = db.get(Case, document.case_id, with_for_update=True)
        if case is None:
            raise HTTPException(status_code=404, detail="Case not found.")
        metadata = dict(case.metadata_json or {})
        offer = metadata.get("existing_offer")
        if isinstance(offer, dict) and str(target) in offer.get("document_ids", []):
            metadata["existing_offer"] = {
                **offer, "document_ids": list(dict.fromkeys(
                    str(document.id) if item == str(target) else item
                    for item in offer["document_ids"]
                )),
            }
            case.metadata_json = metadata
        mediation = metadata.get("asset_mediation")
        if isinstance(mediation, dict):
            updated = {}
            for ordinal, state in mediation.items():
                record = dict(state)
                for key in ("document_ids", "accepted_document_ids"):
                    record[key] = list(dict.fromkeys(
                        str(document.id) if item == str(target) else item
                        for item in record.get(key, [])
                    ))
                updated[ordinal] = record
            metadata["asset_mediation"] = updated
            case.metadata_json = metadata
        document.overwrite_document_id = None
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        log_failure_event(logger, "upload_overwrite_completion_failed", error)
        raise HTTPException(status_code=503, detail="Overwrite cleanup is incomplete. Retry the same upload.") from error


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
        log_failure_event(logger, "upload_document_missing", severity="SEV1")
        raise HTTPException(status_code=503, detail="Import status is unavailable. Please try again.")
    return batch, document


def _validate_retry_file(document: Document, filename: str, content: bytes) -> None:
    if hashlib.sha256(content).hexdigest() != document.sha256 or (
        document.original_filename is not None and filename != document.original_filename
    ):
        raise HTTPException(
            status_code=409,
            detail="This import item was already used for different file contents or filename. Reselect the original file or start a new selection.",
        )


def _delete_uploaded_object(key: str | None) -> None:
    if key is None:
        return
    try:
        storage.delete_all_versions(key)
    except Exception as error:
        log_failure_event(logger, "upload_object_cleanup_failed", error, severity="SEV1")


@router.get("/config", response_model=MaterialsConfig)
def materials_config(
    case_id: UUID | None = None,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> MaterialsConfig:
    config = get_settings()
    stored, limit = 0, FREE_ATTACHMENT_LIMIT
    if case_id is not None:
        try:
            membership = db.scalar(
                select(CaseMembership).where(
                    CaseMembership.case_id == case_id,
                    CaseMembership.user_id == user.id,
                    CaseMembership.revoked_at.is_(None),
                    CaseMembership.suspended_at.is_(None),
                )
            )
        except SQLAlchemyError as error:
            log_failure_event(logger, "upload_authorization_lookup_failed", error)
            raise HTTPException(
                status_code=503,
                detail="Case access could not be verified. Please try again.",
            ) from error
        if membership is None:
            raise HTTPException(status_code=404, detail="Case not found.")
        stored, limit = attachment_usage(db, case_id)
    return MaterialsConfig(
        max_upload_bytes=config.max_upload_bytes,
        max_attachments=limit,
        attachment_count=stored,
        supported_extensions=["pdf", "docx"],
        max_pdf_pages=config.max_pdf_pages,
        ocr_supported=False,
        import_enabled=(
            config.auth_enabled
            and config.case_data_enabled
            and config.case_materials_enabled
            and not config.demo_mode_enabled
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
    case_id: UUID | None = Form(default=None),
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
    overwrite_document_id: Annotated[UUID | None, Form()] = None,
) -> ImportedFile:
    config = get_settings()
    filename = upload.filename or ""
    extension = filename.rpartition(".")[2].lower()
    try:
        _require_import_enabled()
        if not filename or len(filename) > 1024 or any(ord(char) < 32 for char in filename):
            raise HTTPException(status_code=422, detail="The filename is missing, too long or contains control characters.")
        if extension not in {"pdf", "docx"}:
            raise HTTPException(status_code=415, detail="Only PDF and DOCX files are supported.")
        content = await upload.read(config.max_upload_bytes + 1)
        validate_upload(filename, content, extension, config.max_upload_bytes)
    except UploadValidationError as error:
        status_code = 413 if len(content) > config.max_upload_bytes else 415
        raise HTTPException(status_code=status_code, detail=str(error)) from error
    finally:
        await upload.close()

    if scope_tombstone(
        db, "import_item", import_item_tombstone_id(batch_id, item_id)
    ) is not None:
        raise HTTPException(
            status_code=410,
            detail="This material import was permanently deleted and cannot be retried.",
        )

    try:
        existing = _existing_item(db, batch_id, item_id)
    except SQLAlchemyError as error:
        log_failure_event(logger, "upload_reconciliation_failed", error)
        raise HTTPException(
            status_code=503,
            detail="Import status is unavailable. Please try again.",
        ) from error
    if existing is not None:
        batch, document = existing
        if batch.user_id != user.id:
            raise HTTPException(status_code=404, detail="Import batch not found.")
        if case_id is not None and case_id != batch.case_id:
            raise HTTPException(status_code=409, detail="Import batch belongs to another case.")
        try:
            membership = db.scalar(
                select(CaseMembership).where(
                    CaseMembership.case_id == batch.case_id,
                    CaseMembership.user_id == user.id,
                    CaseMembership.revoked_at.is_(None),
                    CaseMembership.suspended_at.is_(None),
                )
            )
        except SQLAlchemyError as error:
            log_failure_event(logger, "upload_authorization_lookup_failed", error)
            raise HTTPException(
                status_code=503,
                detail="Import authorization is unavailable. Please try again.",
            ) from error
        if membership is None:
            raise HTTPException(status_code=404, detail="Import batch not found.")
        case = db.get(Case, batch.case_id, with_for_update=True)
        if case is None:
            raise HTTPException(status_code=404, detail="Case not found.")
        require_scope_active(db, "case", batch.case_id)
        if document is not None:
            _validate_retry_file(document, filename, content)
            _finish_overwrite(db, user, document)
            return _document_response(item_id, batch.case_id, document)
        case_id = batch.case_id
        new_case = False
    else:
        new_case = case_id is None
        if case_id is None:
            require_scope_active(db, "account", user.id)
            require_active_case_slot(db, user.id)
            case = Case(id=uuid4(), status="draft")
            db.add(case)
            db.flush()
            case_id = case.id
            db.add(CaseMembership(case_id=case_id, user_id=user.id, role="owner"))
            track_owner_beta_fixture_case(db, user.id, case)
        else:
            try:
                membership = db.scalar(
                    select(CaseMembership).where(
                        CaseMembership.case_id == case_id,
                        CaseMembership.user_id == user.id,
                        CaseMembership.revoked_at.is_(None),
                        CaseMembership.suspended_at.is_(None),
                    )
                )
                case = db.get(Case, case_id, with_for_update=True)
            except SQLAlchemyError as error:
                log_failure_event(logger, "upload_authorization_lookup_failed", error)
                raise HTTPException(
                    status_code=503,
                    detail="Case access could not be verified. Please try again.",
                ) from error
            if membership is None:
                raise HTTPException(status_code=404, detail="Case not found.")
            require_scope_active(db, "case", case_id)
            if membership.role == "viewer":
                raise HTTPException(status_code=403, detail="Case is read-only.")
            if case is None:
                raise HTTPException(status_code=404, detail="Case not found.")
            require_scope_active(db, "case", case_id)
        new_batch = MaterialImportBatch(id=batch_id, user_id=user.id, case_id=case_id)
        db.add_all(
            [
                new_batch,
            ]
        )

    duplicate = db.scalars(select(Document).where(
        Document.case_id == case_id, Document.original_filename == filename,
    ).order_by(Document.overwrite_document_id.is_(None), Document.created_at, Document.id).limit(1)).first()
    if duplicate is not None:
        if duplicate.overwrite_document_id is not None:
            raise HTTPException(status_code=409, detail="A previous overwrite of this filename is incomplete. Retry that upload first.")
        if overwrite_document_id != duplicate.id:
            raise HTTPException(status_code=409, detail={
                "code": "filename_conflict", "filename": filename, "document_id": str(duplicate.id),
                "message": "A file with this name already exists. Overwrite it?",
            })
        if membership.role != "owner":
            raise HTTPException(status_code=403, detail="Only the case owner can overwrite files.")
    elif overwrite_document_id is not None:
        raise HTTPException(status_code=409, detail="The file to overwrite changed or was deleted. Reload before uploading again.")

    if not new_case:
        if case.closed_at is not None or case.status == "finalized":
            raise HTTPException(status_code=409, detail="This case is closed or read-only.")
        if (case.metadata_json or {}).get("onboarding_reset"):
            raise HTTPException(status_code=409, detail="Finish discarding onboarding before importing files.")
        if duplicate is not None:
            enforce_attachment_quota(db, case_id, incoming=0)
        else:
            enforce_attachment_quota(db, case_id)

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
        original_filename=filename,
        overwrite_document_id=duplicate.id if duplicate is not None else None,
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
        require_scope_active(db, "case", case_id)
        db.commit()
    except HTTPException:
        db.rollback()
        _delete_uploaded_object(object_key if upload_attempted else None)
        raise
    except (BotoCoreError, RuntimeError) as error:
        db.rollback()
        _delete_uploaded_object(object_key if upload_attempted else None)
        log_failure_event(logger, "upload_storage_failed", error)
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
                    _validate_retry_file(recovered_document, filename, content)
                    _finish_overwrite(db, user, recovered_document)
                    return _document_response(item_id, recovered_batch.case_id, recovered_document)
                raise HTTPException(
                    status_code=409,
                    detail="Another file in this import is being saved. Please retry.",
                ) from error
        log_failure_event(logger, "upload_persistence_failed", error)
        raise HTTPException(
            status_code=503,
            detail="This file could not be recorded. Please retry it.",
        ) from error
    except Exception as error:
        db.rollback()
        _delete_uploaded_object(object_key if upload_attempted else None)
        log_failure_event(logger, "upload_unexpected_failure", error)
        raise HTTPException(
            status_code=503,
            detail="This file could not be confirmed as stored. Check its import status before retrying.",
        ) from error

    _finish_overwrite(db, user, document)
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
            .where(
                ~select(DeletionTombstone.id)
                .where(
                    DeletionTombstone.scope_type == "document",
                    DeletionTombstone.scope_id == Document.id,
                )
                .exists()
            )
            .order_by(MaterialImportItem.id)
        ).all()
    except SQLAlchemyError as error:
        log_failure_event(logger, "upload_reconciliation_failed", error)
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
