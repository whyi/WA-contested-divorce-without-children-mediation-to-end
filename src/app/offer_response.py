import hashlib
import logging
from copy import deepcopy
from datetime import UTC, date, datetime
from pathlib import PurePath
from typing import Literal
from urllib.parse import quote
from uuid import UUID, uuid4

from botocore.exceptions import BotoCoreError
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth_routes import require_current_user
from app.config import get_settings
from app.database import get_db
from app.models import (
    Case,
    Document,
    SettlementLedgerEvent,
    SettlementNegotiationAttempt,
    SettlementOfferResponse,
    SettlementProposalVersion,
    SettlementOfferResponseAttachment,
    SettlementScenarioRun,
    SettlementScenarioSelection,
    User,
    user_settlement_attempt_limit,
)
from app.existing_offer import OfferOrigin, offer_origin
from app.offer_documents import MediationOfferTerms
from app.modified_offer import ModifiedOfferParseError, parse_modified_offer
from app.settlement_planning import ScenarioAxes, calculate_scenario, generate_scenarios
from app.settlement_routes import (
    _active_profile_facts,
    _authorize_case,
    _lock_case,
    _prepare_attempt_offer_export,
)
from app.case_lifecycle import close_case_record
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
    "modified_docx": {"docx"},
    "modified_xlsx": {"xlsx"},
    "counteroffer": {"docx", "xlsx", "pdf"},
    "accepted_offer": {"docx", "xlsx", "pdf"},
}


class OfferResponseAttachmentRead(BaseModel):
    id: UUID
    kind: Literal[
        "sent_docx",
        "sent_xlsx",
        "modified_docx",
        "modified_xlsx",
        "counteroffer",
        "accepted_offer",
        "modified_source_docx",
        "modified_source_xlsx",
    ]
    filename: str
    extension: Literal["docx", "xlsx", "pdf"]
    size_bytes: int


class ModifiedOfferParseRead(BaseModel):
    editable_state: dict
    warnings: list[str]


class OfferResponseRead(BaseModel):
    selection_id: UUID
    outcome: Literal["counteroffer", "rejected", "accepted"] | None
    attachments: list[OfferResponseAttachmentRead]
    sent_documents_complete: bool
    sent_confirmed: bool
    counteroffer_attachment_present: bool
    attempt_ordinal: int
    offer_origin: OfferOrigin
    attempt_limit: int
    attempts_remaining: int
    frozen: bool
    proposal_issued: bool
    proposal_draft_unlocked: bool
    proposal_version_ordinal: int
    attempt_revision: int
    editable_state: dict
    snapshot: dict
    scenario_result: dict
    proposal_terms: dict | None
    has_next_attempt: bool


class OfferOutcomeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: Literal["counteroffer", "rejected", "accepted"]
    expected_attempt_revision: int = Field(default=0, ge=0)


class OfferSentConfirmation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_attempt_revision: int = Field(ge=0)


