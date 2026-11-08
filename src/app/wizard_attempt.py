import logging
from dataclasses import dataclass, field
from datetime import date as Date
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID, uuid5

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth_routes import require_current_user
from app.case_lifecycle import lifecycle_write_allowed
from app.database import get_db
from app.failure_logging import log_failure_event
from app.models import (
    Case,
    SettlementLedgerEvent,
    SettlementNegotiationAttempt,
    SettlementScenarioRun,
    SettlementScenarioSelection,
    User,
)
from app.offer_response import (
    NegotiationMilestone,
    OfferAttemptStateUpdate,
    _create_initial_attempt,
)
from app.settlement_planning import (
    LedgerEvent,
    RelationshipWindow,
    ScenarioAxes,
    calculate_scenario,
    generate_scenarios,
)
from app.settlement_routes import (
    LedgerEventCreate,
    ScenarioSelectRequest,
    _asset_ledgers,
    _authorize_case,
    _lock_case,
    _request_sha256,
)
from app.wizard_intake import WizardFinanceEntry, WizardIntakeDraft

logger = logging.getLogger(__name__)
router = APIRouter(tags=["wizard attempt"])

REPORT_KEY = "wizard_attempt"
MAX_TERMS = 80
MAX_TERM_LENGTH = 2_000
WINDOW_LABEL = "As entered in your case information"
OBJECTIVE = "Values exactly as entered in the case information wizard."
MILESTONES = (
    ("cohabitation", "Cohabitation start"),
    ("marriage", "Marriage"),
    ("separation", "Separation"),
    ("petition", "Petition filed"),
)
ROLE_LABELS = {"petitioner": "Petitioner", "respondent": "Respondent"}
OTHER_ROLE = {"petitioner": "Respondent", "respondent": "Petitioner"}


@dataclass(frozen=True)
class PlannedAsset:
    asset_id: UUID
    event_id: UUID
    name: str
    kind: Literal["asset", "debt"]
    amount_cents: int
    effective_date: Date
    note: str


@dataclass
class AttemptPlan:
    assets: list[PlannedAsset] = field(default_factory=list)
    needs: list[str] = field(default_factory=list)
    axes: dict | None = None
    offer_from: str = ""
    offer_to: str = ""
    milestones: list[dict] = field(default_factory=list)
    proposal_terms: list[str] = field(default_factory=list)
    report: dict = field(default_factory=dict)


def _entry_name(entry: WizardFinanceEntry, position: int) -> str:
    label = entry.description.strip() or entry.category.strip()
    if not label:
        label = f"{'Debt' if entry.kind == 'debt' else 'Asset'} {position}"
    return label[:200]


def _entry_note(entry: WizardFinanceEntry) -> str:
    parts = [("Category", entry.category), ("Owners", entry.owners)]
    parts.append(("Holding", entry.holding or ""))
    parts.append(("Acquisition", entry.acquisition_method or ""))
    details = "; ".join(f"{name}: {value.strip()}" for name, value in parts if value.strip())
    prefix = "Entered in your case information."
    return f"{prefix} {details}"[:1000] if details else prefix


def _cents(amount: Decimal) -> int:
    return int(amount.scaleb(2).to_integral_exact())


def _terms(draft: WizardIntakeDraft) -> tuple[list[str], list[dict]]:
    candidates: list[tuple[str, str, str]] = []
    for issue in draft.issues:
        topic, outcome = issue.topic.strip(), issue.outcome.strip()
        if not topic and not outcome:
            continue
        body = f"{topic}: {outcome}" if topic and outcome else topic or outcome
        candidates.append(("issue", topic or outcome, f"Issue — {body}"))
    for agreement in draft.agreements:
        summary = agreement.summary.strip()
        if not summary:
            continue
        suffix = f" ({agreement.date.isoformat()})" if agreement.date else ""
        candidates.append(("agreement", summary, f"Agreement — {summary}{suffix}"))
    terms: list[str] = []
    excluded: list[dict] = []
    for kind, label, term in candidates:
        if len(term) > MAX_TERM_LENGTH:
            reason = "Too long for a proposal term (2,000 characters)."
        elif len(terms) >= MAX_TERMS:
            reason = "The proposal supports at most 80 terms."
        else:
            terms.append(term)
            continue
        excluded.append({"kind": kind, "label": label[:120], "reason": reason})
    return terms, excluded


