import hashlib
import hmac
import json
import logging
from collections import defaultdict
from datetime import UTC, date, datetime
from typing import Annotated, Literal
from uuid import UUID, uuid4

from botocore.exceptions import BotoCoreError
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth_routes import require_current_user
from app.config import Settings, get_settings
from app.database import get_db
from app.models import (
    Case,
    CaseMembership,
    CaseProfileFact,
    CaseProfileFactEvent,
    Document,
    ExportDeliveryEvent,
    SettlementLedgerEvent,
    SettlementNegotiationAttempt,
    SettlementOfferResponse,
    SettlementOfferResponseAttachment,
    SettlementPlanningConsentEvent,
    SettlementScenarioRun,
    SettlementScenarioSelection,
    User,
)
from app.export_delivery import (
    ExportDeliveryError,
    ExportFile,
    deliver_export_files,
)
from app.offer_documents import (
    MediationOfferTerms,
    render_mediation_offer_docx,
    render_property_schedule_xlsx,
)
from app.settlement_ai import ScenarioRankingResult, rank_settlement_scenarios
from app.settlement_planning import (
    AssetLedger,
    LedgerEvent,
    RelationshipWindow,
    ScenarioAxes,
    SettlementScenarioResult,
    calculate_scenario,
    generate_scenarios,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cases/{case_id}/settlement-planning", tags=["settlement planning"])
demo_export_router = APIRouter(tags=["demo exports"])
SETTLEMENT_CONSENT_NOTICE_VERSION = "settlement-planning-v1"
MAX_LEDGER_EVENTS_PER_CASE = 25_000
DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class ConsentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm: Literal[True]
    notice_version: Literal["settlement-planning-v1"]


class SettlementPlanningDisclosure(BaseModel):
    available: bool
    provider: str
    model_id: str | None
    region: str | None
    notice_version: str
    purpose: str
    data_sent: str
    data_handling_notice: str | None


class LedgerEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idempotency_key: UUID
    expected_profile_revision: int = Field(ge=0)
    expected_settlement_revision: int = Field(ge=0)
    asset_id: UUID
    asset_name: str = Field(min_length=1, max_length=200)
    asset_kind: Literal["asset", "debt"]
    event: LedgerEvent


class LedgerEventRead(BaseModel):
    id: UUID
    asset_id: UUID
    asset_name: str
    asset_kind: Literal["asset", "debt"]
    event: LedgerEvent
    settlement_revision: int


class SettlementPlanningStateRead(BaseModel):
    case_id: UUID
    consented: bool
    consent_notice_version: str | None
    profile_revision: int
    settlement_revision: int
    ledger_event_count: int


class ScenarioGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_profile_revision: int = Field(ge=0)
    expected_settlement_revision: int = Field(ge=0)
    objective: str = Field(min_length=1, max_length=2000)
    axes: ScenarioAxes


class SettlementScenariosRead(BaseModel):
    run_id: UUID
    profile_revision: int
    settlement_revision: int
    scenarios: list[SettlementScenarioResult]
    ranking: ScenarioRankingResult | None
    ranking_error: str | None


class ScenarioSelectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idempotency_key: UUID
    expected_profile_revision: int = Field(ge=0)
    expected_settlement_revision: int = Field(ge=0)
    run_id: UUID
    scenario_id: str = Field(min_length=1, max_length=80)


class ScenarioSelectionRead(BaseModel):
    selection_id: UUID
    run_id: UUID
    scenario_id: str
    profile_revision: int
    settlement_revision: int
    attempt_ordinal: int = 1


class OfferResponseHistoryAttachment(BaseModel):
    kind: Literal["sent_docx", "sent_xlsx", "counteroffer"]
    filename: str


class OfferResponseHistoryItem(BaseModel):
    selection_id: UUID
    scenario_id: str
    attempt_ordinal: int
    frozen: bool
    outcome: Literal["counteroffer", "rejected", "accepted"] | None
    attachments: list[OfferResponseHistoryAttachment]


class OfferCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    terms: MediationOfferTerms


class DemoExportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_date: date
    end_date: date
    community_share_bps: Literal[4500, 5000, 5500]

    @model_validator(mode="after")
    def validate_demo_dates(self) -> "DemoExportRequest":
        if self.start_date > self.end_date:
            raise ValueError("Start date must not follow the end date.")
        if self.start_date.year < 2020 or self.end_date.year > 2025:
            raise ValueError("Demo dates must be between 2020 and 2025.")
        return self


class OfferDelivery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: Literal["google_drive", "dropbox", "email"]
    confirm: Literal[True]
    idempotency_key: UUID
    recipient: EmailStr | None = None
    terms: MediationOfferTerms

    @model_validator(mode="after")
    def require_recipient_only_for_email(self) -> "OfferDelivery":
        if self.channel == "email" and self.recipient is None:
            raise ValueError("Confirm the email recipient before delivery.")
        if self.channel != "email" and self.recipient is not None:
            raise ValueError("An email recipient is only valid for email delivery.")
        return self


def _authorize_case(db: Session, user: User, case_id: UUID, *, write: bool) -> Case:
    membership = db.scalar(
        select(CaseMembership).where(
            CaseMembership.case_id == case_id,
            CaseMembership.user_id == user.id,
            CaseMembership.revoked_at.is_(None),
        )
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    if write and membership.role == "viewer":
        raise HTTPException(status_code=403, detail="Case is read-only.")
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    return case


def _lock_case(db: Session, case_id: UUID) -> Case:
    case = db.scalar(select(Case).where(Case.id == case_id).with_for_update())
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    return case


def _current_consent(
    db: Session,
    case_id: UUID,
    user_id: UUID,
) -> SettlementPlanningConsentEvent | None:
    return db.scalar(
        select(SettlementPlanningConsentEvent)
        .where(
            SettlementPlanningConsentEvent.case_id == case_id,
            SettlementPlanningConsentEvent.user_id_snapshot == user_id,
        )
        .order_by(
            SettlementPlanningConsentEvent.created_at.desc(),
            SettlementPlanningConsentEvent.id.desc(),
        )
        .limit(1)
    )


def _active_profile_facts(db: Session, case_id: UUID) -> list[CaseProfileFact]:
    facts = db.scalars(
        select(CaseProfileFact)
        .where(CaseProfileFact.case_id == case_id)
        .order_by(CaseProfileFact.profile_revision, CaseProfileFact.id)
    ).all()
    if not facts:
        return []
    events = db.scalars(
        select(CaseProfileFactEvent)
        .where(
            CaseProfileFactEvent.case_id == case_id,
            CaseProfileFactEvent.fact_id.in_([fact.id for fact in facts]),
        )
        .order_by(CaseProfileFactEvent.created_at, CaseProfileFactEvent.id)
    ).all()
    latest_event = {event.fact_id: event for event in events}
    active = []
    for fact in facts:
        disposition = latest_event.get(fact.id)
        if disposition is not None and disposition.action != "reinstated":
            continue
        document = db.get(Document, fact.source_document_id)
        if (
            document is not None
            and document.case_id == case_id
            and document.sha256 == fact.source_sha256
        ):
            active.append(fact)
    return active


def _fact_ids(facts: list[CaseProfileFact]) -> set[UUID]:
    return {fact.id for fact in facts}


def _check_fact_references(ids: list[UUID], available_ids: set[UUID]) -> None:
    if not set(ids).issubset(available_ids):
        raise HTTPException(
            status_code=422,
            detail="Ledger and scenario references must use currently active, source-backed case facts.",
        )


def _reviewed_fact_payload(facts: list[CaseProfileFact]) -> list[dict[str, object]]:
    return [
        {
            "id": fact.id,
            "field_key": fact.field_key,
            "value": fact.value,
            "source_document_id": fact.source_document_id,
            "source_quote": fact.source_quote,
            "source_page_number": fact.source_page_number,
        }
        for fact in facts
    ]


def _ledger_event_read(row: SettlementLedgerEvent) -> LedgerEventRead:
    return LedgerEventRead(
        id=row.id,
        asset_id=row.asset_id,
        asset_name=row.asset_name,
        asset_kind=row.asset_kind,
        event=LedgerEvent.model_validate(row.event_json),
        settlement_revision=row.settlement_revision,
    )


def _asset_ledgers(db: Session, case_id: UUID) -> list[AssetLedger]:
    rows = db.scalars(
        select(SettlementLedgerEvent)
        .where(SettlementLedgerEvent.case_id == case_id)
        .order_by(
            SettlementLedgerEvent.asset_id,
            SettlementLedgerEvent.effective_date,
            SettlementLedgerEvent.sequence_number,
        )
        .limit(MAX_LEDGER_EVENTS_PER_CASE + 1)
    ).all()
    if len(rows) > MAX_LEDGER_EVENTS_PER_CASE:
        raise HTTPException(status_code=413, detail="Settlement ledger exceeds the supported event limit.")
    grouped: dict[UUID, list[SettlementLedgerEvent]] = defaultdict(list)
    for row in rows:
        grouped[row.asset_id].append(row)
    try:
        return [
            AssetLedger(
                asset_id=asset_id,
                name=asset_rows[0].asset_name,
                kind=asset_rows[0].asset_kind,
                events=[LedgerEvent.model_validate(row.event_json) for row in asset_rows],
            )
            for asset_id, asset_rows in grouped.items()
        ]
    except ValueError as error:
        logger.exception("Persisted settlement ledger failed validation.")
        raise HTTPException(status_code=500, detail="The saved settlement ledger is invalid.") from error


def _check_revisions(
    case: Case,
    expected_profile_revision: int,
    expected_settlement_revision: int,
) -> None:
    if (
        case.profile_revision != expected_profile_revision
        or case.settlement_revision != expected_settlement_revision
    ):
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Case facts or settlement ledger changed. Reload and retry.",
                "profile_revision": case.profile_revision,
                "settlement_revision": case.settlement_revision,
            },
        )


