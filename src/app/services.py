import hashlib
import logging
from dataclasses import dataclass
from uuid import UUID, uuid4

from botocore.exceptions import BotoCoreError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.attachment_limits import enforce_attachment_quota
from app.models import Case, Document, DocumentExtraction
from app.storage import ObjectStorage

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Artifact:
    content: bytes
    extension: str
    media_type: str


def store_artifacts(
    db: Session,
    storage: ObjectStorage,
    case_id: UUID,
    artifacts: list[Artifact],
    extraction_data: tuple[str, int] | None = None,
) -> tuple[list[Document], DocumentExtraction | None]:
    if extraction_data is not None and len(artifacts) != 1:
        raise ValueError("An extraction can only be saved with one document.")

    records: list[Document] = []
    uploaded_keys: list[str] = []
    extraction = None

    enforce_attachment_quota(db, case_id, len(artifacts))
    try:
        for artifact in artifacts:
            document_id = uuid4()
            key = f"{case_id}/{document_id}.{artifact.extension}"
            storage.put(key, artifact.content, artifact.media_type)
            uploaded_keys.append(key)
            records.append(
                Document(
                    id=document_id,
                    case_id=case_id,
                    object_key=key,
                    extension=artifact.extension,
                    media_type=artifact.media_type,
                    sha256=hashlib.sha256(artifact.content).hexdigest(),
                    size_bytes=len(artifact.content),
                )
            )
        db.add_all(records)
        if extraction_data is not None:
            extracted_text, page_count = extraction_data
            extraction = DocumentExtraction(
                document_id=records[0].id,
                extracted_text=extracted_text,
                page_count=page_count,
                review_status="pending_review",
            )
            db.add(extraction)
        db.commit()
        return records, extraction
    except BotoCoreError:
        db.rollback()
        _delete_uploaded(storage, uploaded_keys)
        raise
    except SQLAlchemyError:
        db.rollback()
        _delete_uploaded(storage, uploaded_keys)
        raise


def get_case_or_none(db: Session, case_id: UUID) -> Case | None:
    return db.get(Case, case_id)


def get_document_or_none(db: Session, document_id: UUID) -> Document | None:
    return db.get(Document, document_id)


def _delete_uploaded(storage: ObjectStorage, keys: list[str]) -> None:
    for key in keys:
        try:
            storage.delete(key)
        except BotoCoreError:
            logger.exception("Could not clean up object after a failed document transaction: %s", key)