class NegotiationMilestone(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    date: date


class NegotiationValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: UUID
    proposed_amount_cents: int = Field(ge=-1_000_000_000_000, le=1_000_000_000_000)


class OfferAttemptStateUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_revision: int = Field(ge=0)
    offer_from: str = Field(default="", max_length=160)
    offer_to: str = Field(default="", max_length=160)
    county: str = Field(default="", max_length=100)
    cause_number: str = Field(default="", max_length=100)
    proposed_effective_date: date | None = None
    proposed_response_date: date | None = None
    scenario_assumptions: ScenarioAxes | None = None
    milestones: list[NegotiationMilestone] = Field(default_factory=list, max_length=100)
    proposed_values: list[NegotiationValue] = Field(default_factory=list, max_length=500)
    proposal_terms: list[str] = Field(default_factory=list, max_length=80)
    sent_offer_mode: Literal["unchanged", "modified"] = "unchanged"
    modified_offer_reviewed: bool = False

    @field_validator("proposal_terms")
    @classmethod
    def validate_proposal_terms(cls, terms: list[str]) -> list[str]:
        cleaned = [term.strip() for term in terms]
        if any(not term or len(term) > 2_000 for term in cleaned):
            raise ValueError("Proposal terms must contain 1 to 2,000 characters.")
        return cleaned


class OfferAttemptStateRead(BaseModel):
    selection_id: UUID
    attempt_ordinal: int
    revision: int
    editable_state: dict
    scenario_result: dict
    scenario_recalculated: bool


def _attempt_for_selection(
    db: Session,
    selection: SettlementScenarioSelection,
) -> SettlementNegotiationAttempt | None:
    return db.scalar(
        select(SettlementNegotiationAttempt).where(
            SettlementNegotiationAttempt.case_id == selection.case_id,
            SettlementNegotiationAttempt.selection_id == selection.id,
        )
    )


def _attempt_snapshot(
    db: Session,
    case: Case,
    selection: SettlementScenarioSelection,
) -> dict:
    if (
        selection.profile_revision != case.profile_revision
        or selection.settlement_revision != case.settlement_revision
    ):
        raise HTTPException(status_code=409, detail="Selected scenario is stale. Recalculate before continuing.")
    run = db.scalar(
        select(SettlementScenarioRun).where(
            SettlementScenarioRun.id == selection.run_id,
            SettlementScenarioRun.case_id == case.id,
        )
    )
    if run is None:
        raise HTTPException(status_code=409, detail="Selected scenario run is unavailable.")

    facts = _active_profile_facts(db, case.id)
    profile_facts = [
        {
            "id": str(fact.id),
            "field_key": fact.field_key,
            "value": fact.value,
            "source_document_id": str(fact.source_document_id),
            "source_sha256": fact.source_sha256,
            "source_page_number": fact.source_page_number,
            "review_decision": fact.review_decision,
            "profile_revision": fact.profile_revision,
        }
        for fact in facts
    ]
    ledger = db.scalars(
        select(SettlementLedgerEvent)
        .where(SettlementLedgerEvent.case_id == case.id)
        .order_by(
            SettlementLedgerEvent.asset_id,
            SettlementLedgerEvent.effective_date,
            SettlementLedgerEvent.sequence_number,
            SettlementLedgerEvent.id,
        )
    ).all()
    return {
        "schema_version": 1,
        "case_id": str(case.id),
        "revisions": {
            "profile": case.profile_revision,
            "settlement": case.settlement_revision,
        },
        "scenario": {
            "run_id": str(run.id),
            "scenario_id": selection.scenario_id,
            "objective": run.objective,
            "axes": run.axes_json,
            "result": selection.scenario_result_json,
        },
        "case_profile": {
            "metadata": case.metadata_json,
            "asset_liability_inventory": case.asset_liability_inventory,
            "relationship_milestones": case.relationship_milestones,
            "property_assets": case.property_assets,
            "facts": profile_facts,
        },
        "settlement_ledger": [
            {
                "asset_id": str(row.asset_id),
                "asset_name": row.asset_name,
                "asset_kind": row.asset_kind,
                "effective_date": row.effective_date.isoformat(),
                "sequence_number": row.sequence_number,
                "event": row.event_json,
                "profile_revision": row.profile_revision,
                "settlement_revision": row.settlement_revision,
            }
            for row in ledger
        ],
    }


def _create_initial_attempt(
    db: Session,
    case: Case,
    selection: SettlementScenarioSelection,
    user: User,
) -> SettlementNegotiationAttempt:
    previous = db.scalar(
        select(SettlementNegotiationAttempt)
        .where(SettlementNegotiationAttempt.case_id == case.id)
        .order_by(SettlementNegotiationAttempt.attempt_ordinal.desc())
        .limit(1)
    )
    if previous is not None:
        raise HTTPException(
            status_code=409,
            detail="Continue the saved negotiation attempt before selecting another scenario.",
        )
    snapshot = _attempt_snapshot(db, case, selection)
    selected_scenario = snapshot["scenario"]["result"]["scenario"]
    editable_axes = {
        "relationship_windows": [selected_scenario["relationship_window"]],
        "tracing_methods": [selected_scenario["tracing_method"]],
        "community_share_bps": [selected_scenario["community_share_bps"]],
    }
    response_record = SettlementOfferResponse(
        case_id=case.id,
        selection_id=selection.id,
        user_id=user.id,
        user_id_snapshot=user.id,
    )
    db.add(response_record)
    attempt = SettlementNegotiationAttempt(
        case_id=case.id,
        selection_id=selection.id,
        attempt_ordinal=1,
        snapshot_json=snapshot,
        editable_state_json={
            "scenario_assumptions": editable_axes,
        },
    )
    db.add(attempt)
    return attempt


def _require_current_attempt_revisions(case: Case, attempt: SettlementNegotiationAttempt) -> None:
    revisions = attempt.snapshot_json.get("revisions", {})
    if (
        revisions.get("profile") != case.profile_revision
        or revisions.get("settlement") != case.settlement_revision
    ):
        raise HTTPException(
            status_code=409,
            detail="Case facts or settlement ledger changed since this attempt began. Reload before continuing.",
        )


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
    attempt_limit: int,
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
                "id": item.id,
                "kind": item.kind,
                "filename": item.filename,
                "extension": document.extension,
                "size_bytes": document.size_bytes,
            }
            for item, document in rows
        ]
    attempt = _attempt_for_selection(db, selection)
    proposal_issued_at = getattr(attempt, "proposal_issued_at", None)
    proposal_terms = getattr(attempt, "proposal_terms_json", None)
    proposal_scenario_result = getattr(attempt, "proposal_scenario_result_json", None)
    if attempt is not None and getattr(attempt, "proposal_draft_unlocked", False):
        scenario_result = selection.scenario_result_json
    elif proposal_scenario_result is not None:
        scenario_result = proposal_scenario_result
    else:
        scenario_result = selection.scenario_result_json
    kinds = {item["kind"] for item in attachments}
    sent_documents_complete = (
        {"modified_docx", "modified_xlsx"}.issubset(kinds)
        if attempt is not None
        and attempt.editable_state_json.get("sent_offer_mode") == "modified"
        else {"sent_docx", "sent_xlsx"}.issubset(kinds)
    )
    has_next_attempt = False
    if attempt is not None:
        has_next_attempt = db.scalar(
            select(SettlementNegotiationAttempt.id).where(
                SettlementNegotiationAttempt.predecessor_id == attempt.id
            )
        ) is not None
    snapshot = (
        attempt.frozen_snapshot_json or attempt.snapshot_json if attempt is not None else {}
    )
    attempt_ordinal = attempt.attempt_ordinal if attempt is not None else 1
    return OfferResponseRead(
        selection_id=selection.id,
        outcome=response_record.outcome if response_record is not None else None,
        attachments=attachments,
        sent_documents_complete=sent_documents_complete,
        sent_confirmed=attempt.sent_confirmed_at is not None if attempt is not None else False,
        counteroffer_attachment_present="counteroffer" in kinds,
        attempt_ordinal=attempt_ordinal,
        offer_origin=offer_origin(attempt_ordinal, snapshot),
        attempt_limit=attempt_limit,
        attempts_remaining=max(
            0,
            attempt_limit - (attempt.attempt_ordinal if attempt is not None else 1),
        ),
        frozen=attempt.frozen_at is not None if attempt is not None else bool(
            response_record and response_record.outcome is not None
        ),
        proposal_issued=proposal_issued_at is not None,
        proposal_draft_unlocked=(
            bool(getattr(attempt, "proposal_draft_unlocked", False))
            if attempt is not None
            else False
        ),
        proposal_version_ordinal=(
            getattr(attempt, "proposal_version_ordinal", 0) if attempt is not None else 0
        ),
        attempt_revision=attempt.revision if attempt is not None else 0,
        editable_state=attempt.editable_state_json if attempt is not None else {},
        snapshot=snapshot,
        scenario_result=scenario_result,
        proposal_terms=proposal_terms,
        has_next_attempt=has_next_attempt,
    )