def _request_sha256(payload: BaseModel) -> str:
    data = payload.model_dump(mode="json")
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _delivery_request_digest(payload: OfferDelivery) -> str:
    key = get_settings().auth_jwt_secret
    if not key:
        raise HTTPException(status_code=503, detail="Delivery audit protection is not configured.")
    data = payload.model_dump(mode="json")
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hmac.new(key.encode(), encoded.encode("utf-8"), hashlib.sha256).hexdigest()


def _require_real_case_exports() -> None:
    settings = get_settings()
    if not settings.auth_enabled or not settings.case_data_enabled or settings.demo_mode_enabled:
        raise HTTPException(
            status_code=503,
            detail="Case document exports are available only for authenticated real-case workflows.",
        )


def _demo_export_files(payload: DemoExportRequest) -> tuple[MediationOfferTerms, SettlementScenarioResult]:
    window = RelationshipWindow(
        id="fictional-demo",
        label="Fictional demo dates",
        relationship_type="alternate",
        start_date=payload.start_date,
        separation_date=payload.end_date,
        assumption_note="Fictional sample dates for a product preview; not a legal characterization.",
    )
    scenario = generate_scenarios(
        ScenarioAxes(
            relationship_windows=[window],
            tracing_methods=["explicit"],
            community_share_bps=[payload.community_share_bps],
        )
    )[0]
    ledgers = [
        AssetLedger(
            asset_id=UUID("00000000-0000-4000-8000-000000000001"),
            name="Fictional home equity",
            kind="asset",
            events=[
                LedgerEvent(
                    effective_date=payload.start_date,
                    event_type="acquisition",
                    amount_cents=33_000_000,
                    source_allocations={
                        "user_separate": 10_000_000,
                        "other_separate": 8_000_000,
                        "community": 15_000_000,
                        "unresolved": 0,
                    },
                    provenance="scenario_assumed",
                    note="Fictional demo value and allocations.",
                )
            ],
        ),
        AssetLedger(
            asset_id=UUID("00000000-0000-4000-8000-000000000002"),
            name="Fictional savings",
            kind="asset",
            events=[
                LedgerEvent(
                    effective_date=payload.start_date,
                    event_type="acquisition",
                    amount_cents=8_500_000,
                    source_allocations={
                        "user_separate": 4_000_000,
                        "other_separate": 1_500_000,
                        "community": 3_000_000,
                        "unresolved": 0,
                    },
                    provenance="scenario_assumed",
                    note="Fictional demo value and allocations.",
                )
            ],
        ),
        AssetLedger(
            asset_id=UUID("00000000-0000-4000-8000-000000000003"),
            name="Fictional credit-card debt",
            kind="debt",
            events=[
                LedgerEvent(
                    effective_date=payload.start_date,
                    event_type="acquisition",
                    amount_cents=1_200_000,
                    source_allocations={
                        "user_separate": 0,
                        "other_separate": 0,
                        "community": 1_200_000,
                        "unresolved": 0,
                    },
                    provenance="scenario_assumed",
                    note="Fictional demo liability and allocation.",
                )
            ],
        ),
    ]
    terms = MediationOfferTerms(
        offer_from="Sam Taylor (fictional)",
        offer_to="Alex Taylor (fictional)",
        county="King",
        terms=[
            "Fictional sample proposal only; these names, figures, and allocations are invented.",
            (
                f"Illustrative community share: "
                f"{payload.community_share_bps / 100:g}% to the proposing party."
            ),
            "Each party retains the fictional property and debts shown in their proposed column.",
        ],
    )
    return terms, calculate_scenario(scenario, ledgers)