def plan_attempt(
    case_id: UUID,
    draft: WizardIntakeDraft,
    saved_on: Date,
    wizard_revision: int,
) -> AttemptPlan:
    plan = AttemptPlan()
    included: list[dict] = []
    excluded: list[dict] = []
    for position, entry in enumerate(draft.finances, start=1):
        name = _entry_name(entry, position)
        if entry.amount is None:
            excluded.append({"kind": entry.kind, "label": name, "reason": "No amount was entered."})
            continue
        if entry.amount <= 0:
            excluded.append({"kind": entry.kind, "label": name, "reason": "The amount is zero."})
            continue
        planned = PlannedAsset(
            asset_id=uuid5(case_id, f"wizard-asset:{entry.id}"),
            event_id=uuid5(case_id, f"wizard-event:{entry.id}"),
            name=name,
            kind=entry.kind,
            amount_cents=_cents(entry.amount),
            effective_date=entry.acquired_date or saved_on,
            note=_entry_note(entry),
        )
        plan.assets.append(planned)
        included.append({"label": name, "kind": entry.kind, "amount_cents": planned.amount_cents})

    dates = draft.dates
    start_source = "marriage" if dates.marriage.date else "cohabitation"
    start = dates.marriage.date or dates.cohabitation.date
    separation = dates.separation.date
    if not plan.assets:
        plan.needs.append("At least one asset or debt with an amount greater than zero.")
    if start is None:
        plan.needs.append("A marriage or cohabitation start date.")
    if separation is None:
        plan.needs.append("A separation date.")
    if start and separation and start > separation:
        plan.needs.append("The start date must not be after the separation date.")

    plan.offer_from = ROLE_LABELS.get(draft.role or "", "")
    plan.offer_to = OTHER_ROLE.get(draft.role or "", "")
    plan.milestones = [
        {"name": label, "date": getattr(dates, key).date.isoformat()}
        for key, label in MILESTONES
        if getattr(dates, key).date
    ]
    plan.proposal_terms, excluded_terms = _terms(draft)
    excluded.extend(excluded_terms)

    if not plan.needs and start and separation:
        marriage = start_source == "marriage"
        plan.axes = ScenarioAxes(
            relationship_windows=[
                RelationshipWindow(
                    id="wizard-entered",
                    label=WINDOW_LABEL,
                    relationship_type="marriage_only" if marriage else "alternate",
                    start_date=start,
                    separation_date=separation,
                    assumption_note=(
                        "The start is the marriage date you entered."
                        if marriage
                        else "The start is the cohabitation date you entered. "
                        "It is an entered date, not a legal classification."
                    ),
                )
            ],
            tracing_methods=["explicit"],
            community_share_bps=[5000],
        ).model_dump(mode="json")

    plan.report = {
        "wizard_revision": wizard_revision,
        "role": draft.role,
        "included": included,
        "excluded": excluded,
        "dates": {
            "start": start.isoformat() if start else None,
            "start_source": start_source if start else None,
            "separation": separation.isoformat() if separation else None,
        },
        "milestones": len(plan.milestones),
        "terms": len(plan.proposal_terms),
    }
    return plan


class WizardAttemptRead(BaseModel):
    status: Literal["created", "exists", "needs_information"]
    attempt_exists: bool
    needs: list[str]
    report: dict | None


def _attempt_exists(db: Session, case_id: UUID) -> bool:
    return (
        db.scalar(
            select(SettlementNegotiationAttempt.id)
            .where(SettlementNegotiationAttempt.case_id == case_id)
            .limit(1)
        )
        is not None
    )


def _stored_report(case: Case) -> dict | None:
    report = (case.metadata_json or {}).get(REPORT_KEY)
    return report if isinstance(report, dict) else None


def _draft_of(case: Case) -> WizardIntakeDraft:
    try:
        return WizardIntakeDraft.model_validate(case.wizard_intake_json or {})
    except ValidationError as error:
        logger.error("Stored wizard-intake draft failed schema validation.")
        raise HTTPException(
            status_code=503,
            detail="The saved wizard draft is unavailable. Please contact support.",
        ) from error


def _plan_for(db: Session, case: Case) -> AttemptPlan:
    saved_on = (case.updated_at or case.created_at).date()
    plan = plan_attempt(case.id, _draft_of(case), saved_on, case.wizard_intake_revision)
    has_ledger = db.scalar(
        select(SettlementLedgerEvent.id).where(SettlementLedgerEvent.case_id == case.id).limit(1)
    )
    if has_ledger is not None and not plan.needs:
        plan.needs.append(
            "This case already has settlement ledger entries. Existing attempt data is preserved; "
            "a new wizard-seeded attempt cannot be created."
        )
    return plan