def _frozen_attempt_snapshot(
    attempt: SettlementNegotiationAttempt,
    selection: SettlementScenarioSelection,
    current: OfferResponseRead,
    *,
    confirmed_at: datetime,
    user_id: UUID,
) -> dict:
    snapshot = deepcopy(attempt.snapshot_json)
    snapshot["scenario"] = {
        "run_id": str(selection.run_id),
        "scenario_id": selection.scenario_id,
        "objective": attempt.snapshot_json["scenario"]["objective"],
        "axes": deepcopy(attempt.editable_state_json.get("scenario_assumptions")),
        "result": deepcopy(
            getattr(attempt, "proposal_scenario_result_json", None)
            or selection.scenario_result_json
        ),
    }
    snapshot["negotiation"] = deepcopy(attempt.editable_state_json)
    proposal_terms = getattr(attempt, "proposal_terms_json", None)
    if proposal_terms is not None:
        snapshot["proposal_terms"] = deepcopy(proposal_terms)
    snapshot["sent_attachments"] = [
        item.model_dump(mode="json")
        for item in current.attachments
        if item.kind
        in (
            {"modified_docx", "modified_xlsx"}
            if attempt.editable_state_json.get("sent_offer_mode") == "modified"
            else {"sent_docx", "sent_xlsx"}
        )
    ]
    snapshot["sent_confirmation"] = {
        "confirmed_at": confirmed_at.isoformat(),
        "user_id_snapshot": str(user_id),
    }
    return snapshot


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


def _modified_offer_documents(
    db: Session,
    selection: SettlementScenarioSelection,
    response_record: SettlementOfferResponse | None,
) -> dict[str, bytes]:
    if response_record is None:
        raise HTTPException(status_code=409, detail="Upload both modified offer documents first.")
    rows = db.execute(
        select(SettlementOfferResponseAttachment, Document)
        .join(Document, Document.id == SettlementOfferResponseAttachment.document_id)
        .where(
            SettlementOfferResponseAttachment.response_id == response_record.id,
            SettlementOfferResponseAttachment.kind.in_(("modified_docx", "modified_xlsx")),
            Document.case_id == selection.case_id,
        )
    ).all()
    documents = {attachment.kind: (attachment, document) for attachment, document in rows}
    if set(documents) != {"modified_docx", "modified_xlsx"}:
        raise HTTPException(status_code=409, detail="Upload both modified DOCX and XLSX files first.")

    contents: dict[str, bytes] = {}
    max_bytes = get_settings().max_upload_bytes
    for kind, expected_extension in (("modified_docx", "docx"), ("modified_xlsx", "xlsx")):
        attachment, document = documents[kind]
        if document.extension != expected_extension:
            raise HTTPException(status_code=415, detail=f"The {kind} attachment has an unsupported file type.")
        try:
            content = storage.get(document.object_key)
        except (BotoCoreError, RuntimeError) as error:
            logger.error("Modified offer document could not be read from storage (%s).", type(error).__name__)
            raise HTTPException(
                status_code=503,
                detail="A modified offer document could not be read. Please retry.",
            ) from error
        try:
            validate_upload(attachment.filename, content, expected_extension, max_bytes)
        except UploadValidationError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        contents[kind] = content
    return contents


