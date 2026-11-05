import logging
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth_routes import require_current_user
from app.database import get_db
from app.models import Case, Document, SettlementNegotiationAttempt, User
from app.settlement_routes import _authorize_case, _lock_case

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cases/{case_id}/existing-offer", tags=["existing offer intake"])

METADATA_KEY = "existing_offer"
MAX_NOTES_LENGTH = 20_000
MAX_DOCUMENTS = 10
OfferOrigin = Literal["initial_incoming_offer", "initial_user_proposal", "counteroffer_response"]


def _normalize_notes(value: object) -> object:
    if isinstance(value, str):
        return value.strip() or None
    return value


def _require_offer_source(exists: bool, notes: str | None, document_count: int) -> None:
    if exists and notes is None and document_count == 0:
        raise ValueError("Add an offer document or notes describing the offer.")
    if not exists and (notes is not None or document_count):
        raise ValueError("Offer notes and documents require an existing offer.")


class ExistingOfferCreate(BaseModel):
    """Intake answer accepted when a case is created; no document can exist yet."""

    model_config = ConfigDict(extra="forbid")

    exists: bool
    notes: str | None = Field(default=None, max_length=MAX_NOTES_LENGTH + 1000)

    @field_validator("notes", mode="before")
    @classmethod
    def trim_notes(cls, value: object) -> object:
        return _normalize_notes(value)

    @field_validator("notes")
    @classmethod
    def notes_within_limit(cls, value: str | None) -> str | None:
        if value is not None and len(value) > MAX_NOTES_LENGTH:
            raise ValueError("Notes are too long.")
        return value

    @model_validator(mode="after")
    def require_source(self) -> "ExistingOfferCreate":
        _require_offer_source(self.exists, self.notes, 0)
        return self


class ExistingOfferUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exists: bool
    notes: str | None = Field(default=None, max_length=MAX_NOTES_LENGTH + 1000)
    document_ids: list[UUID] = Field(default_factory=list, max_length=MAX_DOCUMENTS)

    @field_validator("notes", mode="before")
    @classmethod
    def trim_notes(cls, value: object) -> object:
        return _normalize_notes(value)

    @field_validator("notes")
    @classmethod
    def notes_within_limit(cls, value: str | None) -> str | None:
        if value is not None and len(value) > MAX_NOTES_LENGTH:
            raise ValueError("Notes are too long.")
        return value

    @field_validator("document_ids")
    @classmethod
    def unique_documents(cls, value: list[UUID]) -> list[UUID]:
        return list(dict.fromkeys(value))

    @model_validator(mode="after")
    def require_source(self) -> "ExistingOfferUpdate":
        _require_offer_source(self.exists, self.notes, len(self.document_ids))
        return self