@router.get("/cases/{case_id}/wizard-attempt", response_model=WizardAttemptRead)
def read_wizard_attempt(
    case_id: UUID,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> WizardAttemptRead:
    response.headers["Cache-Control"] = "no-store"
    try:
        case = _authorize_case(db, user, case_id, write=False)
        exists = _attempt_exists(db, case_id)
        needs = [] if exists else _plan_for(db, case).needs
        return WizardAttemptRead(
            status="exists" if exists else "needs_information" if needs else "created",
            attempt_exists=exists,
            needs=needs,
            report=_stored_report(case),
        )
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        log_failure_event(logger, "wizard_attempt_read_failed", error)
        raise HTTPException(status_code=503, detail="The wizard attempt is unavailable.") from error


@router.post("/cases/{case_id}/wizard-attempt", response_model=WizardAttemptRead)
def create_wizard_attempt(
    case_id: UUID,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> WizardAttemptRead:
    response.headers["Cache-Control"] = "no-store"
    try:
        _authorize_case(db, user, case_id, write=True)
        case = _lock_case(db, case_id)
        if not lifecycle_write_allowed(case, f"/cases/{case_id}/wizard-attempt"):
            raise HTTPException(
                status_code=409,
                detail="This case is closed and read-only. Reopen it to make changes.",
            )
        if _attempt_exists(db, case_id):
            db.rollback()
            return WizardAttemptRead(
                status="exists", attempt_exists=True, needs=[], report=_stored_report(case)
            )
        plan = _plan_for(db, case)
        if plan.needs or plan.axes is None:
            db.rollback()
            return WizardAttemptRead(
                status="needs_information",
                attempt_exists=False,
                needs=plan.needs,
                report=plan.report,
            )
        _write_attempt(db, case, user, plan)
        db.commit()
        return WizardAttemptRead(
            status="created", attempt_exists=True, needs=[], report=_stored_report(case)
        )
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as error:
        db.rollback()
        log_failure_event(logger, "wizard_attempt_conflict", error)
        raise HTTPException(
            status_code=409,
            detail="The first attempt is already being created. Reload and retry.",
        ) from error
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    except SQLAlchemyError as error:
        db.rollback()
        log_failure_event(logger, "wizard_attempt_create_failed", error)
        raise HTTPException(
            status_code=503, detail="The first attempt could not be created. Please try again."
        ) from error


def _write_attempt(db: Session, case: Case, user: User, plan: AttemptPlan) -> None:
    profile_revision = case.profile_revision
    base_revision = case.settlement_revision
    for offset, asset in enumerate(plan.assets, start=1):
        event = LedgerEvent(
            id=asset.event_id,
            effective_date=asset.effective_date,
            sequence_number=0,
            event_type="valuation",
            amount_cents=asset.amount_cents,
            provenance="user_reported",
            note=asset.note,
        )
        request = LedgerEventCreate(
            idempotency_key=uuid5(case.id, f"wizard-ledger-key:{asset.asset_id}"),
            expected_profile_revision=profile_revision,
            expected_settlement_revision=base_revision + offset - 1,
            asset_id=asset.asset_id,
            asset_name=asset.name,
            asset_kind=asset.kind,
            event=event,
        )
        db.add(
            SettlementLedgerEvent(
                id=event.id,
                case_id=case.id,
                asset_id=asset.asset_id,
                asset_name=asset.name,
                asset_kind=asset.kind,
                effective_date=event.effective_date,
                sequence_number=0,
                event_json=event.model_dump(mode="json"),
                user_id=user.id,
                user_id_snapshot=user.id,
                idempotency_key=request.idempotency_key,
                request_sha256=_request_sha256(request),
                profile_revision=profile_revision,
                settlement_revision=base_revision + offset,
            )
        )
    case.settlement_revision = base_revision + len(plan.assets)
    db.flush()

    axes = ScenarioAxes.model_validate(plan.axes)
    scenarios = generate_scenarios(axes)
    if len(scenarios) != 1:
        raise ValueError("The entered information must produce exactly one starting scenario.")
    calculated = calculate_scenario(scenarios[0], _asset_ledgers(db, case.id))
    run = SettlementScenarioRun(
        id=uuid5(case.id, "wizard-run"),
        case_id=case.id,
        user_id=user.id,
        user_id_snapshot=user.id,
        profile_revision=profile_revision,
        settlement_revision=case.settlement_revision,
        objective=OBJECTIVE,
        axes_json=plan.axes,
        scenario_results_json=[calculated.model_dump(mode="json")],
        input_fact_ids=[],
    )
    db.add(run)
    db.flush()

    selection_request = ScenarioSelectRequest(
        idempotency_key=uuid5(case.id, "wizard-selection-key"),
        expected_profile_revision=profile_revision,
        expected_settlement_revision=case.settlement_revision,
        run_id=run.id,
        scenario_id=calculated.scenario.id,
    )
    selection = SettlementScenarioSelection(
        case_id=case.id,
        user_id=user.id,
        user_id_snapshot=user.id,
        idempotency_key=selection_request.idempotency_key,
        request_sha256=_request_sha256(selection_request),
        run_id=run.id,
        scenario_id=calculated.scenario.id,
        scenario_result_json=calculated.model_dump(mode="json"),
        profile_revision=profile_revision,
        settlement_revision=case.settlement_revision,
    )
    db.add(selection)
    db.flush()
    attempt = _create_initial_attempt(db, case, selection, user)

    state = OfferAttemptStateUpdate(
        expected_revision=0,
        offer_from=plan.offer_from,
        offer_to=plan.offer_to,
        scenario_assumptions=ScenarioAxes.model_validate(
            attempt.editable_state_json["scenario_assumptions"]
        ),
        milestones=[NegotiationMilestone.model_validate(item) for item in plan.milestones],
        proposal_terms=plan.proposal_terms,
    )
    attempt.editable_state_json = state.model_dump(mode="json", exclude={"expected_revision"})
    case.metadata_json = {**(case.metadata_json or {}), REPORT_KEY: plan.report}
    db.flush()
