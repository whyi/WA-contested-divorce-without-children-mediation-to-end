"""Persist consent-based document analysis requests and proposals."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_document_analysis"
down_revision = "0004_document_extraction_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=True)
    timestamp = sa.DateTime(timezone=True)

    op.create_table(
        "document_analysis_consents",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("case_id", uuid_type, nullable=False),
        sa.Column("user_id", uuid_type, nullable=False),
        sa.Column("request_id", uuid_type, nullable=False),
        sa.Column("notice_version", sa.String(length=100), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("data_sent", sa.Text(), nullable=False),
        sa.Column("data_handling_notice", sa.Text(), nullable=False),
        sa.Column(
            "consented_at",
            timestamp,
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("revoked_at", timestamp),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("request_id", name="uq_document_analysis_consent_request"),
    )
    op.create_table(
        "document_analysis_requests",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("case_id", uuid_type, nullable=False),
        sa.Column("user_id", uuid_type, nullable=False),
        sa.Column("consent_id", uuid_type, nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default="queued",
            nullable=False,
        ),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('queued', 'processing', 'completed', 'partial', 'failed', 'cancelled')",
            name="ck_document_analysis_requests_status",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["consent_id"],
            ["document_analysis_consents.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("consent_id", name="uq_document_analysis_requests_consent"),
    )
    op.create_table(
        "document_analysis_jobs",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("request_id", uuid_type, nullable=False),
        sa.Column("document_id", uuid_type, nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default="queued",
            nullable=False,
        ),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("lease_token", uuid_type),
        sa.Column("lease_expires_at", timestamp),
        sa.Column("error_code", sa.String(length=80)),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", timestamp),
        sa.CheckConstraint(
            "status IN ('queued', 'processing', 'completed', 'partial', 'failed', 'cancelled')",
            name="ck_document_analysis_jobs_status",
        ),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["document_analysis_requests.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "request_id",
            "document_id",
            name="uq_document_analysis_job_request_document",
        ),
    )
    op.create_table(
        "document_analysis_proposals",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("job_id", uuid_type, nullable=False),
        sa.Column("document_id", uuid_type, nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("field_key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("source_quote", sa.Text(), nullable=False),
        sa.Column("source_page_number", sa.Integer()),
        sa.Column("confidence", sa.String(length=10), nullable=False),
        sa.Column("uncertainty", sa.Text(), nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "confidence IN ('high', 'medium', 'low')",
            name="ck_document_analysis_proposals_confidence",
        ),
        sa.CheckConstraint(
            "source_page_number IS NULL OR source_page_number >= 1",
            name="ck_document_analysis_proposals_source_page_number",
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["document_analysis_jobs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_document_analysis_consents_case_id",
        "document_analysis_consents",
        ["case_id"],
    )
    op.create_index(
        "ix_document_analysis_consents_user_id",
        "document_analysis_consents",
        ["user_id"],
    )
    op.create_index(
        "ix_document_analysis_requests_case_id",
        "document_analysis_requests",
        ["case_id"],
    )
    op.create_index(
        "ix_document_analysis_requests_user_id",
        "document_analysis_requests",
        ["user_id"],
    )
    op.create_index(
        "ix_document_analysis_jobs_request_id",
        "document_analysis_jobs",
        ["request_id"],
    )
    op.create_index(
        "ix_document_analysis_jobs_document_id",
        "document_analysis_jobs",
        ["document_id"],
    )
    op.create_index(
        "ix_document_analysis_jobs_status_created_at",
        "document_analysis_jobs",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_document_analysis_proposals_job_id",
        "document_analysis_proposals",
        ["job_id"],
    )
    op.create_index(
        "ix_document_analysis_proposals_document_id",
        "document_analysis_proposals",
        ["document_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_analysis_proposals_document_id",
        table_name="document_analysis_proposals",
    )
    op.drop_index(
        "ix_document_analysis_proposals_job_id",
        table_name="document_analysis_proposals",
    )
    op.drop_index(
        "ix_document_analysis_jobs_status_created_at",
        table_name="document_analysis_jobs",
    )
    op.drop_index(
        "ix_document_analysis_jobs_document_id",
        table_name="document_analysis_jobs",
    )
    op.drop_index(
        "ix_document_analysis_jobs_request_id",
        table_name="document_analysis_jobs",
    )
    op.drop_index(
        "ix_document_analysis_requests_user_id",
        table_name="document_analysis_requests",
    )
    op.drop_index(
        "ix_document_analysis_requests_case_id",
        table_name="document_analysis_requests",
    )
    op.drop_index(
        "ix_document_analysis_consents_user_id",
        table_name="document_analysis_consents",
    )
    op.drop_index(
        "ix_document_analysis_consents_case_id",
        table_name="document_analysis_consents",
    )
    op.drop_table("document_analysis_proposals")
    op.drop_table("document_analysis_jobs")
    op.drop_table("document_analysis_requests")
    op.drop_table("document_analysis_consents")
