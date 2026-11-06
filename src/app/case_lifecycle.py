import io
import json
import logging
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile

from botocore.exceptions import BotoCoreError
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth_routes import require_current_user
from app.database import Base, get_db
from app.models import (
    Case,
    CaseLifecycleEvent,
    CaseMembership,
    DeletionTombstone,
    Document,
    User,
)
from app.storage import ObjectStorage

logger = logging.getLogger(__name__)
router = APIRouter(tags=["case lifecycle"])
storage = ObjectStorage()

# Tables scoped directly by case_id, then tables scoped through the case's documents.
CASE_TABLES = (
    "negotiation_events",
    "case_lifecycle_events",
    "settlement_planning_consent_events",
    "settlement_scenario_runs",
    "settlement_ledger_events",
    "settlement_scenario_selections",
    "settlement_negotiation_attempts",
    "settlement_proposal_versions",
    "settlement_offer_responses",
    "export_delivery_events",
    "documents",
    "material_import_batches",
    "document_analysis_consents",
    "document_analysis_requests",
    "case_profile_adoptions",
    "case_profile_facts",
    "case_profile_fact_events",
    "analysis_proposal_review_events",
)
DOCUMENT_TABLES = (
    "document_extractions",
    "document_extraction_jobs",
    "document_analysis_jobs",
    "document_analysis_proposals",
    "material_import_items",
    "settlement_offer_response_attachments",
)
# Internal storage, lease and idempotency details are not user data.
EXCLUDED_COLUMNS = {
    "object_key",
    "lease_token",
    "lease_expires_at",
    "destination_digest",
    "idempotency_key",
    "docx_content",
    "xlsx_content",
}

README = """Case data export

manifest.json contains the case profile, notes, negotiation attempts, offers,
calculations, generated records and this case's attempt-credit balance and ledger.
files/ contains the documents you uploaded and the proposal documents generated
for this case.

Closing a case does not delete it and unused attempt credits do not expire. This
export is a copy of your workspace data, not a legal determination, and a
closed case does not mean the legal matter is resolved.
"""


class CaseCloseRequest(BaseModel):
    reason: Literal["stopped", "closed"] = "closed"


class CaseLifecycleRead(BaseModel):
    id: UUID
    status: str
    closed_at: datetime | None
    closed_reason: str | None
    attempt_credit_balance: int


class ClosedCaseRead(BaseModel):
    id: UUID
    title: str
    status: str
    closed_at: datetime
    closed_reason: str | None


class ClosedCaseList(BaseModel):
    cases: list[ClosedCaseRead]


def get_storage() -> ObjectStorage:
    return storage


def lifecycle_write_allowed(case: Case, path: str) -> bool:
    if case.status != "finalized" and case.closed_at is None:
        return True
    return path.rstrip("/").endswith(
        ("/reopen", "/close", "/delegation", "/permanent-deletion")
    )


def close_case_record(db: Session, case: Case, user_id: UUID, reason: str) -> None:
    if case.closed_at is not None:
        return
    case.closed_at = datetime.now(UTC)
    case.closed_reason = reason
    case.status_before_close = case.status
    db.add(
        CaseLifecycleEvent(
            case_id=case.id, user_id_snapshot=user_id, event_type="closed", reason=reason
        )
    )


def _membership(db: Session, case_id: UUID, user: User) -> CaseMembership:
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
    return membership


def _owned_case(db: Session, case_id: UUID, user: User) -> Case:
    membership = _membership(db, case_id, user)
    if membership.role not in {"owner", "delegate"}:
        raise HTTPException(status_code=403, detail="Only the case owner can do this.")
    case = db.get(Case, case_id, with_for_update=True)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    return case


def _read(case: Case, user: User) -> CaseLifecycleRead:
    return CaseLifecycleRead(
        id=case.id,
        status=case.status,
        closed_at=case.closed_at,
        closed_reason=case.closed_reason,
        attempt_credit_balance=case.attempt_credit_balance,
    )


def _commit(db: Session, action: str) -> None:
    try:
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        logger.error("Case %s failed (%s).", action, type(error).__name__)
        raise HTTPException(
            status_code=503, detail=f"The case could not be {action}. Please try again."
        ) from error