def _parse_current_modified_offer(
    db: Session,
    selection: SettlementScenarioSelection,
    response_record: SettlementOfferResponse | None,
    attempt: SettlementNegotiationAttempt,
) -> dict:
    contents = _modified_offer_documents(db, selection, response_record)
    known_assets = attempt.snapshot_json.get("settlement_ledger", [])
    try:
        return parse_modified_offer(
            contents["modified_docx"],
            contents["modified_xlsx"],
            known_assets,
        )
    except ModifiedOfferParseError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


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
    return _read_response(
        db, selection, _response_record(db, selection), user_settlement_attempt_limit(user)
    )


def _finalize_case_record(case, user_id: UUID, db: Session) -> None:
    close_case_record(db, case, user_id, "accepted")
    case.status = "finalized"


@router.post("/complete")
def complete_accepted_case(
    case_id: UUID,
    selection_id: UUID,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    _, selection = _authorized_selection(case_id, selection_id, user, db, write=True)
    case = _lock_case(db, case_id)
    current = _read_response(
        db,
        selection,
        _response_record(db, selection),
        user_settlement_attempt_limit(user),
    )
    if (
        current.outcome != "accepted"
        or not current.sent_documents_complete
        or not current.sent_confirmed
    ):
        raise HTTPException(
            status_code=409,
            detail="Only a confirmed, accepted offer can complete this case.",
        )
    if case.status == "finalized":
        return {"status": "finalized"}

    _finalize_case_record(case, user.id, db)
    try:
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        logger.error("Case finalization failed (%s).", type(error).__name__)
        raise HTTPException(
            status_code=503,
            detail="The case could not be marked as completed. Please try again.",
        ) from error
    return {"status": "finalized"}


@router.post("/parse-modified-offer", response_model=ModifiedOfferParseRead)
def parse_uploaded_modified_offer(
    case_id: UUID,
    selection_id: UUID,
    response: Response,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> ModifiedOfferParseRead:
    _require_secure_case_storage()
    _, selection = _authorized_selection(case_id, selection_id, user, db, write=False)
    attempt = _attempt_for_selection(db, selection)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Negotiation attempt not found.")
    contents = _modified_offer_documents(
        db,
        selection,
        _response_record(db, selection),
    )
    try:
        parsed = parse_modified_offer(
            contents["modified_docx"],
            contents["modified_xlsx"],
            attempt.snapshot_json.get("settlement_ledger", []),
        )
    except ModifiedOfferParseError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    response.headers["Cache-Control"] = "no-store"
    return ModifiedOfferParseRead(**parsed)


@router.get("/attachments/{document_id}")
def download_offer_response_attachment(
    case_id: UUID,
    selection_id: UUID,
    document_id: UUID,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> Response:
    _require_secure_case_storage()
    _, selection = _authorized_selection(case_id, selection_id, user, db, write=False)
    response_record = _response_record(db, selection)
    if response_record is None:
        raise HTTPException(status_code=404, detail="Offer response attachment not found.")
    row = db.execute(
        select(SettlementOfferResponseAttachment, Document)
        .join(Document, Document.id == SettlementOfferResponseAttachment.document_id)
        .where(
            SettlementOfferResponseAttachment.response_id == response_record.id,
            SettlementOfferResponseAttachment.document_id == document_id,
            Document.case_id == case_id,
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Offer response attachment not found.")
    attachment, document = row
    try:
        content = storage.get(document.object_key)
    except (BotoCoreError, RuntimeError) as error:
        logger.error("Offer-response attachment download failed (%s).", type(error).__name__)
        raise HTTPException(status_code=503, detail="The attachment could not be downloaded.") from error
    return Response(
        content=content,
        media_type=document.media_type,
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(attachment.filename, safe='')}",
        },
    )


@router.put("/attempt", response_model=OfferAttemptStateRead)
def update_offer_attempt_state(
    case_id: UUID,
    selection_id: UUID,
    payload: OfferAttemptStateUpdate,
    response: Response,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> OfferAttemptStateRead:
    _authorized_selection(case_id, selection_id, user, db, write=True)
    case = _lock_case(db, case_id)
    selection = _selection(db, case_id, selection_id)
    attempt = _attempt_for_selection(db, selection)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Negotiation attempt not found.")
    if attempt.frozen_at is not None:
        raise HTTPException(status_code=409, detail="This negotiation attempt is frozen and read-only.")
    if (
        attempt.proposal_issued_at is None
        and attempt.attempt_ordinal > user_settlement_attempt_limit(user)
    ):
        raise HTTPException(
            status_code=409,
            detail="This account has reached its negotiation attempt limit.",
        )
    issued = attempt.proposal_issued_at is not None
    draft_unlocked = bool(getattr(attempt, "proposal_draft_unlocked", False))
    if payload.expected_revision != attempt.revision:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Negotiation attempt changed. Reload and retry.",
                "attempt_revision": attempt.revision,
            },
        )
    if issued and not draft_unlocked:
        incoming_state = payload.model_dump(mode="json", exclude={"expected_revision"})
        workflow_fields = {"sent_offer_mode", "modified_offer_reviewed"}
        saved_content = {
            key: value
            for key, value in attempt.editable_state_json.items()
            if key not in workflow_fields
        }
        requested_content = {
            key: value for key, value in incoming_state.items() if key not in workflow_fields
        }
        if saved_content != requested_content:
            raise HTTPException(
                status_code=409,
                detail="This attempt's proposal has been issued. Its terms and scenario are locked.",
            )
        if (
            attempt.editable_state_json.get("sent_offer_mode") == "modified"
            and payload.sent_offer_mode != "modified"
        ):
            raise HTTPException(
                status_code=409,
                detail="The modified-offer workflow cannot be changed after it is selected.",
            )
    else:
        _require_current_attempt_revisions(case, attempt)
    if (
        payload.proposed_effective_date is not None
        and payload.proposed_response_date is not None
        and payload.proposed_effective_date > payload.proposed_response_date
    ):
        raise HTTPException(status_code=422, detail="The proposed effective date must not follow the response date.")
    known_asset_ids = {
        item["asset_id"] for item in attempt.snapshot_json.get("settlement_ledger", [])
    }
    if any(str(value.asset_id) not in known_asset_ids for value in payload.proposed_values):
        raise HTTPException(status_code=422, detail="Proposed values must reference an asset in this attempt snapshot.")
    if payload.modified_offer_reviewed and payload.sent_offer_mode != "modified":
        raise HTTPException(
            status_code=422,
            detail="Modified-offer review can be recorded only for the modified-offer path.",
        )
    if payload.sent_offer_mode == "modified" and payload.modified_offer_reviewed:
        _parse_current_modified_offer(
            db,
            selection,
            _response_record(db, selection),
            attempt,
        )
    if payload.scenario_assumptions is not None:
        known_fact_ids = {
            item["id"] for item in attempt.snapshot_json.get("case_profile", {}).get("facts", [])
        }
        source_fact_ids = {
            str(fact_id)
            for window in payload.scenario_assumptions.relationship_windows
            for fact_id in window.source_fact_ids
        }
        if not source_fact_ids.issubset(known_fact_ids):
            raise HTTPException(
                status_code=422,
                detail="Scenario assumptions may cite only source facts in this attempt snapshot.",
            )
    scenario_result = (
        getattr(attempt, "proposal_scenario_result_json", None)
        or selection.scenario_result_json
    )
    scenario_recalculated = False
    if payload.scenario_assumptions is not None:
        incoming_axes = payload.scenario_assumptions.model_dump(mode="json")
        previous_axes = attempt.editable_state_json.get("scenario_assumptions")
        if incoming_axes != previous_axes:
            try:
                scenarios = generate_scenarios(payload.scenario_assumptions)
                if len(scenarios) != 1:
                    raise HTTPException(
                        status_code=422,
                        detail="A negotiation attempt must have exactly one selected scenario assumption set.",
                    )
                from app.settlement_routes import _asset_ledgers

                ledgers = _asset_ledgers(db, case.id)
                if not ledgers:
                    raise HTTPException(status_code=409, detail="The saved settlement ledger is unavailable.")
                calculated = calculate_scenario(scenarios[0], ledgers)
                ledger_fact_ids = {
                    str(fact_id)
                    for item in attempt.snapshot_json.get("settlement_ledger", [])
                    for fact_id in item.get("event", {}).get("source_fact_ids", [])
                }
            except HTTPException:
                db.rollback()
                raise
            except ValueError as error:
                db.rollback()
                raise HTTPException(status_code=422, detail=str(error)) from error
            except SQLAlchemyError as error:
                db.rollback()
                logger.exception("Attempt-specific scenario could not be calculated.")
                raise HTTPException(status_code=503, detail="Attempt scenario could not be recalculated.") from error
            new_run = SettlementScenarioRun(
                id=uuid4(),
                case_id=case.id,
                user_id=user.id,
                user_id_snapshot=user.id,
                profile_revision=case.profile_revision,
                settlement_revision=case.settlement_revision,
                objective=attempt.snapshot_json["scenario"]["objective"],
                axes_json=incoming_axes,
                scenario_results_json=[calculated.model_dump(mode="json")],
                input_fact_ids=sorted(source_fact_ids | ledger_fact_ids),
            )
            db.add(new_run)
            selection.run_id = new_run.id
            selection.scenario_id = calculated.scenario.id
            selection.scenario_result_json = calculated.model_dump(mode="json")
            selection.profile_revision = case.profile_revision
            selection.settlement_revision = case.settlement_revision
            scenario_result = selection.scenario_result_json
            scenario_recalculated = True
    attempt.editable_state_json = payload.model_dump(mode="json", exclude={"expected_revision"})
    attempt.revision += 1
    try:
        db.commit()
        db.refresh(attempt)
    except SQLAlchemyError as error:
        db.rollback()
        logger.error("Negotiation attempt changes could not be saved (%s).", type(error).__name__)
        raise HTTPException(status_code=503, detail="Negotiation attempt changes could not be saved.") from error
    response.headers["Cache-Control"] = "no-store"
    return OfferAttemptStateRead(
        selection_id=selection.id,
        attempt_ordinal=attempt.attempt_ordinal,
        revision=attempt.revision,
        editable_state=attempt.editable_state_json,
        scenario_result=scenario_result,
        scenario_recalculated=scenario_recalculated,
    )


@router.post("/new-proposal-version")
def start_new_proposal_version(
    case_id: UUID,
    selection_id: UUID,
    response: Response,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, int | bool]:
    _authorized_selection(case_id, selection_id, user, db, write=True)
    _lock_case(db, case_id)
    selection = _selection(db, case_id, selection_id)
    attempt = _attempt_for_selection(db, selection)
    if attempt is None or attempt.proposal_issued_at is None:
        raise HTTPException(status_code=409, detail="Generate the initial proposal before starting a new version.")
    if attempt.frozen_at is not None or attempt.sent_confirmed_at is not None:
        raise HTTPException(status_code=409, detail="A sent or frozen proposal cannot be revised.")
    response_record = _response_record(db, selection)
    if response_record is not None and response_record.outcome is not None:
        raise HTTPException(status_code=409, detail="A proposal with a recorded outcome cannot be revised.")
    if not getattr(attempt, "proposal_draft_unlocked", False):
        legacy_ordinal = max(1, getattr(attempt, "proposal_version_ordinal", 0))
        existing_version = db.scalar(
            select(SettlementProposalVersion).where(
                SettlementProposalVersion.attempt_id == attempt.id,
                SettlementProposalVersion.version_ordinal == legacy_ordinal,
            )
        )
        if existing_version is None:
            if attempt.proposal_terms_json is None:
                raise HTTPException(status_code=409, detail="The issued proposal snapshot is unavailable.")
            _prepare_attempt_offer_export(
                db,
                user,
                case_id,
                selection_id,
                MediationOfferTerms.model_validate(attempt.proposal_terms_json),
                confirm_credit_use=False,
            )
    if not getattr(attempt, "proposal_draft_unlocked", False):
        attempt.proposal_version_ordinal = max(
            1,
            getattr(attempt, "proposal_version_ordinal", 0),
        ) + 1
        attempt.proposal_draft_unlocked = True
        attempt.revision += 1
        try:
            db.commit()
            db.refresh(attempt)
        except SQLAlchemyError as error:
            db.rollback()
            logger.exception("A new proposal version could not be opened.")
            raise HTTPException(status_code=503, detail="A new proposal version could not be opened.") from error
    response.headers["Cache-Control"] = "no-store"
    return {
        "proposal_draft_unlocked": True,
        "proposal_version_ordinal": attempt.proposal_version_ordinal,
        "attempt_revision": attempt.revision,
    }


@router.post("/confirm-sent", response_model=OfferResponseRead)
def confirm_offer_sent(
    case_id: UUID,
    selection_id: UUID,
    payload: OfferSentConfirmation,
    response: Response,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> OfferResponseRead:
    _authorized_selection(case_id, selection_id, user, db, write=True)
    case = _lock_case(db, case_id)
    selection = _selection(db, case_id, selection_id)
    response_record = _response_record(db, selection)
    attempt = _attempt_for_selection(db, selection)
    current = _read_response(
        db, selection, response_record, user_settlement_attempt_limit(user)
    )
    if not current.sent_documents_complete:
        raise HTTPException(
            status_code=409,
            detail="Attach both final DOCX and XLSX files before confirming that you sent them.",
        )
    if attempt is None or response_record is None:
        raise HTTPException(status_code=409, detail="Negotiation attempt is unavailable.")
    if attempt.sent_confirmed_at is not None:
        response.headers["Cache-Control"] = "no-store"
        return current
    if attempt.frozen_at is not None or response_record.outcome is not None:
        raise HTTPException(status_code=409, detail="This negotiation attempt is already frozen.")
    if payload.expected_attempt_revision != attempt.revision:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Negotiation attempt changed. Reload and retry.",
                "attempt_revision": attempt.revision,
            },
        )
    _require_current_attempt_revisions(case, attempt)
    if attempt.editable_state_json.get("sent_offer_mode") == "modified":
        if not attempt.editable_state_json.get("modified_offer_reviewed"):
            raise HTTPException(
                status_code=409,
                detail="Review and accept the parsed modified-offer fields before confirming that you sent them.",
            )
        _parse_current_modified_offer(db, selection, response_record, attempt)
    confirmed_at = datetime.now(UTC)
    attempt.frozen_snapshot_json = _frozen_attempt_snapshot(
        attempt,
        selection,
        current,
        confirmed_at=confirmed_at,
        user_id=user.id,
    )
    attempt.sent_confirmed_at = confirmed_at
    attempt.frozen_at = confirmed_at
    attempt.revision += 1
    try:
        db.commit()
        db.refresh(attempt)
    except SQLAlchemyError as error:
        db.rollback()
        logger.error("Sent-document confirmation failed (%s).", type(error).__name__)
        raise HTTPException(
            status_code=503,
            detail="The sent-document confirmation could not be saved.",
        ) from error
    response.headers["Cache-Control"] = "no-store"
    return _read_response(
        db, selection, response_record, user_settlement_attempt_limit(user)
    )


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
    case = _lock_case(db, case_id)
    response_record = _response_record(db, selection)
    attempt = _attempt_for_selection(db, selection)
    if (
        attempt is not None
        and attempt.frozen_at is None
        and kind in {"sent_docx", "sent_xlsx", "modified_docx", "modified_xlsx"}
    ):
        _require_current_attempt_revisions(case, attempt)
    if kind == "counteroffer" and (
        response_record is None or response_record.outcome != "counteroffer"
    ):
        raise HTTPException(
            status_code=409,
            detail="Select “Counteroffer received” before attaching the received counteroffer.",
        )
    if kind == "accepted_offer" and (
        response_record is None or response_record.outcome != "accepted"
    ):
        raise HTTPException(status_code=409, detail="Record an accepted response before attaching its document.")
    if attempt is not None and attempt.frozen_at is not None:
        if kind in {"sent_docx", "sent_xlsx", "modified_docx", "modified_xlsx"}:
            raise HTTPException(status_code=409, detail="This attempt is frozen; sent documents cannot be replaced.")
        expected_outcome = "counteroffer" if kind == "counteroffer" else "accepted"
        if response_record is None or response_record.outcome != expected_outcome:
            raise HTTPException(status_code=409, detail="This attachment does not match the recorded response.")
    if kind in {"counteroffer", "accepted_offer"} and response_record is not None:
        existing_counteroffer = db.scalar(
            select(SettlementOfferResponseAttachment.id).where(
                SettlementOfferResponseAttachment.response_id == response_record.id,
                SettlementOfferResponseAttachment.kind == kind,
            )
        )
        if existing_counteroffer is not None:
            if kind == "counteroffer":
                detail = "A counteroffer file is already attached to this attempt."
            else:
                detail = "An accepted offer file is already attached to this attempt."
            raise HTTPException(status_code=409, detail=detail)
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
    if kind in {"sent_docx", "sent_xlsx", "modified_docx", "modified_xlsx"} and (
        attempt is None or attempt.frozen_at is None
    ):
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
    if (
        kind in {"modified_docx", "modified_xlsx"}
        and attempt is not None
        and attempt.frozen_at is None
        and attempt.editable_state_json.get("sent_offer_mode") == "modified"
        and attempt.editable_state_json.get("modified_offer_reviewed")
    ):
        attempt.editable_state_json = {
            **attempt.editable_state_json,
            "modified_offer_reviewed": False,
        }
        attempt.revision += 1

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
    return _read_response(
        db, selection, response_record, user_settlement_attempt_limit(user)
    )


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
    _lock_case(db, case_id)
    response_record = _response_record(db, selection)
    current = _read_response(
        db, selection, response_record, user_settlement_attempt_limit(user)
    )
    if not current.sent_documents_complete:
        raise HTTPException(status_code=409, detail="Attach the final sent DOCX and XLSX before choosing an outcome.")
    attempt = _attempt_for_selection(db, selection)
    if response_record is None or attempt is None:
        raise HTTPException(status_code=409, detail="Offer response record is unavailable.")
    if response_record.outcome is not None:
        if response_record.outcome != payload.outcome:
            raise HTTPException(status_code=409, detail="This negotiation attempt is frozen and cannot be changed.")
        response.headers["Cache-Control"] = "no-store"
        return current
    if attempt.sent_confirmed_at is None or attempt.frozen_at is None:
        raise HTTPException(
            status_code=409,
            detail="Confirm that you reviewed and sent the final documents before recording a response.",
        )
    if payload.expected_attempt_revision != attempt.revision:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Negotiation attempt changed. Reload and retry.",
                "attempt_revision": attempt.revision,
            },
        )
    response_record.outcome = payload.outcome
    try:
        db.commit()
        db.refresh(response_record)
    except SQLAlchemyError as error:
        db.rollback()
        logger.error("Offer-response outcome write failed (%s).", type(error).__name__)
        raise HTTPException(status_code=503, detail="The response could not be saved.") from error
    response.headers["Cache-Control"] = "no-store"
    return _read_response(
        db, selection, response_record, user_settlement_attempt_limit(user)
    )


