import hashlib
import json
import logging
from collections import defaultdict
from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID, uuid4, uuid5

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth_routes import require_current_user
from app.database import get_db
from app.failure_logging import log_failure_event
from app.models import (
    Case,
    CaseMembership,
    CaseProfileAdoption,
    CaseProfileFact,
    CaseProfileFactEvent,
    Document,
    DocumentAnalysisConsent,
    DocumentAnalysisJob,
    DocumentAnalysisProposal,
    DocumentAnalysisRequest,
    DocumentExtraction,
    ProposalReviewEvent,
    User,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["proposal review"])


class ProposalReviewCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idempotency_key: UUID
    decision: Literal["accepted", "edited", "rejected"]
    edited_value: str | None = Field(default=None, max_length=10_000)

    @model_validator(mode="after")
    def validate_edited_value(self) -> "ProposalReviewCreate":
        if self.decision == "edited":
            if self.edited_value is None or not self.edited_value.strip():
                raise ValueError("An edited suggestion needs a non-empty value.")
        elif self.edited_value is not None:
            raise ValueError("Only an edited decision may include an edited value.")
        return self


class AdoptionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idempotency_key: UUID
    expected_profile_revision: int = Field(ge=0)
    proposal_ids: list[UUID] = Field(min_length=1, max_length=50)
    supersede_fact_ids: list[UUID] = Field(default_factory=list, max_length=100)
    confirm: Literal[True]

    @model_validator(mode="after")
    def validate_unique_ids(self) -> "AdoptionCreate":
        if len(self.proposal_ids) != len(set(self.proposal_ids)):
            raise ValueError("Proposal IDs must be unique.")
        if len(self.supersede_fact_ids) != len(set(self.supersede_fact_ids)):
            raise ValueError("Superseded fact IDs must be unique.")
        return self


class FactDispositionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idempotency_key: UUID
    expected_profile_revision: int = Field(ge=0)
    action: Literal["withdrawn"]
    confirm: Literal[True]


class ProposalReviewEventRead(BaseModel):
    id: UUID
    decision: Literal["accepted", "edited", "rejected"]
    edited_value: str | None
    created_at: datetime


class ReviewProposalRead(BaseModel):
    proposal_id: UUID
    document_id: UUID
    field_key: str
    proposed_value: str
    source_sha256: str
    source_quote: str
    source_page_number: int | None
    confidence: Literal["high", "medium", "low"]
    uncertainty: str
    label: Literal["AI suggestion"] = "AI suggestion"
    evidence_status: Literal["available", "unavailable"]
    source_file_url: str | None
    source_text_url: str
    review_decision: Literal["accepted", "edited", "rejected"] | None
    reviewed_value: str | None
    review_history: list[ProposalReviewEventRead]


class ProposalReviewList(BaseModel):
    request_id: UUID
    proposals: list[ReviewProposalRead]


class SourceTextPage(BaseModel):
    page_number: int | None
    text: str


class SourceTextRead(BaseModel):
    document_id: UUID
    extension: str
    source_sha256: str
    pages: list[SourceTextPage]


class ProfileFactEventRead(BaseModel):
    id: UUID
    action: Literal["withdrawn", "superseded", "reinstated"]
    replacement_fact_id: UUID | None
    profile_revision: int
    created_at: datetime


class ProfileFactRead(BaseModel):
    id: UUID
    proposal_id: UUID
    field_key: str
    value: str
    original_value: str
    source_document_id: UUID
    source_sha256: str
    source_quote: str
    source_page_number: int | None
    provider: str
    model_id: str
    notice_version: str
    review_decision: Literal["accepted", "edited"]
    adopted_by: UUID
    adopted_at: datetime
    profile_revision: int
    disposition: Literal["active", "withdrawn", "superseded"]
    conflict: bool
    source_available: bool
    history: list[ProfileFactEventRead]


class ProfileFactsRead(BaseModel):
    case_id: UUID
    profile_revision: int
    facts: list[ProfileFactRead]


class AdoptionRead(BaseModel):
    adoption_id: UUID
    profile_revision: int
    facts: list[ProfileFactRead]