@router.post("/cases/{case_id}/close", response_model=CaseLifecycleRead)
def close_case(
    case_id: UUID,
    payload: CaseCloseRequest,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> CaseLifecycleRead:
    case = _owned_case(db, case_id, user)
    close_case_record(db, case, user.id, payload.reason)
    _commit(db, "closed")
    return _read(case, user)


@router.post("/cases/{case_id}/reopen", response_model=CaseLifecycleRead)
def reopen_case(
    case_id: UUID,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> CaseLifecycleRead:
    case = _owned_case(db, case_id, user)
    if case.closed_at is None and case.status != "finalized":
        raise HTTPException(status_code=409, detail="This case is already open.")
    # Reopening restores an existing case; it is never gated by plan or other cases.
    restored = case.status_before_close
    case.status = restored if restored and restored != "finalized" else "settlement"
    case.closed_at = None
    case.closed_reason = None
    case.status_before_close = None
    db.add(
        CaseLifecycleEvent(case_id=case.id, user_id_snapshot=user.id, event_type="reopened")
    )
    _commit(db, "reopened")
    return _read(case, user)


@router.get("/api/v1/closed-cases", response_model=ClosedCaseList)
def list_closed_cases(
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> ClosedCaseList:
    cases = db.scalars(
        select(Case)
        .join(CaseMembership, CaseMembership.case_id == Case.id)
        .where(
            CaseMembership.user_id == user.id,
            CaseMembership.role.in_(("owner", "delegate")),
            CaseMembership.revoked_at.is_(None),
            CaseMembership.suspended_at.is_(None),
            Case.closed_at.is_not(None),
            ~select(DeletionTombstone.id)
            .where(
                DeletionTombstone.scope_type == "case",
                DeletionTombstone.scope_id == Case.id,
            )
            .exists(),
        )
        .order_by(Case.closed_at.desc(), Case.id)
    ).all()
    result = []
    for case in cases:
        title = (case.metadata_json or {}).get("case_title")
        result.append(
            ClosedCaseRead(
                id=case.id,
                title=title.strip() if isinstance(title, str) and title.strip() else "Case",
                status=case.status,
                closed_at=case.closed_at,
                closed_reason=case.closed_reason,
            )
        )
    return ClosedCaseList(cases=result)


def _rows(db: Session, table, where) -> list[dict]:
    columns = [c for c in table.columns if c.name not in EXCLUDED_COLUMNS]
    rows = db.execute(select(*columns).where(where).order_by(*table.primary_key.columns)).mappings()
    return [jsonable_encoder(dict(row)) for row in rows]


def _collect_tables(db: Session, case_id: UUID) -> dict[str, list[dict]]:
    metadata = Base.metadata.tables
    tables = {
        name: _rows(db, metadata[name], metadata[name].c.case_id == case_id)
        for name in CASE_TABLES
    }
    document_ids = select(metadata["documents"].c.id).where(
        metadata["documents"].c.case_id == case_id
    )
    for name in DOCUMENT_TABLES:
        tables[name] = _rows(db, metadata[name], metadata[name].c.document_id.in_(document_ids))
    return tables


@router.get("/cases/{case_id}/export")
def export_case(
    case_id: UUID,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
    object_storage: ObjectStorage = Depends(get_storage),
) -> Response:
    _membership(db, case_id, user)
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    try:
        manifest = {
            "format_version": 1,
            "exported_at": datetime.now(UTC).isoformat(),
            "case": jsonable_encoder(
                {
                    "id": case.id,
                    "status": case.status,
                    "closed_at": case.closed_at,
                    "closed_reason": case.closed_reason,
                    "metadata_json": case.metadata_json,
                    "asset_liability_inventory": case.asset_liability_inventory,
                    "relationship_milestones": case.relationship_milestones,
                    "property_assets": case.property_assets,
                    "profile_revision": case.profile_revision,
                    "settlement_revision": case.settlement_revision,
                    "attempt_credit_balance": case.attempt_credit_balance,
                    "first_finalization_used": case.first_finalization_used,
                    "created_at": case.created_at,
                    "updated_at": case.updated_at,
                }
            ),
            "tables": _collect_tables(db, case_id),
        }
        ledger = db.execute(
            select(
                Base.metadata.tables["document_credit_ledger_entries"].c.id,
                Base.metadata.tables["document_credit_ledger_entries"].c.proposal_version_id,
                Base.metadata.tables["document_credit_ledger_entries"].c.source_type,
                Base.metadata.tables["document_credit_ledger_entries"].c.source_reference,
                Base.metadata.tables["document_credit_ledger_entries"].c.delta,
                Base.metadata.tables["document_credit_ledger_entries"].c.balance_after,
                Base.metadata.tables["document_credit_ledger_entries"].c.created_at,
            )
            .where(
                Base.metadata.tables["document_credit_ledger_entries"].c.case_id == case_id,
                Base.metadata.tables["document_credit_ledger_entries"].c.user_id == user.id,
            )
            .order_by(Base.metadata.tables["document_credit_ledger_entries"].c.created_at)
        ).mappings()
        manifest["credits"] = {
            "balance": case.attempt_credit_balance,
            "ledger": [jsonable_encoder(dict(row)) for row in ledger],
        }
        files: list[dict] = []
        output = io.BytesIO()
        with ZipFile(output, "w", ZIP_DEFLATED) as archive:
            for document in db.scalars(select(Document).where(Document.case_id == case_id)):
                path = f"files/documents/{document.id}.{document.extension}"
                archive.writestr(path, object_storage.get(document.object_key))
                files.append(
                    {"kind": "document", "id": str(document.id), "path": path,
                     "media_type": document.media_type, "sha256": document.sha256}
                )
            versions = db.execute(
                select(
                    Base.metadata.tables["settlement_proposal_versions"].c.id,
                    Base.metadata.tables["settlement_proposal_versions"].c.version_ordinal,
                    Base.metadata.tables["settlement_proposal_versions"].c.docx_content,
                    Base.metadata.tables["settlement_proposal_versions"].c.xlsx_content,
                ).where(Base.metadata.tables["settlement_proposal_versions"].c.case_id == case_id)
            ).all()
            for version_id, ordinal, docx, xlsx in versions:
                for extension, content in (("docx", docx), ("xlsx", xlsx)):
                    path = f"files/proposal-versions/{version_id}-v{ordinal}.{extension}"
                    archive.writestr(path, content)
                    files.append({"kind": "proposal_version", "id": str(version_id), "path": path})
            manifest["files"] = files
            archive.writestr("manifest.json", json.dumps(manifest, indent=2))
            archive.writestr("README.txt", README)
    except (SQLAlchemyError, BotoCoreError, KeyError) as error:
        logger.error("Case export failed (%s).", type(error).__name__)
        raise HTTPException(
            status_code=503, detail="The export could not be created. Please try again."
        ) from error
    return Response(
        content=output.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="case-{case_id}-export.zip"',
            "Cache-Control": "no-store",
        },
    )
