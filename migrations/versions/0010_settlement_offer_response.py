"""Persist user-recorded settlement offer responses and private attachments."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0010_settlement_offer_response"
down_revision = "0009_cr2a_property_exports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=True)
    timestamp = sa.DateTime(timezone=True)

    op.create_table(
        "settlement_offer_responses",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("case_id", uuid_type, nullable=False),
        sa.Column("selection_id", uuid_type, nullable=False),
        sa.Column("user_id", uuid_type),
        sa.Column("user_id_snapshot", uuid_type, nullable=False),
        sa.Column("outcome", sa.String(length=20)),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "outcome IS NULL OR outcome IN ('counteroffer', 'rejected', 'accepted')",
            name="ck_settlement_offer_responses_outcome",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["selection_id"],
            ["settlement_scenario_selections.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("selection_id", name="uq_settlement_offer_responses_selection"),
    )
    op.create_index(
        "ix_settlement_offer_responses_case_id",
        "settlement_offer_responses",
        ["case_id"],
    )
    op.create_index(
        "ix_settlement_offer_responses_selection_id",
        "settlement_offer_responses",
        ["selection_id"],
    )

    op.create_table(
        "settlement_offer_response_attachments",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("response_id", uuid_type, nullable=False),
        sa.Column("document_id", uuid_type, nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "kind IN ('sent_docx', 'sent_xlsx', 'counteroffer', 'accepted_offer')",
            name="ck_settlement_offer_response_attachments_kind",
        ),
        sa.ForeignKeyConstraint(
            ["response_id"],
            ["settlement_offer_responses.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "response_id",
            "kind",
            "document_id",
            name="uq_settlement_offer_response_attachment_document",
        ),
    )
    op.create_index(
        "ix_settlement_offer_response_attachments_response_id",
        "settlement_offer_response_attachments",
        ["response_id"],
    )
    op.create_index(
        "ix_settlement_offer_response_attachments_document_id",
        "settlement_offer_response_attachments",
        ["document_id"],
    )
    op.create_index(
        "uq_settlement_offer_response_sent_docx",
        "settlement_offer_response_attachments",
        ["response_id"],
        unique=True,
        postgresql_where=sa.text("kind = 'sent_docx'"),
    )
    op.create_index(
        "uq_settlement_offer_response_sent_xlsx",
        "settlement_offer_response_attachments",
        ["response_id"],
        unique=True,
        postgresql_where=sa.text("kind = 'sent_xlsx'"),
    )


def downgrade() -> None:
    op.drop_table("settlement_offer_response_attachments")
    op.drop_table("settlement_offer_responses")