@demo_export_router.post("/demo/exports/docx")
def create_demo_settlement_offer(payload: DemoExportRequest) -> Response:
    terms, result = _demo_export_files(payload)
    docx = render_mediation_offer_docx(terms, result)
    if len(docx) > get_settings().max_upload_bytes:
        raise HTTPException(status_code=413, detail="Generated demo proposal exceeds the file size limit.")
    return Response(
        content=docx,
        media_type=DOCX_MEDIA_TYPE,
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": 'attachment; filename="fictional-demo-cr2a-proposal.docx"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@demo_export_router.post("/demo/exports/xlsx")
def create_demo_settlement_property_schedule(payload: DemoExportRequest) -> Response:
    terms, result = _demo_export_files(payload)
    workbook = render_property_schedule_xlsx(terms, result)
    if len(workbook) > get_settings().max_upload_bytes:
        raise HTTPException(status_code=413, detail="Generated demo schedule exceeds the file size limit.")
    return Response(
        content=workbook,
        media_type=XLSX_MEDIA_TYPE,
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": 'attachment; filename="fictional-demo-property-schedule.xlsx"',
            "X-Content-Type-Options": "nosniff",
        },
    )


def _settlement_disclosure(settings: Settings | None = None) -> SettlementPlanningDisclosure:
    settings = settings or get_settings()
    return SettlementPlanningDisclosure(
        available=bool(
            settings.ai_analysis_enabled
            and settings.auth_enabled
            and settings.case_data_enabled
            and settings.case_materials_enabled
            and not settings.demo_mode_enabled
            and (settings.bedrock_model_id or "").strip()
            and (settings.bedrock_region or "").strip()
            and (settings.settlement_planning_data_handling_notice or "").strip()
        ),
        provider="Amazon Bedrock",
        model_id=settings.bedrock_model_id or None,
        region=settings.bedrock_region or None,
        notice_version=SETTLEMENT_CONSENT_NOTICE_VERSION,
        purpose="Rank only user-specified, server-calculated settlement scenarios for discussion.",
        data_sent=(
            "The user's negotiation objective; active adopted fact IDs, values, field names, "
            "source document IDs, exact source quotes, and page numbers; summarized calculated "
            "property/debt balances and scenario assumptions; and the curated Washington authority set. "
            "Full source documents, ledger notes, credentials, and account numbers are not sent."
        ),
        data_handling_notice=settings.settlement_planning_data_handling_notice or None,
    )


