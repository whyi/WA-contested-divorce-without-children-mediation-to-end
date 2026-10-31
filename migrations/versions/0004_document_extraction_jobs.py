"""Persist asynchronous extraction jobs and page provenance."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_document_extraction_jobs"
down_revision = "0003_material_imports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=True)
    timestamp = sa.DateTime(timezone=True)

    op.add_column(
        "document_extractions",
        sa.Column(
            "pages_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.create_table(
        "document_extraction_jobs",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("document_id", uuid_type, nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("request_id", uuid_type, nullable=False),
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
            "status IN ('queued', 'processing', 'needs_attention', 'failed', 'completed')",
            name="ck_document_extraction_jobs_status",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "document_id",
            "source_sha256",
            "request_id",
            name="uq_document_extraction_job_request",
        ),
    )
    op.create_index(
        "ix_document_extraction_jobs_document_id",
        "document_extraction_jobs",
        ["document_id"],
    )
    op.create_index(
        "ix_document_extraction_jobs_status_created_at",
        "document_extraction_jobs",
        ["status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_extraction_jobs_status_created_at",
        table_name="document_extraction_jobs",
    )
    op.drop_index(
        "ix_document_extraction_jobs_document_id",
        table_name="document_extraction_jobs",
    )
    op.drop_table("document_extraction_jobs")
    op.drop_column("document_extractions", "pages_json")
