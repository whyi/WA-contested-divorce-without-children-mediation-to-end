"""Persist proposal decisions and append-only case-profile facts."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_proposal_review_and_adoption"
down_revision = "0005_document_analysis"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=True)
    timestamp = sa.DateTime(timezone=True)

    op.add_column(
        "cases",
        sa.Column("profile_revision", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_table(
        "analysis_proposal_review_events",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("case_id", uuid_type, nullable=False),
        sa.Column("proposal_id", uuid_type),
        sa.Column("proposal_id_snapshot", uuid_type, nullable=False),
        sa.Column("user_id", uuid_type),
        sa.Column("user_id_snapshot", uuid_type, nullable=False),
        sa.Column("idempotency_key", uuid_type, nullable=False),
        sa.Column("request_sha256", sa.String(length=64), nullable=False),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("edited_value", sa.Text()),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "decision IN ('accepted', 'edited', 'rejected')",
            name="ck_analysis_proposal_review_events_decision",
        ),
        sa.CheckConstraint(
            "(decision = 'edited' AND edited_value IS NOT NULL AND length(trim(edited_value)) > 0) "
            "OR (decision != 'edited' AND edited_value IS NULL)",
            name="ck_analysis_proposal_review_events_edited_value",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["proposal_id"],
            ["document_analysis_proposals.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "case_id",
            "user_id_snapshot",
            "idempotency_key",
            name="uq_analysis_proposal_review_event_idempotency",
        ),
    )
    op.create_index(
        "ix_analysis_proposal_review_events_case_id",
        "analysis_proposal_review_events",
        ["case_id"],
    )
    op.create_index(
        "ix_analysis_proposal_review_events_proposal_id",
        "analysis_proposal_review_events",
        ["proposal_id"],
    )

    op.create_table(
        "case_profile_adoptions",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("case_id", uuid_type, nullable=False),
        sa.Column("user_id", uuid_type),
        sa.Column("user_id_snapshot", uuid_type, nullable=False),
        sa.Column("idempotency_key", uuid_type, nullable=False),
        sa.Column("request_sha256", sa.String(length=64), nullable=False),
        sa.Column("profile_revision_before", sa.Integer(), nullable=False),
        sa.Column("profile_revision_after", sa.Integer(), nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "profile_revision_after = profile_revision_before + 1",
            name="ck_case_profile_adoptions_revision",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "case_id",
            "user_id_snapshot",
            "idempotency_key",
            name="uq_case_profile_adoption_idempotency",
        ),
    )
    op.create_index("ix_case_profile_adoptions_case_id", "case_profile_adoptions", ["case_id"])

    op.create_table(
        "case_profile_facts",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("case_id", uuid_type, nullable=False),
        sa.Column("adoption_id", uuid_type, nullable=False),
        sa.Column("proposal_id_snapshot", uuid_type, nullable=False),
        sa.Column("field_key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("original_value", sa.Text(), nullable=False),
        sa.Column("source_document_id", uuid_type, nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("source_quote", sa.Text(), nullable=False),
        sa.Column("source_page_number", sa.Integer()),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("notice_version", sa.String(length=100), nullable=False),
        sa.Column("review_decision", sa.String(length=16), nullable=False),
        sa.Column("adopted_by_snapshot", uuid_type, nullable=False),
        sa.Column("profile_revision", sa.Integer(), nullable=False),
        sa.Column("adopted_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "source_page_number IS NULL OR source_page_number >= 1",
            name="ck_case_profile_facts_source_page_number",
        ),
        sa.CheckConstraint(
            "review_decision IN ('accepted', 'edited')",
            name="ck_case_profile_facts_review_decision",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["adoption_id"], ["case_profile_adoptions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "case_id",
            "proposal_id_snapshot",
            name="uq_case_profile_fact_case_proposal",
        ),
    )
    op.create_index("ix_case_profile_facts_case_id", "case_profile_facts", ["case_id"])
    op.create_index("ix_case_profile_facts_adoption_id", "case_profile_facts", ["adoption_id"])

    op.create_table(
        "case_profile_fact_events",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("case_id", uuid_type, nullable=False),
        sa.Column("fact_id", uuid_type, nullable=False),
        sa.Column("replacement_fact_id", uuid_type),
        sa.Column("user_id", uuid_type),
        sa.Column("user_id_snapshot", uuid_type, nullable=False),
        sa.Column("idempotency_key", uuid_type, nullable=False),
        sa.Column("request_sha256", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("profile_revision", sa.Integer(), nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "action IN ('withdrawn', 'superseded', 'reinstated')",
            name="ck_case_profile_fact_events_action",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fact_id"], ["case_profile_facts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["replacement_fact_id"],
            ["case_profile_facts.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "case_id",
            "user_id_snapshot",
            "idempotency_key",
            name="uq_case_profile_fact_event_idempotency",
        ),
    )
    op.create_index(
        "ix_case_profile_fact_events_case_id",
        "case_profile_fact_events",
        ["case_id"],
    )
    op.create_index(
        "ix_case_profile_fact_events_fact_id",
        "case_profile_fact_events",
        ["fact_id"],
    )


def downgrade() -> None:
    op.drop_table("case_profile_fact_events")
    op.drop_table("case_profile_facts")
    op.drop_table("case_profile_adoptions")
    op.drop_table("analysis_proposal_review_events")
    op.drop_column("cases", "profile_revision")
