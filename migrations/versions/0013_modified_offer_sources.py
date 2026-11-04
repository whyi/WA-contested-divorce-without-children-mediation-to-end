"""Preserve modified-offer source documents on the next attempt."""

from alembic import op
import sqlalchemy as sa

revision = "0013_modified_offer_sources"
down_revision = "0012_sent_confirmation_freeze"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_settlement_offer_response_attachments_kind",
        "settlement_offer_response_attachments",
        type_="check",
    )
    op.create_check_constraint(
        "ck_settlement_offer_response_attachments_kind",
        "settlement_offer_response_attachments",
        "kind IN ('sent_docx', 'sent_xlsx', 'modified_docx', 'modified_xlsx', "
        "'counteroffer', 'accepted_offer', "
        "'modified_source_docx', 'modified_source_xlsx')",
    )
    op.create_index(
        "uq_settlement_offer_response_modified_docx",
        "settlement_offer_response_attachments",
        ["response_id"],
        unique=True,
        postgresql_where=sa.text("kind = 'modified_docx'"),
    )
    op.create_index(
        "uq_settlement_offer_response_modified_xlsx",
        "settlement_offer_response_attachments",
        ["response_id"],
        unique=True,
        postgresql_where=sa.text("kind = 'modified_xlsx'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_settlement_offer_response_modified_xlsx",
        table_name="settlement_offer_response_attachments",
    )
    op.drop_index(
        "uq_settlement_offer_response_modified_docx",
        table_name="settlement_offer_response_attachments",
    )
    op.drop_constraint(
        "ck_settlement_offer_response_attachments_kind",
        "settlement_offer_response_attachments",
        type_="check",
    )
    op.create_check_constraint(
        "ck_settlement_offer_response_attachments_kind",
        "settlement_offer_response_attachments",
        "kind IN ('sent_docx', 'sent_xlsx', 'counteroffer', 'accepted_offer')",
    )