@router.get("", response_model=SettlementPlanningStateRead)
def get_settlement_planning_state(
    case_id: UUID,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SettlementPlanningStateRead:
    try:
        case = _authorize_case(db, user, case_id, write=False)
        consent = _current_consent(db, case_id, user.id)
        event_count = db.query(SettlementLedgerEvent).filter(
            SettlementLedgerEvent.case_id == case_id
        ).count()
        response.headers["Cache-Control"] = "no-store"
        return SettlementPlanningStateRead(
            case_id=case.id,
            consented=bool(
                consent
                and consent.accepted
                and consent.notice_version == SETTLEMENT_CONSENT_NOTICE_VERSION
            ),
            consent_notice_version=consent.notice_version if consent else None,
            profile_revision=case.profile_revision,
            settlement_revision=case.settlement_revision,
            ledger_event_count=event_count,
        )
    except SQLAlchemyError as error:
        logger.exception("Settlement-planning state lookup failed.")
        raise HTTPException(status_code=503, detail="Settlement-planning state is unavailable.") from error


@router.get("/disclosure", response_model=SettlementPlanningDisclosure)
def get_settlement_planning_disclosure(
    case_id: UUID,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SettlementPlanningDisclosure:
    try:
        _authorize_case(db, user, case_id, write=False)
        disclosure = _settlement_disclosure()
        response.headers["Cache-Control"] = "no-store"
        return disclosure
    except SQLAlchemyError as error:
        logger.exception("Settlement-planning disclosure lookup failed.")
        raise HTTPException(status_code=503, detail="Settlement-planning disclosure is unavailable.") from error


@router.post("/consent", status_code=201)
def grant_settlement_planning_consent(
    case_id: UUID,
    payload: ConsentCreate,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    try:
        _authorize_case(db, user, case_id, write=True)
        disclosure = _settlement_disclosure()
        if not disclosure.available:
            raise HTTPException(
                status_code=503,
                detail="AI ranking is unavailable until provider and data-handling settings are configured.",
            )
        db.add(
            SettlementPlanningConsentEvent(
                case_id=case_id,
                user_id=user.id,
                user_id_snapshot=user.id,
                notice_version=payload.notice_version,
                accepted=True,
                provider=disclosure.provider,
                model_id=disclosure.model_id,
                region=disclosure.region,
                purpose=disclosure.purpose,
                data_sent=disclosure.data_sent,
                data_handling_notice=disclosure.data_handling_notice,
                created_at=datetime.now(UTC),
            )
        )
        db.commit()
        response.headers["Cache-Control"] = "no-store"
        return {"status": "consented", "notice_version": payload.notice_version}
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Settlement-planning consent could not be recorded.")
        raise HTTPException(status_code=503, detail="Consent could not be saved.") from error


@router.delete("/consent", status_code=204)
def revoke_settlement_planning_consent(
    case_id: UUID,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    try:
        _authorize_case(db, user, case_id, write=True)
        disclosure = _settlement_disclosure()
        db.add(
            SettlementPlanningConsentEvent(
                case_id=case_id,
                user_id=user.id,
                user_id_snapshot=user.id,
                notice_version=SETTLEMENT_CONSENT_NOTICE_VERSION,
                accepted=False,
                provider=disclosure.provider,
                model_id=disclosure.model_id,
                region=disclosure.region,
                purpose=disclosure.purpose,
                data_sent=disclosure.data_sent,
                data_handling_notice=disclosure.data_handling_notice,
                created_at=datetime.now(UTC),
            )
        )
        db.commit()
        return Response(status_code=204, headers={"Cache-Control": "no-store"})
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Settlement-planning consent revocation could not be recorded.")
        raise HTTPException(status_code=503, detail="Consent revocation could not be saved.") from error


@router.get("/ledger-events", response_model=list[LedgerEventRead])
def get_settlement_ledger_events(
    case_id: UUID,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[LedgerEventRead]:
    try:
        _authorize_case(db, user, case_id, write=False)
        rows = db.scalars(
            select(SettlementLedgerEvent)
            .where(SettlementLedgerEvent.case_id == case_id)
            .order_by(
                SettlementLedgerEvent.effective_date,
                SettlementLedgerEvent.sequence_number,
                SettlementLedgerEvent.id,
            )
            .limit(MAX_LEDGER_EVENTS_PER_CASE + 1)
        ).all()
        if len(rows) > MAX_LEDGER_EVENTS_PER_CASE:
            raise HTTPException(
                status_code=413,
                detail="Settlement ledger exceeds the supported event limit.",
            )
        response.headers["Cache-Control"] = "no-store"
        return [_ledger_event_read(row) for row in rows]
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        logger.exception("Settlement ledger lookup failed.")
        raise HTTPException(status_code=503, detail="Settlement ledger is unavailable.") from error


@router.post("/ledger-events", response_model=LedgerEventRead, status_code=201)
def add_settlement_ledger_event(
    case_id: UUID,
    payload: LedgerEventCreate,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> LedgerEventRead:
    try:
        _authorize_case(db, user, case_id, write=True)
        case = _lock_case(db, case_id)
        request_hash = _request_sha256(payload)
        existing = db.scalar(
            select(SettlementLedgerEvent).where(
                SettlementLedgerEvent.case_id == case_id,
                SettlementLedgerEvent.user_id_snapshot == user.id,
                SettlementLedgerEvent.idempotency_key == payload.idempotency_key,
            )
        )
        if existing is not None:
            if existing.request_sha256 != request_hash:
                raise HTTPException(status_code=409, detail="Idempotency key was reused for different ledger data.")
            response.headers["Cache-Control"] = "no-store"
            return _ledger_event_read(existing)
        _check_revisions(case, payload.expected_profile_revision, payload.expected_settlement_revision)
        if db.query(SettlementLedgerEvent).filter(
            SettlementLedgerEvent.case_id == case_id
        ).count() >= MAX_LEDGER_EVENTS_PER_CASE:
            raise HTTPException(status_code=413, detail="Settlement ledger event limit reached.")
        facts = _active_profile_facts(db, case_id)
        _check_fact_references(payload.event.source_fact_ids, _fact_ids(facts))
        existing_asset = db.scalar(
            select(SettlementLedgerEvent)
            .where(
                SettlementLedgerEvent.case_id == case_id,
                SettlementLedgerEvent.asset_id == payload.asset_id,
            )
            .limit(1)
        )
        if existing_asset is not None and (
            existing_asset.asset_name != payload.asset_name.strip()
            or existing_asset.asset_kind != payload.asset_kind
        ):
            raise HTTPException(status_code=409, detail="Asset name and type cannot change after ledger entry.")
        next_revision = case.settlement_revision + 1
        event = payload.event
        row = SettlementLedgerEvent(
            id=event.id,
            case_id=case_id,
            asset_id=payload.asset_id,
            asset_name=payload.asset_name.strip(),
            asset_kind=payload.asset_kind,
            effective_date=event.effective_date,
            sequence_number=event.sequence_number,
            event_json=event.model_dump(mode="json"),
            user_id=user.id,
            user_id_snapshot=user.id,
            idempotency_key=payload.idempotency_key,
            request_sha256=request_hash,
            profile_revision=case.profile_revision,
            settlement_revision=next_revision,
        )
        case.settlement_revision = next_revision
        db.add(row)
        db.commit()
        db.refresh(row)
        response.headers["Cache-Control"] = "no-store"
        return _ledger_event_read(row)
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ledger event conflicts with an existing ID, date/sequence, or idempotency key.",
        ) from error
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Settlement ledger event could not be saved.")
        raise HTTPException(status_code=503, detail="Settlement ledger event could not be saved.") from error


@router.post("/scenarios", response_model=SettlementScenariosRead)
def create_settlement_scenarios(
    case_id: UUID,
    payload: ScenarioGenerateRequest,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SettlementScenariosRead:
    try:
        case = _authorize_case(db, user, case_id, write=False)
        _check_revisions(case, payload.expected_profile_revision, payload.expected_settlement_revision)
        facts = _active_profile_facts(db, case_id)
        _check_fact_references(
            [fact_id for window in payload.axes.relationship_windows for fact_id in window.source_fact_ids],
            _fact_ids(facts),
        )
        ledgers = _asset_ledgers(db, case_id)
        if not ledgers:
            raise HTTPException(status_code=422, detail="Add ledger events before generating scenarios.")
        _check_fact_references(
            [
                fact_id
                for ledger in ledgers
                for event in ledger.events
                for fact_id in event.source_fact_ids
            ],
            _fact_ids(facts),
        )
        scenarios = [
            calculate_scenario(scenario, ledgers)
            for scenario in generate_scenarios(payload.axes)
        ]
        ranking = None
        ranking_error = None
        consent = _current_consent(db, case_id, user.id)
        disclosure = _settlement_disclosure()
        has_consent = bool(
            consent
            and consent.accepted
            and consent.notice_version == SETTLEMENT_CONSENT_NOTICE_VERSION
        )
        if not has_consent:
            ranking_error = "AI ranking was not performed because separate settlement-planning consent is not active."
        elif not disclosure.available:
            ranking_error = "AI ranking is unavailable until provider and data-handling settings are configured."
        elif not facts:
            ranking_error = "AI ranking was not performed because no active source-backed adopted facts are available."
        else:
            try:
                ranking = rank_settlement_scenarios(
                    scenarios,
                    payload.objective,
                    _reviewed_fact_payload(facts),
                )
            except (ValueError, RuntimeError, BotoCoreError):
                logger.exception("AI settlement-scenario ranking failed; calculated candidates are retained.")
                ranking_error = (
                    "AI ranking failed. The calculated candidates are still available for review; "
                    "check provider configuration and try again."
                )
        db.refresh(case)
        _check_revisions(case, payload.expected_profile_revision, payload.expected_settlement_revision)
        run = SettlementScenarioRun(
            id=uuid4(),
            case_id=case_id,
            user_id=user.id,
            user_id_snapshot=user.id,
            profile_revision=case.profile_revision,
            settlement_revision=case.settlement_revision,
            objective=payload.objective,
            axes_json=payload.axes.model_dump(mode="json"),
            scenario_results_json=[scenario.model_dump(mode="json") for scenario in scenarios],
            ranking_json=ranking.model_dump(mode="json") if ranking is not None else None,
            ranking_error=ranking_error,
            input_fact_ids=[str(fact.id) for fact in facts],
            provider=disclosure.provider if ranking is not None else None,
            model_id=disclosure.model_id if ranking is not None else None,
            region=disclosure.region if ranking is not None else None,
            notice_version=SETTLEMENT_CONSENT_NOTICE_VERSION if ranking is not None else None,
            data_handling_notice=disclosure.data_handling_notice if ranking is not None else None,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        response.headers["Cache-Control"] = "no-store"
        return SettlementScenariosRead(
            run_id=run.id,
            profile_revision=case.profile_revision,
            settlement_revision=case.settlement_revision,
            scenarios=scenarios,
            ranking=ranking,
            ranking_error=ranking_error,
        )
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Settlement scenarios could not be loaded.")
        raise HTTPException(status_code=503, detail="Settlement scenarios are unavailable.") from error


@router.get("/offer-responses", response_model=list[OfferResponseHistoryItem])
def list_settlement_offer_responses(
    case_id: UUID,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[OfferResponseHistoryItem]:
    try:
        _authorize_case(db, user, case_id, write=False)
        rows = db.execute(
            select(
                SettlementOfferResponse,
                SettlementScenarioSelection,
                SettlementNegotiationAttempt,
            )
            .join(
                SettlementScenarioSelection,
                SettlementScenarioSelection.id == SettlementOfferResponse.selection_id,
            )
            .outerjoin(
                SettlementNegotiationAttempt,
                SettlementNegotiationAttempt.selection_id == SettlementScenarioSelection.id,
            )
            .where(
                SettlementOfferResponse.case_id == case_id,
                SettlementScenarioSelection.case_id == case_id,
            )
            .order_by(
                SettlementNegotiationAttempt.attempt_ordinal.asc().nullsfirst(),
                SettlementNegotiationAttempt.created_at.asc().nullsfirst(),
                SettlementOfferResponse.id.asc(),
            )
        ).all()
        response_ids = [offer_response.id for offer_response, _, _ in rows]
        attachments_by_response: dict[UUID, list[dict]] = {
            response_id: [] for response_id in response_ids
        }
        if response_ids:
            attachments = db.scalars(
                select(SettlementOfferResponseAttachment)
                .join(Document, Document.id == SettlementOfferResponseAttachment.document_id)
                .where(
                    SettlementOfferResponseAttachment.response_id.in_(response_ids),
                    Document.case_id == case_id,
                )
                .order_by(SettlementOfferResponseAttachment.created_at)
            ).all()
            for attachment in attachments:
                attachments_by_response[attachment.response_id].append(
                    {"kind": attachment.kind, "filename": attachment.filename}
                )
        response.headers["Cache-Control"] = "no-store"
        return [
            OfferResponseHistoryItem(
                selection_id=selection.id,
                scenario_id=selection.scenario_id,
                attempt_ordinal=attempt.attempt_ordinal if attempt is not None else 1,
                frozen=attempt.frozen_at is not None if attempt is not None else (
                    offer_response.outcome is not None
                ),
                outcome=offer_response.outcome,
                attachments=attachments_by_response[offer_response.id],
            )
            for offer_response, selection, attempt in rows
        ]
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        logger.exception("Settlement offer-response history could not be loaded.")
        raise HTTPException(
            status_code=503,
            detail="Settlement offer-response history is unavailable.",
        ) from error


@router.post("/selections", response_model=ScenarioSelectionRead, status_code=201)
def select_settlement_scenario(
    case_id: UUID,
    payload: ScenarioSelectRequest,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ScenarioSelectionRead:
    try:
        _authorize_case(db, user, case_id, write=True)
        case = _lock_case(db, case_id)
        request_hash = _request_sha256(payload)
        existing = db.scalar(
            select(SettlementScenarioSelection).where(
                SettlementScenarioSelection.case_id == case_id,
                SettlementScenarioSelection.user_id_snapshot == user.id,
                SettlementScenarioSelection.idempotency_key == payload.idempotency_key,
            )
        )
        if existing is not None:
            if existing.request_sha256 != request_hash:
                raise HTTPException(status_code=409, detail="Idempotency key was reused for different scenario data.")
            response.headers["Cache-Control"] = "no-store"
            return ScenarioSelectionRead(
                selection_id=existing.id,
                run_id=existing.run_id,
                scenario_id=existing.scenario_id,
                profile_revision=existing.profile_revision,
                settlement_revision=existing.settlement_revision,
            )
        _check_revisions(case, payload.expected_profile_revision, payload.expected_settlement_revision)
        run = db.scalar(
            select(SettlementScenarioRun).where(
                SettlementScenarioRun.id == payload.run_id,
                SettlementScenarioRun.case_id == case_id,
            )
        )
        if run is None:
            raise HTTPException(status_code=404, detail="Calculated scenario run not found.")
        if (
            run.profile_revision != case.profile_revision
            or run.settlement_revision != case.settlement_revision
        ):
            raise HTTPException(status_code=409, detail="Scenario run is stale. Recalculate before selecting.")
        calculated = [
            SettlementScenarioResult.model_validate(result)
            for result in run.scenario_results_json
        ]
        selected = next(
            (result for result in calculated if result.scenario.id == payload.scenario_id),
            None,
        )
        if selected is None:
            raise HTTPException(status_code=422, detail="Select a scenario generated from the supplied assumptions.")
        selection = SettlementScenarioSelection(
            case_id=case_id,
            user_id=user.id,
            user_id_snapshot=user.id,
            idempotency_key=payload.idempotency_key,
            request_sha256=request_hash,
            run_id=run.id,
            scenario_id=selected.scenario.id,
            scenario_result_json=selected.model_dump(mode="json"),
            profile_revision=case.profile_revision,
            settlement_revision=case.settlement_revision,
        )
        db.add(selection)
        db.flush()
        from app.offer_response import _create_initial_attempt

        _create_initial_attempt(db, case, selection, user)
        db.commit()
        db.refresh(selection)
        response.headers["Cache-Control"] = "no-store"
        return ScenarioSelectionRead(
            selection_id=selection.id,
            run_id=selection.run_id,
            scenario_id=selection.scenario_id,
            profile_revision=selection.profile_revision,
            settlement_revision=selection.settlement_revision,
            attempt_ordinal=1,
        )
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Scenario selection idempotency key already exists.") from error
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Settlement scenario selection could not be saved.")
        raise HTTPException(status_code=503, detail="Scenario selection could not be saved.") from error


@router.post("/offers/{selection_id}/docx")
def create_settlement_offer(
    case_id: UUID,
    selection_id: UUID,
    payload: OfferCreate,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    try:
        _require_real_case_exports()
        case = _authorize_case(db, user, case_id, write=True)
        selection = db.scalar(
            select(SettlementScenarioSelection).where(
                SettlementScenarioSelection.id == selection_id,
                SettlementScenarioSelection.case_id == case_id,
            )
        )
        if selection is None:
            raise HTTPException(status_code=404, detail="Selected settlement scenario not found.")
        _check_revisions(case, selection.profile_revision, selection.settlement_revision)
        result = SettlementScenarioResult.model_validate(selection.scenario_result_json)
        docx = render_mediation_offer_docx(payload.terms, result)
        if len(docx) > get_settings().max_upload_bytes:
            raise HTTPException(status_code=413, detail="Generated proposal exceeds the file size limit.")
        return Response(
            content=docx,
            media_type=DOCX_MEDIA_TYPE,
            headers={
                "Cache-Control": "no-store",
                "Content-Disposition": 'attachment; filename="cr2a-agreement-proposal-draft.docx"',
                "X-Content-Type-Options": "nosniff",
            },
        )
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Saved scenario data is invalid.") from error
    except SQLAlchemyError as error:
        logger.exception("Selected settlement scenario could not be loaded.")
        raise HTTPException(status_code=503, detail="Offer draft could not be generated.") from error


@router.post("/offers/{selection_id}/xlsx")
def create_settlement_property_schedule(
    case_id: UUID,
    selection_id: UUID,
    payload: OfferCreate,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    try:
        _require_real_case_exports()
        case = _authorize_case(db, user, case_id, write=True)
        selection = db.scalar(
            select(SettlementScenarioSelection).where(
                SettlementScenarioSelection.id == selection_id,
                SettlementScenarioSelection.case_id == case_id,
            )
        )
        if selection is None:
            raise HTTPException(status_code=404, detail="Selected settlement scenario not found.")
        _check_revisions(case, selection.profile_revision, selection.settlement_revision)
        result = SettlementScenarioResult.model_validate(selection.scenario_result_json)
        workbook = render_property_schedule_xlsx(payload.terms, result)
        if len(workbook) > get_settings().max_upload_bytes:
            raise HTTPException(status_code=413, detail="Generated proposal exceeds the file size limit.")
        return Response(
            content=workbook,
            media_type=XLSX_MEDIA_TYPE,
            headers={
                "Cache-Control": "no-store",
                "Content-Disposition": 'attachment; filename="property-division-proposal-draft.xlsx"',
                "X-Content-Type-Options": "nosniff",
            },
        )
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Saved scenario data is invalid.") from error
    except SQLAlchemyError as error:
        logger.exception("Selected settlement scenario could not be loaded for workbook export.")
        raise HTTPException(status_code=503, detail="Property schedule could not be generated.") from error


def _destination_digest(destination: str) -> str:
    key = get_settings().auth_jwt_secret
    if not key:
        raise HTTPException(status_code=503, detail="Delivery audit protection is not configured.")
    return hmac.new(key.encode(), destination.encode(), hashlib.sha256).hexdigest()


def _offer_exports(
    terms: MediationOfferTerms,
    result: SettlementScenarioResult,
) -> list[ExportFile]:
    exports = [
        ExportFile(
            filename="cr2a-agreement-proposal-draft.docx",
            content_type=DOCX_MEDIA_TYPE,
            content=render_mediation_offer_docx(terms, result),
        ),
        ExportFile(
            filename="property-division-proposal-draft.xlsx",
            content_type=XLSX_MEDIA_TYPE,
            content=render_property_schedule_xlsx(terms, result),
        ),
    ]
    max_bytes = get_settings().max_upload_bytes
    if sum(len(export.content) for export in exports) > max_bytes:
        raise HTTPException(status_code=413, detail="Generated proposal files exceed the delivery size limit.")
    return exports


@router.post("/offers/{selection_id}/deliver")
def deliver_settlement_offer(
    case_id: UUID,
    selection_id: UUID,
    payload: OfferDelivery,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, int | str]:
    try:
        _require_real_case_exports()
        case = _authorize_case(db, user, case_id, write=True)
        selection = db.scalar(
            select(SettlementScenarioSelection).where(
                SettlementScenarioSelection.id == selection_id,
                SettlementScenarioSelection.case_id == case_id,
            )
        )
        if selection is None:
            raise HTTPException(status_code=404, detail="Selected settlement scenario not found.")
        _check_revisions(case, selection.profile_revision, selection.settlement_revision)
        result = SettlementScenarioResult.model_validate(selection.scenario_result_json)
        exports = _offer_exports(payload.terms, result)
        settings = get_settings()
        if payload.channel == "email":
            if not settings.smtp_host or not settings.auth_email_from:
                raise HTTPException(status_code=503, detail="Email delivery is not configured.")
            destination = str(payload.recipient)
        elif payload.channel == "google_drive":
            if not settings.google_client_id or not settings.google_client_secret:
                raise HTTPException(status_code=503, detail="Google Drive delivery is not configured.")
            destination = "Google Drive root (private)"
        else:
            if not settings.dropbox_app_key or not settings.dropbox_app_secret:
                raise HTTPException(status_code=503, detail="Dropbox delivery is not configured.")
            destination = "Connected Dropbox app folder (private)"
        destination_digest = _destination_digest(f"{payload.channel}:{destination}")
        request_hash = _delivery_request_digest(payload)
        prior = db.scalar(
            select(ExportDeliveryEvent)
            .where(
                ExportDeliveryEvent.user_id_snapshot == user.id,
                ExportDeliveryEvent.idempotency_key == payload.idempotency_key,
            )
            .with_for_update()
        )
        if prior is not None:
            if (
                prior.request_sha256 != request_hash
                or prior.selection_id != selection_id
                or prior.case_id != case_id
                or prior.channel != payload.channel
                or prior.destination_digest != destination_digest
            ):
                raise HTTPException(status_code=409, detail="Delivery key was reused for a different request.")
            if prior.outcome != "success":
                raise HTTPException(
                    status_code=409,
                    detail="A delivery attempt is already recorded. Check the destination before retrying.",
                )
            response.headers["Cache-Control"] = "no-store"
            return {"outcome": "success", "file_count": prior.file_count}
        event = ExportDeliveryEvent(
            id=uuid4(),
            case_id=case_id,
            selection_id=selection_id,
            user_id=user.id,
            user_id_snapshot=user.id,
            channel=payload.channel,
            destination_digest=destination_digest,
            request_sha256=request_hash,
            outcome="pending",
            file_count=0,
            idempotency_key=payload.idempotency_key,
        )
        db.add(event)
        db.commit()
        try:
            file_count = deliver_export_files(
                db,
                user,
                payload.channel,
                destination if payload.channel == "email" else "",
                exports,
            )
        except ExportDeliveryError as error:
            event.outcome = "partial" if error.delivered_files else "failed"
            event.file_count = error.delivered_files
            db.commit()
            raise HTTPException(status_code=502, detail=str(error)) from error
        event.outcome = "success"
        event.file_count = file_count
        db.commit()
        response.headers["Cache-Control"] = "no-store"
        return {"outcome": event.outcome, "file_count": event.file_count}
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="A delivery request with this key already exists.") from error
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Settlement proposal delivery could not be completed.")
        raise HTTPException(
            status_code=503,
            detail="Delivery status could not be confirmed. Verify the destination before retrying.",
        ) from error