@router.post("/continue")
def continue_offer_response(
    case_id: UUID,
    selection_id: UUID,
    response: Response,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str | int]:
    _authorized_selection(case_id, selection_id, user, db, write=True)
    case = _lock_case(db, case_id)
    selection = _selection(db, case_id, selection_id)
    response_record = _response_record(db, selection)
    current = _read_response(
        db, selection, response_record, user_settlement_attempt_limit(user)
    )
    if not current.sent_documents_complete:
        raise HTTPException(status_code=409, detail="Attach the final sent DOCX and XLSX before continuing.")
    if not current.sent_confirmed:
        raise HTTPException(
            status_code=409,
            detail="Confirm that you reviewed and sent the final documents before continuing.",
        )
    if current.outcome is None:
        raise HTTPException(status_code=409, detail="Choose a response outcome before continuing.")
    if current.outcome == "counteroffer" and not current.counteroffer_attachment_present:
        raise HTTPException(status_code=409, detail="Attach the received counteroffer before continuing.")
    attempt = _attempt_for_selection(db, selection)
    if attempt is None or response_record is None or attempt.frozen_at is None:
        raise HTTPException(status_code=409, detail="The negotiation attempt is not frozen and cannot continue.")
    if current.outcome in {"counteroffer", "rejected"}:
        if attempt.attempt_ordinal >= user_settlement_attempt_limit(user):
            raise HTTPException(
                status_code=409,
                detail="No negotiation attempts remain on this account. Upgrade your plan to continue.",
            )
        _require_current_attempt_revisions(case, attempt)
        next_attempt = db.scalar(
            select(SettlementNegotiationAttempt).where(
                SettlementNegotiationAttempt.predecessor_id == attempt.id
            )
        )
        if next_attempt is None:
            next_selection = SettlementScenarioSelection(
                id=uuid4(),
                case_id=case.id,
                user_id=user.id,
                user_id_snapshot=user.id,
                idempotency_key=uuid4(),
                request_sha256=hashlib.sha256(
                    f"{attempt.id}:{attempt.attempt_ordinal + 1}".encode()
                ).hexdigest(),
                run_id=selection.run_id,
                scenario_id=selection.scenario_id,
                scenario_result_json=deepcopy(
                    (attempt.frozen_snapshot_json or attempt.snapshot_json)["scenario"]["result"]
                ),
                profile_revision=attempt.snapshot_json["revisions"]["profile"],
                settlement_revision=attempt.snapshot_json["revisions"]["settlement"],
            )
            db.add(next_selection)
            db.flush()
            next_attempt = SettlementNegotiationAttempt(
                id=uuid4(),
                case_id=case.id,
                selection_id=next_selection.id,
                predecessor_id=attempt.id,
                attempt_ordinal=attempt.attempt_ordinal + 1,
                snapshot_json=deepcopy(attempt.frozen_snapshot_json or attempt.snapshot_json),
                editable_state_json=deepcopy(attempt.editable_state_json),
            )
            if attempt.editable_state_json.get("sent_offer_mode") == "modified":
                next_attempt.editable_state_json["sent_offer_mode"] = "unchanged"
                next_attempt.editable_state_json["modified_offer_reviewed"] = False
            db.add(next_attempt)
            next_response = SettlementOfferResponse(
                id=uuid4(),
                case_id=case.id,
                selection_id=next_selection.id,
                user_id=user.id,
                user_id_snapshot=user.id,
            )
            db.add(next_response)
            db.flush()
            if (
                attempt.editable_state_json.get("sent_offer_mode") == "modified"
                and attempt.editable_state_json.get("modified_offer_reviewed")
            ):
                source_rows = db.execute(
                    select(SettlementOfferResponseAttachment)
                    .where(
                        SettlementOfferResponseAttachment.response_id == response_record.id,
                        SettlementOfferResponseAttachment.kind.in_(("modified_docx", "modified_xlsx")),
                    )
                ).scalars().all()
                source_kinds = {
                    "modified_docx": "modified_source_docx",
                    "modified_xlsx": "modified_source_xlsx",
                }
                for source in source_rows:
                    db.add(
                        SettlementOfferResponseAttachment(
                            response_id=next_response.id,
                            document_id=source.document_id,
                            kind=source_kinds[source.kind],
                            filename=source.filename,
                        )
                    )
            try:
                db.commit()
                db.refresh(next_selection)
                db.refresh(next_attempt)
            except IntegrityError:
                db.rollback()
                next_attempt = db.scalar(
                    select(SettlementNegotiationAttempt).where(
                        SettlementNegotiationAttempt.predecessor_id == attempt.id
                    )
                )
                if next_attempt is None:
                    raise HTTPException(
                        status_code=409,
                        detail="A next attempt could not be created from the current negotiation state.",
                    )
            except SQLAlchemyError as error:
                db.rollback()
                logger.error("Next negotiation attempt could not be created (%s).", type(error).__name__)
                raise HTTPException(
                    status_code=503,
                    detail="The previous attempt remains saved, but the next attempt could not be created.",
                ) from error
        response.headers["Cache-Control"] = "no-store"
        return {
            "next_step": "next_attempt",
            "selection_id": str(next_attempt.selection_id),
            "attempt_ordinal": next_attempt.attempt_ordinal,
        }
    response.headers["Cache-Control"] = "no-store"
    return {"next_step": "final_checklist"}
