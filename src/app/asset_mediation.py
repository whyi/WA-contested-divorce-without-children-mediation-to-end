"""Persist the demo-aligned response workflow for saved overview scenarios."""

import hashlib
import json
import logging
from copy import deepcopy
from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID, uuid4

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.asset_overview import AssetOverviewRead, OverviewScenarioExport
from app.attachment_limits import FREE_ATTACHMENT_LIMIT, attachment_limit, enforce_attachment_quota
from app.config import get_settings
from app.auth_routes import require_current_user
from app.case_access import resolve_case_access
from app.case_lifecycle import close_case_record, require_attempts_editable
from app.database import get_db
from app.deletion import require_scope_active
from app.failure_logging import log_failure_event
from app.materials import _finish_overwrite
from app.models import (
    Case, Document, SettlementNegotiationAttempt, SettlementScenarioRun,
    SettlementScenarioSelection, User,
)
from app.settlement_routes import _require_real_case_exports
from app.storage import ObjectStorage
from app.validation import UploadValidationError, validate_upload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cases/{case_id}/asset-mediation", tags=["asset mediation"])
KEY = "asset_mediation"
storage = ObjectStorage()


class MediationState(BaseModel):
    revision: int = 0
    attempt_ordinal: int
    attempt_limit: int
    sent: bool = False
    outcome: Literal["counteroffer", "rejected", "accepted"] | None = None
    notes: str = ""
    document_ids: list[UUID] = Field(default_factory=list)
    sent_filenames: list[str] = Field(default_factory=list)
    selection: OverviewScenarioExport | None = None
    downloaded_formats: list[Literal["docx", "xlsx"]] = Field(default_factory=list)
    stopped: bool = False
    completed: bool = False
    accepted_document_ids: list[UUID] = Field(default_factory=list)
    attempts_locked: bool = False


class MediationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_revision: int = Field(ge=0, strict=True)
    attempt_ordinal: int = Field(ge=1, strict=True)
    action: Literal["sent", "response", "continue", "stop", "complete"]
    selection: OverviewScenarioExport | None = None
    outcome: Literal["counteroffer", "rejected", "accepted"] | None = None
    notes: str = Field(default="", max_length=20000)
    document_ids: list[UUID] = Field(default_factory=list, max_length=10)
    confirm: bool = False


def latest_attempt(db: Session, case_id: UUID) -> SettlementNegotiationAttempt | None:
    return db.scalar(select(SettlementNegotiationAttempt).where(
        SettlementNegotiationAttempt.case_id == case_id,
    ).order_by(SettlementNegotiationAttempt.attempt_ordinal.desc()).limit(1))


def _case(
    db: Session,
    user: User,
    case_id: UUID,
    *,
    write: bool = False,
    allow_locked_attempts: bool = False,
) -> Case:
    case = db.scalar(select(Case).where(Case.id == case_id).with_for_update())
    membership = resolve_case_access(db, case_id, user.id)
    if case is None or membership is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    if membership.role != "owner":
        raise HTTPException(status_code=403, detail="Only the case owner can record mediation responses.")
    require_scope_active(db, "case", case_id)
    if write and not allow_locked_attempts:
        require_attempts_editable(case)
    return case


def read_state(db: Session, case: Case, ordinal: int) -> MediationState:
    saved = (case.metadata_json or {}).get(KEY, {}).get(str(ordinal), {})
    return MediationState.model_validate({
        **saved, "attempt_ordinal": ordinal,
        "attempt_limit": 1 if attachment_limit(db, case.id) == FREE_ATTACHMENT_LIMIT else 3,
        "attempts_locked": getattr(case, "attempts_locked_at", None) is not None,
    })


def _save(case: Case, state: MediationState) -> None:
    metadata = dict(case.metadata_json or {})
    metadata[KEY] = {**metadata.get(KEY, {}), str(state.attempt_ordinal): state.model_dump(mode="json")}
    case.metadata_json = metadata


def record_download(db: Session, case: Case, selection: OverviewScenarioExport, format: Literal["docx", "xlsx"]) -> None:
    require_attempts_editable(case)
    state = read_state(db, case, selection.attempt_ordinal)
    if state.sent:
        if state.selection != selection:
            raise HTTPException(status_code=409, detail="The sent attempt's dates and scenario are read-only.")
        return
    if state.selection != selection:
        state.downloaded_formats = []
    state.selection = selection
    state.downloaded_formats = sorted(set([*state.downloaded_formats, format]))
    state.revision += 1
    _save(case, state)
    db.commit()