class FactDispositionRead(BaseModel):
    fact_id: UUID
    action: Literal["withdrawn"]
    profile_revision: int


def _request_sha256(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _authorize_case(
    db: Session,
    user: User,
    case_id: UUID,
    *,
    write: bool,
) -> None:
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
    if write and membership.role == "viewer":
        raise HTTPException(status_code=403, detail="Case is read-only.")


def _proposal_for_request(
    db: Session,
    case_id: UUID,
    request_id: UUID,
    proposal_id: UUID,
) -> DocumentAnalysisProposal:
    proposal = db.scalar(
        select(DocumentAnalysisProposal)
        .join(
            DocumentAnalysisJob,
            DocumentAnalysisJob.id == DocumentAnalysisProposal.job_id,
        )
        .join(
            DocumentAnalysisRequest,
            DocumentAnalysisRequest.id == DocumentAnalysisJob.request_id,
        )
        .where(
            DocumentAnalysisProposal.id == proposal_id,
            DocumentAnalysisRequest.id == request_id,
            DocumentAnalysisRequest.case_id == case_id,
        )
    )
    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    return proposal


def _source_extraction(
    db: Session,
    case_id: UUID,
    document_id: UUID,
    source_sha256: str,
) -> tuple[Document, DocumentExtraction] | None:
    document = db.get(Document, document_id)
    if document is None or document.case_id != case_id or document.sha256 != source_sha256:
        return None
    extraction = db.scalar(
        select(DocumentExtraction)
        .where(DocumentExtraction.document_id == document_id)
        .order_by(DocumentExtraction.created_at.desc(), DocumentExtraction.id.desc())
        .limit(1)
    )
    if extraction is None or not isinstance(extraction.pages_json, list):
        return None
    return document, extraction


def _quote_matches(
    pages: object,
    quote: str,
    page_number: int | None,
) -> bool:
    if not isinstance(pages, list) or not quote:
        return False
    matching_texts = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        if page.get("page_number") == page_number and isinstance(page.get("text"), str):
            matching_texts.append(page["text"])
    return len(matching_texts) == 1 and quote in matching_texts[0]


def _proposal_evidence(
    db: Session,
    case_id: UUID,
    proposal: DocumentAnalysisProposal,
) -> tuple[Document, DocumentExtraction] | None:
    source = _source_extraction(
        db,
        case_id,
        proposal.document_id,
        proposal.source_sha256,
    )
    if source is None or not _quote_matches(
        source[1].pages_json,
        proposal.source_quote,
        proposal.source_page_number,
    ):
        return None
    return source


def record_proposal_review(
    db: Session,
    case_id: UUID,
    request_id: UUID,
    proposal_id: UUID,
    user_id: UUID,
    payload: ProposalReviewCreate,
) -> ProposalReviewEvent:
    request_sha256 = _request_sha256(
        {
            "proposal_id": str(proposal_id),
            "decision": payload.decision,
            "edited_value": payload.edited_value,
        }
    )
    existing = db.scalar(
        select(ProposalReviewEvent).where(
            ProposalReviewEvent.case_id == case_id,
            ProposalReviewEvent.user_id_snapshot == user_id,
            ProposalReviewEvent.idempotency_key == payload.idempotency_key,
        )
    )
    if existing is not None:
        if existing.request_sha256 != request_sha256:
            raise HTTPException(status_code=409, detail="Review idempotency key was reused.")
        return existing

    proposal = _proposal_for_request(db, case_id, request_id, proposal_id)
    if _proposal_evidence(db, case_id, proposal) is None:
        raise HTTPException(
            status_code=409,
            detail="The source evidence is unavailable or no longer matches this suggestion.",
        )
    event = ProposalReviewEvent(
        id=uuid4(),
        case_id=case_id,
        proposal_id=proposal.id,
        proposal_id_snapshot=proposal.id,
        user_id=user_id,
        user_id_snapshot=user_id,
        idempotency_key=payload.idempotency_key,
        request_sha256=request_sha256,
        decision=payload.decision,
        edited_value=payload.edited_value,
        created_at=datetime.now(UTC),
    )
    db.add(event)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        existing = db.scalar(
            select(ProposalReviewEvent).where(
                ProposalReviewEvent.case_id == case_id,
                ProposalReviewEvent.user_id_snapshot == user_id,
                ProposalReviewEvent.idempotency_key == payload.idempotency_key,
            )
        )
        if existing is None:
            raise
        if existing.request_sha256 != request_sha256:
            raise HTTPException(status_code=409, detail="Review idempotency key was reused.") from error
        return existing
    return event


def proposal_review_list(
    db: Session,
    case_id: UUID,
    request_id: UUID,
) -> ProposalReviewList:
    request = db.scalar(
        select(DocumentAnalysisRequest).where(
            DocumentAnalysisRequest.id == request_id,
            DocumentAnalysisRequest.case_id == case_id,
        )
    )
    if request is None:
        raise HTTPException(status_code=404, detail="Analysis request not found.")
    proposals = db.scalars(
        select(DocumentAnalysisProposal)
        .join(
            DocumentAnalysisJob,
            DocumentAnalysisJob.id == DocumentAnalysisProposal.job_id,
        )
        .where(DocumentAnalysisJob.request_id == request_id)
        .order_by(DocumentAnalysisProposal.created_at, DocumentAnalysisProposal.id)
    ).all()
    results = []
    for proposal in proposals:
        source = _proposal_evidence(db, case_id, proposal)
        events = db.scalars(
            select(ProposalReviewEvent)
            .where(
                ProposalReviewEvent.case_id == case_id,
                ProposalReviewEvent.proposal_id_snapshot == proposal.id,
            )
            .order_by(ProposalReviewEvent.created_at, ProposalReviewEvent.id)
        ).all()
        latest = events[-1] if events else None
        results.append(
            ReviewProposalRead(
                proposal_id=proposal.id,
                document_id=proposal.document_id,
                field_key=proposal.field_key,
                proposed_value=proposal.value,
                source_sha256=proposal.source_sha256,
                source_quote=proposal.source_quote,
                source_page_number=proposal.source_page_number,
                confidence=proposal.confidence,
                uncertainty=proposal.uncertainty,
                evidence_status="available" if source is not None else "unavailable",
                source_file_url=(
                    f"/documents/{proposal.document_id}/preview"
                    + (
                        f"#page={proposal.source_page_number}"
                        if proposal.source_page_number is not None
                        else ""
                    )
                    if source is not None and source[0].extension == "pdf"
                    else None
                ),
                source_text_url=f"/cases/{case_id}/documents/{proposal.document_id}/source-text",
                review_decision=latest.decision if latest is not None else None,
                reviewed_value=(
                    latest.edited_value
                    if latest is not None and latest.decision == "edited"
                    else proposal.value
                    if latest is not None and latest.decision == "accepted"
                    else None
                ),
                review_history=[
                    ProposalReviewEventRead(
                        id=event.id,
                        decision=event.decision,
                        edited_value=event.edited_value,
                        created_at=event.created_at,
                    )
                    for event in events
                ],
            )
        )
    return ProposalReviewList(request_id=request_id, proposals=results)


def source_text(
    db: Session,
    case_id: UUID,
    document_id: UUID,
) -> SourceTextRead:
    document = db.get(Document, document_id)
    if document is None or document.case_id != case_id:
        raise HTTPException(status_code=404, detail="Document not found.")
    extraction = db.scalar(
        select(DocumentExtraction)
        .where(DocumentExtraction.document_id == document_id)
        .order_by(DocumentExtraction.created_at.desc(), DocumentExtraction.id.desc())
        .limit(1)
    )
    if extraction is None or not isinstance(extraction.pages_json, list):
        raise HTTPException(status_code=404, detail="Source text is unavailable.")
    pages = []
    for page in extraction.pages_json:
        if (
            not isinstance(page, dict)
            or not isinstance(page.get("text"), str)
            or (
                page.get("page_number") is not None
                and (
                    not isinstance(page.get("page_number"), int)
                    or isinstance(page.get("page_number"), bool)
                    or page["page_number"] < 1
                )
            )
        ):
            raise HTTPException(status_code=503, detail="Source text is unavailable.")
        pages.append(
            SourceTextPage(
                page_number=page.get("page_number"),
                text=page["text"],
            )
        )
    return SourceTextRead(
        document_id=document.id,
        extension=document.extension,
        source_sha256=document.sha256,
        pages=pages,
    )


def _active_fact_dispositions(
    db: Session,
    case_id: UUID,
    fact_ids: list[UUID],
) -> dict[UUID, CaseProfileFactEvent]:
    if not fact_ids:
        return {}
    events = db.scalars(
        select(CaseProfileFactEvent)
        .where(
            CaseProfileFactEvent.case_id == case_id,
            CaseProfileFactEvent.fact_id.in_(fact_ids),
        )
        .order_by(CaseProfileFactEvent.created_at, CaseProfileFactEvent.id)
    ).all()
    latest = {}
    for event in events:
        latest[event.fact_id] = event
    return latest


def _profile_fact_read(
    db: Session,
    fact: CaseProfileFact,
    disposition_event: CaseProfileFactEvent | None,
    conflict: bool,
    history: list[CaseProfileFactEvent],
) -> ProfileFactRead:
    document = db.get(Document, fact.source_document_id)
    return ProfileFactRead(
        id=fact.id,
        proposal_id=fact.proposal_id_snapshot,
        field_key=fact.field_key,
        value=fact.value,
        original_value=fact.original_value,
        source_document_id=fact.source_document_id,
        source_sha256=fact.source_sha256,
        source_quote=fact.source_quote,
        source_page_number=fact.source_page_number,
        provider=fact.provider,
        model_id=fact.model_id,
        notice_version=fact.notice_version,
        review_decision=fact.review_decision,
        adopted_by=fact.adopted_by_snapshot,
        adopted_at=fact.adopted_at,
        profile_revision=fact.profile_revision,
        disposition=(
            disposition_event.action
            if disposition_event is not None and disposition_event.action != "reinstated"
            else "active"
        ),
        conflict=conflict,
        source_available=(
            document is not None
            and document.case_id == fact.case_id
            and document.sha256 == fact.source_sha256
        ),
        history=[
            ProfileFactEventRead(
                id=event.id,
                action=event.action,
                replacement_fact_id=event.replacement_fact_id,
                profile_revision=event.profile_revision,
                created_at=event.created_at,
            )
            for event in history
        ],
    )


def case_profile_facts(db: Session, case_id: UUID) -> ProfileFactsRead:
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    facts = db.scalars(
        select(CaseProfileFact)
        .where(CaseProfileFact.case_id == case_id)
        .order_by(CaseProfileFact.profile_revision, CaseProfileFact.id)
    ).all()
    fact_ids = [fact.id for fact in facts]
    events = db.scalars(
        select(CaseProfileFactEvent)
        .where(CaseProfileFactEvent.case_id == case_id)
        .order_by(CaseProfileFactEvent.created_at, CaseProfileFactEvent.id)
    ).all()
    history_by_fact: dict[UUID, list[CaseProfileFactEvent]] = defaultdict(list)
    latest_by_fact = {}
    for event in events:
        history_by_fact[event.fact_id].append(event)
        latest_by_fact[event.fact_id] = event

    values_by_key: dict[str, set[str]] = defaultdict(set)
    for fact in facts:
        disposition = latest_by_fact.get(fact.id)
        if disposition is None or disposition.action == "reinstated":
            values_by_key[fact.field_key].add(fact.value)
    results = [
        _profile_fact_read(
            db,
            fact,
            latest_by_fact.get(fact.id),
            len(values_by_key[fact.field_key]) > 1,
            history_by_fact[fact.id],
        )
        for fact in facts
    ]
    return ProfileFactsRead(
        case_id=case_id,
        profile_revision=case.profile_revision,
        facts=results,
    )


def _adoption_facts(db: Session, adoption: CaseProfileAdoption) -> AdoptionRead:
    facts = db.scalars(
        select(CaseProfileFact)
        .where(CaseProfileFact.adoption_id == adoption.id)
        .order_by(CaseProfileFact.id)
    ).all()
    fact_events = _active_fact_dispositions(
        db,
        adoption.case_id,
        [fact.id for fact in facts],
    )
    profile_events = db.scalars(
        select(CaseProfileFactEvent)
        .where(
            CaseProfileFactEvent.case_id == adoption.case_id,
            CaseProfileFactEvent.fact_id.in_([fact.id for fact in facts]),
        )
        .order_by(CaseProfileFactEvent.created_at, CaseProfileFactEvent.id)
    ).all() if facts else []
    history_by_fact: dict[UUID, list[CaseProfileFactEvent]] = defaultdict(list)
    for event in profile_events:
        history_by_fact[event.fact_id].append(event)
    return AdoptionRead(
        adoption_id=adoption.id,
        profile_revision=adoption.profile_revision_after,
        facts=[
            _profile_fact_read(
                db,
                fact,
                fact_events.get(fact.id),
                False,
                history_by_fact[fact.id],
            )
            for fact in facts
        ],
    )


def _latest_review_events(
    db: Session,
    case_id: UUID,
    proposal_ids: list[UUID],
) -> dict[UUID, ProposalReviewEvent]:
    if not proposal_ids:
        return {}
    events = db.scalars(
        select(ProposalReviewEvent)
        .where(
            ProposalReviewEvent.case_id == case_id,
            ProposalReviewEvent.proposal_id_snapshot.in_(proposal_ids),
        )
        .order_by(ProposalReviewEvent.created_at, ProposalReviewEvent.id)
    ).all()
    latest = {}
    for event in events:
        latest[event.proposal_id_snapshot] = event
    return latest


def adopt_case_proposals(
    db: Session,
    case_id: UUID,
    user_id: UUID,
    payload: AdoptionCreate,
) -> AdoptionRead:
    request_sha256 = _request_sha256(
        {
            "proposal_ids": sorted(str(value) for value in payload.proposal_ids),
            "supersede_fact_ids": sorted(str(value) for value in payload.supersede_fact_ids),
        }
    )
    existing = db.scalar(
        select(CaseProfileAdoption).where(
            CaseProfileAdoption.case_id == case_id,
            CaseProfileAdoption.user_id_snapshot == user_id,
            CaseProfileAdoption.idempotency_key == payload.idempotency_key,
        )
    )
    if existing is not None:
        if existing.request_sha256 != request_sha256:
            raise HTTPException(status_code=409, detail="Adoption idempotency key was reused.")
        return _adoption_facts(db, existing)

    case = db.scalar(select(Case).where(Case.id == case_id).with_for_update())
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    existing = db.scalar(
        select(CaseProfileAdoption).where(
            CaseProfileAdoption.case_id == case_id,
            CaseProfileAdoption.user_id_snapshot == user_id,
            CaseProfileAdoption.idempotency_key == payload.idempotency_key,
        )
    )
    if existing is not None:
        if existing.request_sha256 != request_sha256:
            raise HTTPException(status_code=409, detail="Adoption idempotency key was reused.")
        return _adoption_facts(db, existing)
    if case.profile_revision != payload.expected_profile_revision:
        raise HTTPException(
            status_code=409,
            detail=f"Case profile changed. Current revision is {case.profile_revision}.",
        )

    proposals = db.scalars(
        select(DocumentAnalysisProposal)
        .join(
            DocumentAnalysisJob,
            DocumentAnalysisJob.id == DocumentAnalysisProposal.job_id,
        )
        .join(
            DocumentAnalysisRequest,
            DocumentAnalysisRequest.id == DocumentAnalysisJob.request_id,
        )
        .where(
            DocumentAnalysisRequest.case_id == case_id,
            DocumentAnalysisProposal.id.in_(payload.proposal_ids),
        )
    ).all()
    proposals_by_id = {proposal.id: proposal for proposal in proposals}
    if len(proposals_by_id) != len(payload.proposal_ids):
        raise HTTPException(status_code=404, detail="One or more selected suggestions were not found.")

    existing_facts = db.scalars(
        select(CaseProfileFact).where(
            CaseProfileFact.case_id == case_id,
            CaseProfileFact.proposal_id_snapshot.in_(payload.proposal_ids),
        )
    ).all()
    if existing_facts:
        raise HTTPException(status_code=409, detail="A selected suggestion was already adopted.")

    latest_reviews = _latest_review_events(db, case_id, payload.proposal_ids)
    selected: list[tuple[DocumentAnalysisProposal, ProposalReviewEvent, DocumentAnalysisConsent]] = []
    for proposal_id in payload.proposal_ids:
        proposal = proposals_by_id[proposal_id]
        review = latest_reviews.get(proposal_id)
        if review is None or review.decision not in {"accepted", "edited"}:
            raise HTTPException(
                status_code=409,
                detail="Every selected suggestion must be accepted or edited before adoption.",
            )
        if _proposal_evidence(db, case_id, proposal) is None:
            raise HTTPException(
                status_code=409,
                detail="A selected suggestion no longer has verifiable source evidence.",
            )
        consent = db.scalar(
            select(DocumentAnalysisConsent)
            .join(
                DocumentAnalysisRequest,
                DocumentAnalysisRequest.consent_id == DocumentAnalysisConsent.id,
            )
            .join(
                DocumentAnalysisJob,
                DocumentAnalysisJob.request_id == DocumentAnalysisRequest.id,
            )
            .where(
                DocumentAnalysisRequest.case_id == case_id,
                DocumentAnalysisJob.id == proposal.job_id,
            )
        )
        if consent is None:
            raise HTTPException(status_code=409, detail="Suggestion provenance is unavailable.")
        selected.append((proposal, review, consent))

    facts_to_supersede = []
    if payload.supersede_fact_ids:
        old_facts = db.scalars(
            select(CaseProfileFact).where(
                CaseProfileFact.case_id == case_id,
                CaseProfileFact.id.in_(payload.supersede_fact_ids),
            )
        ).all()
        if len(old_facts) != len(payload.supersede_fact_ids):
            raise HTTPException(status_code=404, detail="One or more profile facts were not found.")
        dispositions = _active_fact_dispositions(
            db,
            case_id,
            [fact.id for fact in old_facts],
        )
        selected_keys = {proposal.field_key for proposal, _, _ in selected}
        for fact in old_facts:
            disposition = dispositions.get(fact.id)
            if disposition is not None and disposition.action != "reinstated":
                raise HTTPException(status_code=409, detail="A selected profile fact is no longer active.")
            if fact.field_key not in selected_keys:
                raise HTTPException(
                    status_code=409,
                    detail="A profile fact can only be superseded by a suggestion for the same field.",
                )
            facts_to_supersede.append(fact)

    next_revision = case.profile_revision + 1
    adoption = CaseProfileAdoption(
        id=uuid4(),
        case_id=case_id,
        user_id=user_id,
        user_id_snapshot=user_id,
        idempotency_key=payload.idempotency_key,
        request_sha256=request_sha256,
        profile_revision_before=case.profile_revision,
        profile_revision_after=next_revision,
    )
    db.add(adoption)
    fact_by_key: dict[str, CaseProfileFact] = {}
    new_facts = []
    for proposal, review, consent in selected:
        value = review.edited_value if review.decision == "edited" else proposal.value
        fact = CaseProfileFact(
            id=uuid4(),
            case_id=case_id,
            adoption_id=adoption.id,
            proposal_id_snapshot=proposal.id,
            field_key=proposal.field_key,
            value=value,
            original_value=proposal.value,
            source_document_id=proposal.document_id,
            source_sha256=proposal.source_sha256,
            source_quote=proposal.source_quote,
            source_page_number=proposal.source_page_number,
            provider=consent.provider,
            model_id=consent.model_id,
            notice_version=consent.notice_version,
            review_decision=review.decision,
            adopted_by_snapshot=user_id,
            profile_revision=next_revision,
            adopted_at=datetime.now(UTC),
        )
        fact_by_key.setdefault(proposal.field_key, fact)
        new_facts.append(fact)
    db.add_all(new_facts)
    case.profile_revision = next_revision
    db.flush()

    supersede_events = []
    for old_fact in facts_to_supersede:
        replacement = fact_by_key[old_fact.field_key]
        supersede_events.append(
            CaseProfileFactEvent(
                id=uuid4(),
                case_id=case_id,
                fact_id=old_fact.id,
                replacement_fact_id=replacement.id,
                user_id=user_id,
                user_id_snapshot=user_id,
                idempotency_key=uuid5(adoption.id, str(old_fact.id)),
                request_sha256=request_sha256,
                action="superseded",
                profile_revision=next_revision,
                created_at=datetime.now(UTC),
            )
        )
    if supersede_events:
        db.add_all(supersede_events)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        existing = db.scalar(
            select(CaseProfileAdoption).where(
                CaseProfileAdoption.case_id == case_id,
                CaseProfileAdoption.user_id_snapshot == user_id,
                CaseProfileAdoption.idempotency_key == payload.idempotency_key,
            )
        )
        if existing is not None:
            if existing.request_sha256 != request_sha256:
                raise HTTPException(status_code=409, detail="Adoption idempotency key was reused.") from error
            return _adoption_facts(db, existing)
        raise HTTPException(
            status_code=409,
            detail="The profile changed while adoption was being saved. Refresh and try again.",
        ) from error
    return _adoption_facts(db, adoption)


def withdraw_case_fact(
    db: Session,
    case_id: UUID,
    fact_id: UUID,
    user_id: UUID,
    payload: FactDispositionCreate,
) -> FactDispositionRead:
    request_sha256 = _request_sha256({"fact_id": str(fact_id), "action": payload.action})
    existing = db.scalar(
        select(CaseProfileFactEvent).where(
            CaseProfileFactEvent.case_id == case_id,
            CaseProfileFactEvent.user_id_snapshot == user_id,
            CaseProfileFactEvent.idempotency_key == payload.idempotency_key,
        )
    )
    if existing is not None:
        if existing.request_sha256 != request_sha256:
            raise HTTPException(status_code=409, detail="Fact disposition idempotency key was reused.")
        return FactDispositionRead(
            fact_id=existing.fact_id,
            action="withdrawn",
            profile_revision=existing.profile_revision,
        )

    case = db.scalar(select(Case).where(Case.id == case_id).with_for_update())
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    existing = db.scalar(
        select(CaseProfileFactEvent).where(
            CaseProfileFactEvent.case_id == case_id,
            CaseProfileFactEvent.user_id_snapshot == user_id,
            CaseProfileFactEvent.idempotency_key == payload.idempotency_key,
        )
    )
    if existing is not None:
        if existing.request_sha256 != request_sha256:
            raise HTTPException(status_code=409, detail="Fact disposition idempotency key was reused.")
        return FactDispositionRead(
            fact_id=existing.fact_id,
            action="withdrawn",
            profile_revision=existing.profile_revision,
        )
    if case.profile_revision != payload.expected_profile_revision:
        raise HTTPException(
            status_code=409,
            detail=f"Case profile changed. Current revision is {case.profile_revision}.",
        )
    fact = db.scalar(
        select(CaseProfileFact).where(
            CaseProfileFact.id == fact_id,
            CaseProfileFact.case_id == case_id,
        )
    )
    if fact is None:
        raise HTTPException(status_code=404, detail="Profile fact not found.")
    latest = _active_fact_dispositions(db, case_id, [fact_id]).get(fact_id)
    if latest is not None and latest.action != "reinstated":
        raise HTTPException(status_code=409, detail="The profile fact is no longer active.")
    next_revision = case.profile_revision + 1
    event = CaseProfileFactEvent(
        id=uuid4(),
        case_id=case_id,
        fact_id=fact_id,
        user_id=user_id,
        user_id_snapshot=user_id,
        idempotency_key=payload.idempotency_key,
        request_sha256=request_sha256,
        action="withdrawn",
        profile_revision=next_revision,
        created_at=datetime.now(UTC),
    )
    db.add(event)
    case.profile_revision = next_revision
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        existing = db.scalar(
            select(CaseProfileFactEvent).where(
                CaseProfileFactEvent.case_id == case_id,
                CaseProfileFactEvent.user_id_snapshot == user_id,
                CaseProfileFactEvent.idempotency_key == payload.idempotency_key,
            )
        )
        if existing is None:
            raise
        if existing.request_sha256 != request_sha256:
            raise HTTPException(status_code=409, detail="Fact disposition idempotency key was reused.") from error
        return FactDispositionRead(
            fact_id=existing.fact_id,
            action="withdrawn",
            profile_revision=existing.profile_revision,
        )
    return FactDispositionRead(
        fact_id=fact_id,
        action="withdrawn",
        profile_revision=next_revision,
    )


@router.get(
    "/cases/{case_id}/analysis-requests/{request_id}/review",
    response_model=ProposalReviewList,
)
def get_case_proposal_review(
    case_id: UUID,
    request_id: UUID,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProposalReviewList:
    try:
        _authorize_case(db, user, case_id, write=False)
        response.headers["Cache-Control"] = "no-store"
        return proposal_review_list(db, case_id, request_id)
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        log_failure_event(logger, "proposal_review_lookup_failed", error)
        raise HTTPException(status_code=503, detail="Proposal review is unavailable.") from error


@router.post(
    "/cases/{case_id}/analysis-requests/{request_id}/proposals/{proposal_id}/review",
    response_model=ProposalReviewEventRead,
)
def review_case_proposal(
    case_id: UUID,
    request_id: UUID,
    proposal_id: UUID,
    payload: ProposalReviewCreate,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProposalReviewEventRead:
    try:
        _authorize_case(db, user, case_id, write=True)
        response.headers["Cache-Control"] = "no-store"
        event = record_proposal_review(
            db,
            case_id,
            request_id,
            proposal_id,
            user.id,
            payload,
        )
        return ProposalReviewEventRead(
            id=event.id,
            decision=event.decision,
            edited_value=event.edited_value,
            created_at=event.created_at,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        log_failure_event(logger, "proposal_review_persistence_failed", error)
        raise HTTPException(status_code=503, detail="Proposal review could not be saved.") from error


@router.post("/cases/{case_id}/profile-facts/adoptions", response_model=AdoptionRead)
def adopt_case_profile_facts(
    case_id: UUID,
    payload: AdoptionCreate,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AdoptionRead:
    try:
        _authorize_case(db, user, case_id, write=True)
        response.headers["Cache-Control"] = "no-store"
        return adopt_case_proposals(db, case_id, user.id, payload)
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        log_failure_event(logger, "case_profile_adoption_failed", error)
        raise HTTPException(status_code=503, detail="Selected suggestions could not be adopted.") from error


@router.get("/cases/{case_id}/profile-facts", response_model=ProfileFactsRead)
def get_case_profile_facts(
    case_id: UUID,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProfileFactsRead:
    try:
        _authorize_case(db, user, case_id, write=False)
        response.headers["Cache-Control"] = "no-store"
        return case_profile_facts(db, case_id)
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        log_failure_event(logger, "case_profile_lookup_failed", error)
        raise HTTPException(status_code=503, detail="Case-profile facts are unavailable.") from error


@router.post(
    "/cases/{case_id}/profile-facts/{fact_id}/withdraw",
    response_model=FactDispositionRead,
)
def withdraw_case_profile_fact(
    case_id: UUID,
    fact_id: UUID,
    payload: FactDispositionCreate,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FactDispositionRead:
    try:
        _authorize_case(db, user, case_id, write=True)
        response.headers["Cache-Control"] = "no-store"
        return withdraw_case_fact(db, case_id, fact_id, user.id, payload)
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        log_failure_event(logger, "case_profile_update_failed", error)
        raise HTTPException(status_code=503, detail="Case-profile fact could not be withdrawn.") from error


@router.get(
    "/cases/{case_id}/documents/{document_id}/source-text",
    response_model=SourceTextRead,
)
def get_case_document_source_text(
    case_id: UUID,
    document_id: UUID,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SourceTextRead:
    try:
        _authorize_case(db, user, case_id, write=False)
        response.headers["Cache-Control"] = "no-store"
        return source_text(db, case_id, document_id)
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        log_failure_event(logger, "source_text_lookup_failed", error)
        raise HTTPException(status_code=503, detail="Source text is unavailable.") from error