class AssetTerm(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_index: int = Field(ge=0, lt=250)
    asset_name: str = Field(min_length=1, max_length=200)
    term: str = Field(max_length=2000)

    @field_validator("term")
    @classmethod
    def term_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Describe the offered term for this asset.")
        return value


class AssetTermsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    terms: list[AssetTerm] = Field(max_length=250)

    @field_validator("terms")
    @classmethod
    def unique_assets(cls, value: list[AssetTerm]) -> list[AssetTerm]:
        if len({term.asset_index for term in value}) != len(value):
            raise ValueError("Each asset can have only one offered term.")
        return value


class OfferDocumentRead(BaseModel):
    id: UUID
    extension: str
    size_bytes: int
    created_at: datetime


class OfferAssetRead(BaseModel):
    index: int
    name: str


class ExistingOfferRead(BaseModel):
    exists: bool | None
    origin: Literal["initial_incoming_offer"] | None
    notes: str | None
    document_ids: list[UUID]
    asset_terms: list[AssetTerm]
    assets: list[OfferAssetRead]
    documents: list[OfferDocumentRead]


def build_offer_record(
    exists: bool,
    notes: str | None,
    document_ids: list[UUID],
    asset_terms: list[dict] | None = None,
) -> dict:
    return {
        "exists": exists,
        "origin": "initial_incoming_offer" if exists else None,
        "notes": notes,
        "document_ids": [str(document_id) for document_id in document_ids],
        "asset_terms": asset_terms or [],
        "updated_at": datetime.now(UTC).isoformat(),
    }


def offer_origin(attempt_ordinal: int, snapshot: dict) -> OfferOrigin:
    if attempt_ordinal > 1:
        return "counteroffer_response"
    metadata = (snapshot.get("case_profile") or {}).get("metadata") or {}
    record = metadata.get(METADATA_KEY)
    if isinstance(record, dict) and record.get("exists") is True:
        return "initial_incoming_offer"
    return "initial_user_proposal"


def _record(case: Case) -> dict | None:
    record = (case.metadata_json or {}).get(METADATA_KEY)
    return record if isinstance(record, dict) else None


def _read(db: Session, case: Case) -> ExistingOfferRead:
    record = _record(case) or {}
    documents = db.scalars(
        select(Document)
        .where(Document.case_id == case.id)
        .order_by(Document.created_at, Document.id)
    ).all()
    return ExistingOfferRead(
        exists=record.get("exists"),
        origin=record.get("origin"),
        notes=record.get("notes"),
        document_ids=record.get("document_ids", []),
        asset_terms=record.get("asset_terms", []),
        assets=[
            OfferAssetRead(index=index, name=str(asset.get("name", "")))
            for index, asset in enumerate(case.property_assets or [])
        ],
        documents=[
            OfferDocumentRead(
                id=document.id,
                extension=document.extension,
                size_bytes=document.size_bytes,
                created_at=document.created_at,
            )
            for document in documents
        ],
    )


def _commit(db: Session) -> None:
    try:
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Existing-offer intake could not be saved.")
        raise HTTPException(
            status_code=503,
            detail="Offer details could not be saved. Please try again.",
        ) from error


def _require_open_case(case: Case) -> None:
    if getattr(case, "status", None) == "finalized":
        raise HTTPException(status_code=409, detail="This case is completed and read-only.")


@router.get("", response_model=ExistingOfferRead)
def read_existing_offer(
    case_id: UUID,
    response: Response,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> ExistingOfferRead:
    try:
        case = _authorize_case(db, user, case_id, write=False)
        result = _read(db, case)
    except SQLAlchemyError as error:
        logger.exception("Existing-offer intake lookup failed.")
        raise HTTPException(
            status_code=503,
            detail="Offer details are unavailable. Please try again.",
        ) from error
    response.headers["Cache-Control"] = "no-store"
    return result


@router.put("", response_model=ExistingOfferRead)
def update_existing_offer(
    case_id: UUID,
    payload: ExistingOfferUpdate,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> ExistingOfferRead:
    try:
        _authorize_case(db, user, case_id, write=True)
        case = _lock_case(db, case_id)
        _require_open_case(case)
        record = _record(case)
        previous_exists = record.get("exists") if record else None
        if previous_exists != payload.exists and db.scalar(
            select(SettlementNegotiationAttempt.id)
            .where(SettlementNegotiationAttempt.case_id == case_id)
            .limit(1)
        ) is not None:
            raise HTTPException(
                status_code=409,
                detail="The offer answer cannot change after negotiation has begun.",
            )
        if payload.document_ids:
            owned = set(
                db.scalars(
                    select(Document.id).where(
                        Document.id.in_(payload.document_ids),
                        Document.case_id == case_id,
                    )
                ).all()
            )
            if owned != set(payload.document_ids):
                raise HTTPException(
                    status_code=422,
                    detail="Offer documents must be uploaded to this case.",
                )
        kept_terms = record.get("asset_terms", []) if record and payload.exists else []
        case.metadata_json = {
            **(case.metadata_json or {}),
            METADATA_KEY: build_offer_record(
                payload.exists, payload.notes, payload.document_ids, kept_terms
            ),
        }
        _commit(db)
        return _read(db, case)
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Existing-offer intake update failed.")
        raise HTTPException(
            status_code=503,
            detail="Offer details could not be saved. Please try again.",
        ) from error


@router.put("/asset-terms", response_model=ExistingOfferRead)
def update_asset_terms(
    case_id: UUID,
    payload: AssetTermsUpdate,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> ExistingOfferRead:
    try:
        _authorize_case(db, user, case_id, write=True)
        case = _lock_case(db, case_id)
        _require_open_case(case)
        record = _record(case)
        if not record or record.get("exists") is not True:
            raise HTTPException(status_code=409, detail="Record an existing offer first.")
        assets = case.property_assets or []
        if not assets:
            raise HTTPException(
                status_code=409,
                detail="Create the asset inventory before relating offer terms to assets.",
            )
        for term in payload.terms:
            if term.asset_index >= len(assets) or assets[term.asset_index].get("name") != term.asset_name:
                raise HTTPException(
                    status_code=409,
                    detail="The asset inventory changed. Reload before mapping terms.",
                )
        case.metadata_json = {
            **(case.metadata_json or {}),
            METADATA_KEY: {
                **record,
                "asset_terms": [term.model_dump() for term in payload.terms],
                "updated_at": datetime.now(UTC).isoformat(),
            },
        }
        _commit(db)
        return _read(db, case)
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Existing-offer asset mapping failed.")
        raise HTTPException(
            status_code=503,
            detail="Offer details could not be saved. Please try again.",
        ) from error