def _link_response_file(db: Session, case: Case, ordinal: int, document: Document, previous_id: UUID | None) -> MediationState:
    state = read_state(db, case, ordinal)
    ids = state.accepted_document_ids if state.outcome == "accepted" else state.document_ids
    ids = list(dict.fromkeys([*(item for item in ids if item != previous_id), document.id]))
    if state.outcome == "accepted":
        state.accepted_document_ids = ids
    else:
        state.document_ids = ids
    state.revision += 1
    _save(case, state)
    db.commit()
    return state


def _new_attempt(
    db: Session, case: Case, user: User, ordinal: int, selection: OverviewScenarioExport,
    predecessor: SettlementNegotiationAttempt | None,
) -> SettlementNegotiationAttempt:
    result = {"source": "saved_asset_overview", "selection": selection.model_dump(mode="json")}
    run = SettlementScenarioRun(
        id=uuid4(), case_id=case.id, user_id=user.id, user_id_snapshot=user.id,
        profile_revision=case.profile_revision, settlement_revision=case.settlement_revision,
        objective="User-selected saved balance date-range comparison",
        axes_json=result, scenario_results_json=[result], input_fact_ids=[],
    )
    db.add(run)
    db.flush()
    selected = SettlementScenarioSelection(
        id=uuid4(), case_id=case.id, user_id=user.id, user_id_snapshot=user.id,
        idempotency_key=uuid4(), request_sha256=hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest(),
        run_id=run.id, scenario_id=f"overview-{selection.community_share_bps}",
        scenario_result_json=result, profile_revision=case.profile_revision,
        settlement_revision=case.settlement_revision,
    )
    db.add(selected)
    db.flush()
    attempt = SettlementNegotiationAttempt(
        id=uuid4(), case_id=case.id, selection_id=selected.id,
        predecessor_id=predecessor.id if predecessor is not None else None,
        attempt_ordinal=ordinal, revision=0, proposal_version_ordinal=0,
        snapshot_json={
            "schema_version": 1, "case_id": str(case.id),
            "revisions": {"profile": case.profile_revision, "settlement": case.settlement_revision},
            "overview_selection": selection.model_dump(mode="json"),
            "case_profile": {
                "metadata": deepcopy(case.metadata_json or {}),
                "property_assets": deepcopy(case.property_assets),
                "relationship_milestones": deepcopy(case.relationship_milestones),
                "asset_liability_inventory": deepcopy(case.asset_liability_inventory),
            },
        },
        editable_state_json={},
    )
    db.add(attempt)
    return attempt


