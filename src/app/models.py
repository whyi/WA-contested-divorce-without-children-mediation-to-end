from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Case(Base):
    __tablename__ = "cases"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'mediation', 'settlement', 'finalized')",
            name="ck_cases_status",
        ),
        CheckConstraint(
            "closed_reason IS NULL OR closed_reason IN ('accepted', 'stopped', 'closed')",
            name="ck_cases_closed_reason",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    asset_liability_inventory: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    relationship_milestones: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    property_assets: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    profile_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    settlement_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_reason: Mapped[str | None] = mapped_column(String(20))
    status_before_close: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    negotiations: Mapped[list["NegotiationEvent"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )


class CaseLifecycleEvent(Base):
    __tablename__ = "case_lifecycle_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('closed', 'reopened')",
            name="ck_case_lifecycle_events_type",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    user_id_snapshot: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class NegotiationEvent(Base):
    __tablename__ = "negotiation_events"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    case: Mapped[Case] = relationship(back_populates="negotiations")


class SettlementPlanningConsentEvent(Base):
    __tablename__ = "settlement_planning_consent_events"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    user_id_snapshot: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    notice_version: Mapped[str] = mapped_column(String(100), nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    provider: Mapped[str | None] = mapped_column(String(100))
    model_id: Mapped[str | None] = mapped_column(String(255))
    region: Mapped[str | None] = mapped_column(String(100))
    purpose: Mapped[str | None] = mapped_column(Text)
    data_sent: Mapped[str | None] = mapped_column(Text)
    data_handling_notice: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SettlementScenarioRun(Base):
    __tablename__ = "settlement_scenario_runs"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    user_id_snapshot: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    profile_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    settlement_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    axes_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    scenario_results_json: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
    ranking_json: Mapped[dict | None] = mapped_column(JSONB)
    ranking_error: Mapped[str | None] = mapped_column(Text)
    input_fact_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    provider: Mapped[str | None] = mapped_column(String(100))
    model_id: Mapped[str | None] = mapped_column(String(255))
    region: Mapped[str | None] = mapped_column(String(100))
    notice_version: Mapped[str | None] = mapped_column(String(100))
    data_handling_notice: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SettlementLedgerEvent(Base):
    __tablename__ = "settlement_ledger_events"
    __table_args__ = (
        UniqueConstraint(
            "case_id",
            "asset_id",
            "effective_date",
            "sequence_number",
            name="uq_settlement_ledger_asset_event_order",
        ),
        UniqueConstraint(
            "case_id",
            "user_id_snapshot",
            "idempotency_key",
            name="uq_settlement_ledger_event_idempotency",
        ),
        CheckConstraint("sequence_number >= 0", name="ck_settlement_ledger_sequence"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    asset_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    asset_name: Mapped[str] = mapped_column(String(200), nullable=False)
    asset_kind: Mapped[str] = mapped_column(String(8), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    event_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    user_id_snapshot: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    idempotency_key: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    request_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    profile_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    settlement_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SettlementScenarioSelection(Base):
    __tablename__ = "settlement_scenario_selections"
    __table_args__ = (
        UniqueConstraint(
            "case_id",
            "user_id_snapshot",
            "idempotency_key",
            name="uq_settlement_scenario_selection_idempotency",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    user_id_snapshot: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    idempotency_key: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    request_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    run_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "settlement_scenario_runs.id",
            name="fk_settlement_scenario_selections_run_id",
            ondelete="CASCADE",
        ),
        index=True,
    )
    scenario_id: Mapped[str] = mapped_column(String(80), nullable=False)
    scenario_result_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    profile_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    settlement_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ExportProviderConnection(Base):
    __tablename__ = "export_provider_connections"
    __table_args__ = (
        CheckConstraint(
            "provider IN ('google_drive', 'dropbox')",
            name="ck_export_provider_connections_provider",
        ),
        UniqueConstraint(
            "user_id",
            "provider",
            name="uq_export_provider_connection_user_provider",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    account_label: Mapped[str] = mapped_column(String(320), nullable=False)
    encrypted_access_token: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    encrypted_refresh_token: Mapped[bytes | None] = mapped_column(LargeBinary)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scopes: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ExportDeliveryEvent(Base):
    __tablename__ = "export_delivery_events"
    __table_args__ = (
        CheckConstraint(
            "channel IN ('google_drive', 'dropbox', 'email')",
            name="ck_export_delivery_events_channel",
        ),
        CheckConstraint(
            "outcome IN ('pending', 'success', 'partial', 'failed')",
            name="ck_export_delivery_events_outcome",
        ),
        CheckConstraint("file_count BETWEEN 0 AND 2", name="ck_export_delivery_events_file_count"),
        UniqueConstraint(
            "user_id_snapshot",
            "idempotency_key",
            name="uq_export_delivery_event_idempotency",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    selection_id: Mapped[UUID] = mapped_column(
        ForeignKey("settlement_scenario_selections.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    user_id_snapshot: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    destination_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    request_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    outcome: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    file_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    idempotency_key: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SettlementOfferResponse(Base):
    __tablename__ = "settlement_offer_responses"
    __table_args__ = (
        UniqueConstraint("selection_id", name="uq_settlement_offer_responses_selection"),
        CheckConstraint(
            "outcome IS NULL OR outcome IN ('counteroffer', 'rejected', 'accepted')",
            name="ck_settlement_offer_responses_outcome",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    selection_id: Mapped[UUID] = mapped_column(
        ForeignKey("settlement_scenario_selections.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    user_id_snapshot: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    outcome: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    attachments: Mapped[list["SettlementOfferResponseAttachment"]] = relationship(
        back_populates="response", cascade="all, delete-orphan"
    )


class SettlementOfferResponseAttachment(Base):
    __tablename__ = "settlement_offer_response_attachments"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('sent_docx', 'sent_xlsx', 'modified_docx', 'modified_xlsx', "
            "'counteroffer', 'accepted_offer', "
            "'modified_source_docx', 'modified_source_xlsx')",
            name="ck_settlement_offer_response_attachments_kind",
        ),
        UniqueConstraint(
            "response_id",
            "kind",
            "document_id",
            name="uq_settlement_offer_response_attachment_document",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    response_id: Mapped[UUID] = mapped_column(
        ForeignKey("settlement_offer_responses.id", ondelete="CASCADE"), index=True
    )
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    response: Mapped[SettlementOfferResponse] = relationship(back_populates="attachments")


class SettlementNegotiationAttempt(Base):
    __tablename__ = "settlement_negotiation_attempts"
    __table_args__ = (
        UniqueConstraint("selection_id", name="uq_settlement_negotiation_attempt_selection"),
        UniqueConstraint(
            "case_id",
            "attempt_ordinal",
            name="uq_settlement_negotiation_attempt_case_ordinal",
        ),
        UniqueConstraint("predecessor_id", name="uq_settlement_negotiation_attempt_predecessor"),
        CheckConstraint("attempt_ordinal >= 1", name="ck_settlement_negotiation_attempt_ordinal"),
        CheckConstraint("revision >= 0", name="ck_settlement_negotiation_attempt_revision"),
        CheckConstraint(
            "proposal_version_ordinal >= 0",
            name="ck_settlement_negotiation_attempt_proposal_version",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    selection_id: Mapped[UUID] = mapped_column(
        ForeignKey("settlement_scenario_selections.id", ondelete="CASCADE"), index=True
    )
    predecessor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("settlement_negotiation_attempts.id", ondelete="CASCADE"), index=True
    )
    attempt_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    frozen_snapshot_json: Mapped[dict | None] = mapped_column(JSONB)
    editable_state_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    proposal_issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    proposal_terms_json: Mapped[dict | None] = mapped_column(JSONB)
    proposal_scenario_result_json: Mapped[dict | None] = mapped_column(JSONB)
    proposal_version_ordinal: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    proposal_draft_unlocked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    frozen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SettlementProposalVersion(Base):
    __tablename__ = "settlement_proposal_versions"
    __table_args__ = (
        UniqueConstraint(
            "attempt_id",
            "version_ordinal",
            name="uq_settlement_proposal_version_attempt_ordinal",
        ),
        CheckConstraint("version_ordinal >= 1", name="ck_settlement_proposal_version_ordinal"),
        CheckConstraint("credit_cost IN (0, 1)", name="ck_settlement_proposal_version_credit_cost"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    attempt_id: Mapped[UUID] = mapped_column(
        ForeignKey("settlement_negotiation_attempts.id", ondelete="CASCADE"), index=True
    )
    user_id_snapshot: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    version_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    request_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    terms_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    scenario_result_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    docx_content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    xlsx_content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    credit_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class DocumentCreditLedgerEntry(Base):
    __tablename__ = "document_credit_ledger_entries"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_document_credit_ledger_user_idempotency",
        ),
        CheckConstraint("delta <> 0", name="ck_document_credit_ledger_delta"),
        CheckConstraint("balance_after >= 0", name="ck_document_credit_ledger_balance"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    proposal_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("settlement_proposal_versions.id", ondelete="RESTRICT"), nullable=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="proposal_export", server_default="proposal_export"
    )
    source_reference: Mapped[str | None] = mapped_column(String(255))
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class BillingWebhookEvent(Base):
    __tablename__ = "billing_webhook_events"
    __table_args__ = (
        CheckConstraint(
            "status IN ('processing', 'processed', 'ignored')",
            name="ck_billing_webhook_events_status",
        ),
    )

    event_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="processing")
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    object_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    extension: Mapped[str] = mapped_column(String(10), nullable=False)
    media_type: Mapped[str] = mapped_column(String(120), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    extractions: Mapped[list["DocumentExtraction"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class MaterialImportBatch(Base):
    __tablename__ = "material_import_batches"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MaterialImportItem(Base):
    __tablename__ = "material_import_items"
    __table_args__ = (
        UniqueConstraint("batch_id", "item_id", name="uq_material_import_item_batch_item"),
        UniqueConstraint("document_id", name="uq_material_import_item_document"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    batch_id: Mapped[UUID] = mapped_column(
        ForeignKey("material_import_batches.id", ondelete="CASCADE"), index=True
    )
    item_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )


class DocumentExtraction(Base):
    __tablename__ = "document_extractions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    pages_json: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    review_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending_review")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped[Document] = relationship(back_populates="extractions")


class DocumentExtractionJob(Base):
    __tablename__ = "document_extraction_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'processing', 'needs_attention', 'failed', 'completed')",
            name="ck_document_extraction_jobs_status",
        ),
        UniqueConstraint(
            "document_id",
            "source_sha256",
            "request_id",
            name="uq_document_extraction_job_request",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="queued")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lease_token: Mapped[UUID | None] = mapped_column(Uuid)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DocumentAnalysisConsent(Base):
    __tablename__ = "document_analysis_consents"
    __table_args__ = (
        UniqueConstraint(
            "request_id",
            name="uq_document_analysis_consent_request",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    request_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    notice_version: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    data_sent: Mapped[str] = mapped_column(Text, nullable=False)
    data_handling_notice: Mapped[str] = mapped_column(Text, nullable=False)
    consented_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DocumentAnalysisRequest(Base):
    __tablename__ = "document_analysis_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'processing', 'completed', 'partial', 'failed', 'cancelled')",
            name="ck_document_analysis_requests_status",
        ),
        UniqueConstraint(
            "consent_id",
            name="uq_document_analysis_requests_consent",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    consent_id: Mapped[UUID] = mapped_column(
        ForeignKey("document_analysis_consents.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="queued")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class DocumentAnalysisJob(Base):
    __tablename__ = "document_analysis_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'processing', 'completed', 'partial', 'failed', 'cancelled')",
            name="ck_document_analysis_jobs_status",
        ),
        UniqueConstraint(
            "request_id",
            "document_id",
            name="uq_document_analysis_job_request_document",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(
        ForeignKey("document_analysis_requests.id", ondelete="CASCADE"), index=True
    )
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="queued")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lease_token: Mapped[UUID | None] = mapped_column(Uuid)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DocumentAnalysisProposal(Base):
    __tablename__ = "document_analysis_proposals"
    __table_args__ = (
        CheckConstraint(
            "confidence IN ('high', 'medium', 'low')",
            name="ck_document_analysis_proposals_confidence",
        ),
        CheckConstraint(
            "source_page_number IS NULL OR source_page_number >= 1",
            name="ck_document_analysis_proposals_source_page_number",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("document_analysis_jobs.id", ondelete="CASCADE"), index=True
    )
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    field_key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    source_quote: Mapped[str] = mapped_column(Text, nullable=False)
    source_page_number: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[str] = mapped_column(String(10), nullable=False)
    uncertainty: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ProposalReviewEvent(Base):
    __tablename__ = "analysis_proposal_review_events"
    __table_args__ = (
        CheckConstraint(
            "decision IN ('accepted', 'edited', 'rejected')",
            name="ck_analysis_proposal_review_events_decision",
        ),
        CheckConstraint(
            "(decision = 'edited' AND edited_value IS NOT NULL AND length(trim(edited_value)) > 0) "
            "OR (decision != 'edited' AND edited_value IS NULL)",
            name="ck_analysis_proposal_review_events_edited_value",
        ),
        UniqueConstraint(
            "case_id",
            "user_id_snapshot",
            "idempotency_key",
            name="uq_analysis_proposal_review_event_idempotency",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    proposal_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("document_analysis_proposals.id", ondelete="SET NULL"), index=True
    )
    proposal_id_snapshot: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    user_id_snapshot: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    idempotency_key: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    request_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    edited_value: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CaseProfileAdoption(Base):
    __tablename__ = "case_profile_adoptions"
    __table_args__ = (
        CheckConstraint(
            "profile_revision_after = profile_revision_before + 1",
            name="ck_case_profile_adoptions_revision",
        ),
        UniqueConstraint(
            "case_id",
            "user_id_snapshot",
            "idempotency_key",
            name="uq_case_profile_adoption_idempotency",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    user_id_snapshot: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    idempotency_key: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    request_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    profile_revision_before: Mapped[int] = mapped_column(Integer, nullable=False)
    profile_revision_after: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    facts: Mapped[list["CaseProfileFact"]] = relationship(
        back_populates="adoption", cascade="all, delete-orphan"
    )


class CaseProfileFact(Base):
    __tablename__ = "case_profile_facts"
    __table_args__ = (
        UniqueConstraint(
            "case_id",
            "proposal_id_snapshot",
            name="uq_case_profile_fact_case_proposal",
        ),
        CheckConstraint(
            "source_page_number IS NULL OR source_page_number >= 1",
            name="ck_case_profile_facts_source_page_number",
        ),
        CheckConstraint(
            "review_decision IN ('accepted', 'edited')",
            name="ck_case_profile_facts_review_decision",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    adoption_id: Mapped[UUID] = mapped_column(
        ForeignKey("case_profile_adoptions.id", ondelete="CASCADE"), index=True
    )
    proposal_id_snapshot: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    field_key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    original_value: Mapped[str] = mapped_column(Text, nullable=False)
    source_document_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    source_quote: Mapped[str] = mapped_column(Text, nullable=False)
    source_page_number: Mapped[int | None] = mapped_column(Integer)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    notice_version: Mapped[str] = mapped_column(String(100), nullable=False)
    review_decision: Mapped[str] = mapped_column(String(16), nullable=False)
    adopted_by_snapshot: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    profile_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    adopted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    adoption: Mapped[CaseProfileAdoption] = relationship(back_populates="facts")


class CaseProfileFactEvent(Base):
    __tablename__ = "case_profile_fact_events"
    __table_args__ = (
        CheckConstraint(
            "action IN ('withdrawn', 'superseded', 'reinstated')",
            name="ck_case_profile_fact_events_action",
        ),
        UniqueConstraint(
            "case_id",
            "user_id_snapshot",
            "idempotency_key",
            name="uq_case_profile_fact_event_idempotency",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    fact_id: Mapped[UUID] = mapped_column(
        ForeignKey("case_profile_facts.id", ondelete="CASCADE"), index=True
    )
    replacement_fact_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("case_profile_facts.id", ondelete="SET NULL")
    )
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    user_id_snapshot: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    idempotency_key: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    request_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    profile_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending_verification', 'active', 'locked', 'disabled')",
            name="ck_users_status",
        ),
        CheckConstraint(
            "settlement_attempt_limit IN (1, 3, 5, 10)",
            name="ck_users_settlement_attempt_limit",
        ),
        CheckConstraint(
            "document_credit_balance >= 0",
            name="ck_users_document_credit_balance",
        ),
        CheckConstraint(
            "subscription_plan IN ('free', 'essential', 'plus', 'pro')",
            name="ck_users_subscription_plan",
        ),
        CheckConstraint(
            "subscription_status IN ('free', 'legacy', 'incomplete', 'active', 'trialing', 'past_due', 'unpaid', 'canceled', 'incomplete_expired')",
            name="ck_users_subscription_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending_verification")
    settlement_attempt_limit: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )
    document_credit_balance: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    subscription_plan: Mapped[str] = mapped_column(
        String(20), nullable=False, default="free", server_default=text("'free'")
    )
    subscription_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="free", server_default=text("'free'")
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    subscription_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    billing_state_event_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    subscription_cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    sessions: Mapped[list["AuthSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    external_identities: Mapped[list["ExternalIdentity"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    case_memberships: Mapped[list["CaseMembership"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


def user_settlement_attempt_limit(user: User) -> int:
    from app.subscription_plans import user_settlement_attempt_limit as plan_attempt_limit

    return plan_attempt_limit(user)


class ExternalIdentity(Base):
    __tablename__ = "external_identities"
    __table_args__ = (
        CheckConstraint("provider IN ('google')", name="ck_external_identities_provider"),
        UniqueConstraint(
            "provider", "provider_subject", name="uq_external_identity_provider_subject"
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    provider_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_email: Mapped[str | None] = mapped_column(String(320))
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="external_identities")


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    family_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    idle_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    absolute_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoke_reason: Mapped[str | None] = mapped_column(String(80))

    user: Mapped[User] = relationship(back_populates="sessions")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth_sessions.id", ondelete="CASCADE"), index=True
    )
    jti_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    session: Mapped[AuthSession] = relationship(back_populates="refresh_tokens")


class AuthToken(Base):
    __tablename__ = "auth_tokens"
    __table_args__ = (
        CheckConstraint(
            "purpose IN ('email_verification', 'password_reset')",
            name="ck_auth_tokens_purpose",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    purpose: Mapped[str] = mapped_column(String(30), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TotpCredential(Base):
    __tablename__ = "totp_credentials"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    encrypted_secret: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    pending: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_used_step: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PasskeyCredential(Base):
    __tablename__ = "passkey_credentials"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    credential_id: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    public_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    sign_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    transports: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuthChallenge(Base):
    __tablename__ = "auth_challenges"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    purpose: Mapped[str] = mapped_column(String(40), nullable=False)
    challenge: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    context: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class RecoveryCode(Base):
    __tablename__ = "recovery_codes"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuthRateLimit(Base):
    __tablename__ = "auth_rate_limits"

    key_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False)


class AuthAuditEvent(Base):
    __tablename__ = "auth_audit_events"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    outcome: Mapped[str] = mapped_column(String(30), nullable=False)
    context: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CaseMembership(Base):
    __tablename__ = "case_memberships"
    __table_args__ = (
        CheckConstraint("role IN ('owner', 'editor', 'viewer')", name="ck_case_memberships_role"),
        UniqueConstraint("case_id", "user_id", name="uq_case_membership_user_case"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="owner")
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="case_memberships")