@router.get("/{ordinal}", response_model=MediationState)
def get_mediation_state(
    case_id: UUID, ordinal: int, response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MediationState:
    try:
        _require_real_case_exports()
        case = _case(db, user, case_id)
        latest = latest_attempt(db, case_id)
        if ordinal < 1 or ordinal > (latest.attempt_ordinal if latest is not None else 1):
            raise HTTPException(status_code=404, detail="Attempt not found.")
        response.headers["Cache-Control"] = "no-store"
        return read_state(db, case, ordinal)
    except SQLAlchemyError as error:
        db.rollback()
        log_failure_event(logger, "mediation_state_read_failed", error)
        raise HTTPException(status_code=503, detail="Mediation response could not be loaded. Please retry.") from error
    except ValueError as error:
        log_failure_event(logger, "mediation_state_invalid", error)
        raise HTTPException(status_code=503, detail="Saved mediation response is invalid. Contact support before continuing.") from error


@router.post("", response_model=MediationState)
def update_mediation_state(
    case_id: UUID, payload: MediationUpdate, response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MediationState:
    try:
        _require_real_case_exports()
        case = _case(
            db,
            user,
            case_id,
            write=True,
            allow_locked_attempts=payload.action == "complete",
        )
        response.headers["Cache-Control"] = "no-store"
        state = read_state(db, case, payload.attempt_ordinal)
        if (payload.action == "complete" and state.completed) or (payload.action == "stop" and state.stopped):
            return state
        if payload.action == "complete":
            require_attempts_editable(case)
        if case.closed_at is not None or case.status == "finalized":
            raise HTTPException(status_code=409, detail="This case is closed or read-only.")
        latest = latest_attempt(db, case_id)
        ordinal = latest.attempt_ordinal if latest is not None else 1
        if payload.action == "sent" and state.sent:
            return state
        if payload.action == "continue" and latest is not None and latest.predecessor_id is not None and ordinal == payload.attempt_ordinal + 1:
            return read_state(db, case, ordinal)
        if payload.attempt_ordinal != ordinal:
            raise HTTPException(status_code=409, detail="Only the current attempt can receive a response.")
        if payload.expected_revision != state.revision:
            raise HTTPException(status_code=409, detail="Mediation response changed. Reload and retry.")
        if state.stopped:
            raise HTTPException(status_code=409, detail="This workflow has been stopped.")
        if payload.action == "sent":
            if not payload.confirm or payload.selection is None or payload.selection != state.selection:
                raise HTTPException(status_code=409, detail="Confirm the exact scenario you downloaded and delivered to your mediator.")
            if set(state.downloaded_formats) != {"docx", "xlsx"}:
                raise HTTPException(status_code=409, detail="Download both Word and Excel for the current scenario before confirming delivery.")
            saved = AssetOverviewRead.model_validate((case.metadata_json or {}).get("asset_overview", {}))
            if saved.revision != payload.selection.expected_revision:
                raise HTTPException(status_code=409, detail="Asset values changed. Download the updated documents first.")
            payload.selection.snapshots(saved.overview)
            if latest is not None and (latest.frozen_at is not None or latest.finalized_at is not None):
                raise HTTPException(status_code=409, detail="This attempt is already read-only.")
            if latest is None:
                latest = _new_attempt(db, case, user, ordinal, payload.selection, None)
            state.sent = True
            state.sent_filenames = ["cr2a-proposal-draft.docx", "property-schedule-draft.xlsx"]
            now = datetime.now(UTC)
            latest.sent_confirmed_at = now
            latest.frozen_at = now
            latest.revision += 1
            latest.frozen_snapshot_json = {
                **deepcopy(latest.snapshot_json),
                "overview_selection": payload.selection.model_dump(mode="json"),
                "case_profile": {
                    "metadata": deepcopy(case.metadata_json or {}),
                    "property_assets": deepcopy(case.property_assets),
                    "relationship_milestones": deepcopy(case.relationship_milestones),
                    "asset_liability_inventory": deepcopy(case.asset_liability_inventory),
                },
                "sent_confirmed_at": now.isoformat(),
                "externally_sent": False,
                "user_reported_mediator_delivery": True,
            }
        else:
            if not state.sent:
                raise HTTPException(status_code=409, detail="Confirm mediator delivery before recording a response.")
            if payload.action == "response":
                if payload.outcome is None:
                    raise HTTPException(status_code=422, detail="Choose the response you received.")
                for document_id in payload.document_ids:
                    document = db.get(Document, document_id)
                    if document is None or document.case_id != case.id:
                        raise HTTPException(status_code=404, detail="Counteroffer file not found.")
                    require_scope_active(db, "document", document_id)
                state.outcome, state.notes = payload.outcome, payload.notes
                state.document_ids = list(dict.fromkeys(payload.document_ids))
            elif payload.action == "complete":
                if state.outcome != "accepted":
                    raise HTTPException(status_code=409, detail="An accepted response is required.")
                if not payload.confirm:
                    raise HTTPException(status_code=422, detail="Confirm completion of this product workflow.")
                state.completed = True
                close_case_record(db, case, user.id, "accepted")
                case.status = "finalized"
                state.attempts_locked = True
            elif payload.action == "stop":
                if state.outcome != "rejected" or not payload.confirm:
                    raise HTTPException(status_code=409, detail="Confirm stopping after the rejection.")
                state.stopped = True
                close_case_record(db, case, user.id, "stopped")
            elif payload.action == "continue":
                if state.outcome not in {"counteroffer", "rejected"} or state.selection is None:
                    raise HTTPException(status_code=409, detail="Record a counteroffer or rejection first.")
                if ordinal >= state.attempt_limit:
                    raise HTTPException(status_code=402, detail="Your plan's attempt limit is reached. Purchase credits to continue.")
                if state.outcome == "counteroffer" and not state.notes.strip() and not state.document_ids:
                    raise HTTPException(status_code=422, detail="Add counteroffer notes or a file before continuing.")
                next_selection = state.selection.model_copy(update={"attempt_ordinal": ordinal + 1})
                _new_attempt(db, case, user, ordinal + 1, next_selection, latest)
                state = MediationState(
                    attempt_ordinal=ordinal + 1, attempt_limit=state.attempt_limit,
                    notes=state.notes, document_ids=state.document_ids,
                )
        state.revision += 1
        _save(case, state)
        db.commit()
        response.headers["Cache-Control"] = "no-store"
        return state
    except HTTPException:
        db.rollback()
        raise
    except ValueError as error:
        db.rollback()
        log_failure_event(logger, "mediation_response_invalid", error)
        raise HTTPException(status_code=422, detail="Mediation response data is invalid. Reload and retry.") from error
    except SQLAlchemyError as error:
        db.rollback()
        log_failure_event(logger, "mediation_response_save_failed", error)
        raise HTTPException(status_code=503, detail="Mediation response was not saved. Your work is preserved; retry.") from error


@router.post("/{ordinal}/files/{document_id}", status_code=201)
async def upload_counteroffer(
    case_id: UUID, ordinal: int, document_id: UUID,
    upload: Annotated[UploadFile, File()],
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
    overwrite_document_id: Annotated[UUID | None, Form()] = None,
) -> dict[str, object]:
    _require_real_case_exports()
    filename = upload.filename or ""
    extension = filename.rpartition(".")[2].lower()
    content = b""
    try:
        if not filename or len(filename) > 1024 or any(ord(char) < 32 or ord(char) == 127 for char in filename):
            raise HTTPException(status_code=422, detail="Choose a file with a valid original filename.")
        if extension not in {"pdf", "docx", "xlsx"}:
            raise HTTPException(status_code=415, detail="Choose a PDF, DOCX or XLSX counteroffer.")
        content = await upload.read(get_settings().max_upload_bytes + 1)
        validate_upload(filename, content, extension, get_settings().max_upload_bytes)
    except UploadValidationError as error:
        raise HTTPException(status_code=413 if len(content) > get_settings().max_upload_bytes else 415, detail=str(error)) from error
    finally:
        await upload.close()
    key = None
    stored = False
    try:
        case = _case(db, user, case_id, write=True)
        latest = latest_attempt(db, case_id)
        state = read_state(db, case, ordinal)
        if case.closed_at is not None or case.status == "finalized" or state.attempts_locked or state.stopped:
            raise HTTPException(status_code=409, detail="This case workflow is read-only.")
        if latest is None or latest.attempt_ordinal != ordinal or not state.sent or state.outcome not in {"counteroffer", "accepted"}:
            raise HTTPException(status_code=409, detail="Select Counteroffer received or Offer accepted on the current attempt before attaching a file.")
        digest = hashlib.sha256(content).hexdigest()
        existing = db.get(Document, document_id)
        if existing is not None:
            if existing.case_id != case_id:
                raise HTTPException(status_code=404, detail="File not found.")
            if existing.original_filename != filename or existing.sha256 != digest:
                raise HTTPException(status_code=409, detail="Reselect the original counteroffer file to retry.")
            require_scope_active(db, "document", document_id)
            previous_id = existing.overwrite_document_id
            _finish_overwrite(db, user, existing)
            linked = _link_response_file(db, case, ordinal, existing, previous_id)
            return {"id": str(existing.id), "original_filename": filename, "state": linked.model_dump(mode="json")}
        duplicate = db.scalars(select(Document).where(
            Document.case_id == case_id, Document.original_filename == filename,
        ).order_by(Document.overwrite_document_id.is_(None), Document.created_at).limit(1)).first()
        if duplicate is not None:
            if duplicate.overwrite_document_id is not None:
                raise HTTPException(status_code=409, detail="Retry the unfinished overwrite first.")
            if duplicate.id != overwrite_document_id:
                raise HTTPException(status_code=409, detail={
                    "code": "filename_conflict", "filename": filename, "document_id": str(duplicate.id),
                })
        elif overwrite_document_id is not None:
            raise HTTPException(status_code=409, detail="The overwrite target changed. Reload and retry.")
        enforce_attachment_quota(db, case_id, incoming=0 if duplicate is not None else 1)
        media_type = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }[extension]
        key = f"{case_id}/{document_id}.{extension}"
        storage.put(key, content, media_type)
        document = Document(
            id=document_id, case_id=case_id, object_key=key, original_filename=filename,
            extension=extension, media_type=media_type, size_bytes=len(content), sha256=digest,
            overwrite_document_id=duplicate.id if duplicate is not None else None,
        )
        db.add(document)
        db.commit()
        stored = True
        _finish_overwrite(db, user, document)
        linked = _link_response_file(db, case, ordinal, document, duplicate.id if duplicate is not None else None)
        return {"id": str(document.id), "original_filename": filename, "state": linked.model_dump(mode="json")}
    except HTTPException:
        db.rollback()
        raise
    except (SQLAlchemyError, BotoCoreError, ClientError, RuntimeError) as error:
        db.rollback()
        log_failure_event(logger, "mediation_counteroffer_upload_failed", error)
        raise HTTPException(status_code=503, detail="Counteroffer upload failed. Reselect the same file to retry.") from error
    finally:
        if key is not None and not stored:
            try:
                storage.delete_all_versions(key)
            except (BotoCoreError, ClientError, RuntimeError) as error:
                log_failure_event(logger, "mediation_counteroffer_cleanup_failed", error, severity="SEV1")
