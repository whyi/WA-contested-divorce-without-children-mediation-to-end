"""Store immutable proposal versions and charge document credits atomically."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0015_document_credit_versions"
down_revision = "0014_negotiation_attempt_limits"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("document_credit_balance", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_check_constraint(
        "ck_users_document_credit_balance",
        "users",
        "document_credit_balance >= 0",
    )
    op.add_column(
        "settlement_negotiation_attempts",
        sa.Column("proposal_version_ordinal", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "settlement_negotiation_attempts",
        sa.Column("proposal_draft_unlocked", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_check_constraint(
        "ck_settlement_negotiation_attempt_proposal_version",
        "settlement_negotiation_attempts",
        "proposal_version_ordinal >= 0",
    )
    op.create_table(
        "settlement_proposal_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("user_id_snapshot", sa.Uuid(), nullable=False),
        sa.Column("version_ordinal", sa.Integer(), nullable=False),
        sa.Column("request_sha256", sa.String(length=64), nullable=False),
        sa.Column("terms_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "scenario_result_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("docx_content", sa.LargeBinary(), nullable=False),
        sa.Column("xlsx_content", sa.LargeBinary(), nullable=False),
        sa.Column("credit_cost", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "version_ordinal >= 1",
            name="ck_settlement_proposal_version_ordinal",
        ),
        sa.CheckConstraint(
            "credit_cost IN (0, 1)",
            name="ck_settlement_proposal_version_credit_cost",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["attempt_id"],
            ["settlement_negotiation_attempts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "attempt_id",
            "version_ordinal",
            name="uq_settlement_proposal_version_attempt_ordinal",
        ),
    )
    op.create_index(
        "ix_settlement_proposal_versions_case_id",
        "settlement_proposal_versions",
        ["case_id"],
    )
    op.create_index(
        "ix_settlement_proposal_versions_attempt_id",
        "settlement_proposal_versions",
        ["attempt_id"],
    )
    op.create_index(
        "ix_settlement_proposal_versions_user_id_snapshot",
        "settlement_proposal_versions",
        ["user_id_snapshot"],
    )
    op.create_table(
        "document_credit_ledger_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("proposal_version_id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("delta <> 0", name="ck_document_credit_ledger_delta"),
        sa.CheckConstraint("balance_after >= 0", name="ck_document_credit_ledger_balance"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["proposal_version_id"],
            ["settlement_proposal_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_document_credit_ledger_user_idempotency",
        ),
    )
    op.create_index(
        "ix_document_credit_ledger_entries_user_id",
        "document_credit_ledger_entries",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_document_credit_ledger_entries_user_id", table_name="document_credit_ledger_entries")
    op.drop_table("document_credit_ledger_entries")
    op.drop_index(
        "ix_settlement_proposal_versions_user_id_snapshot",
        table_name="settlement_proposal_versions",
    )
    op.drop_index(
        "ix_settlement_proposal_versions_attempt_id",
        table_name="settlement_proposal_versions",
    )
    op.drop_index(
        "ix_settlement_proposal_versions_case_id",
        table_name="settlement_proposal_versions",
    )
    op.drop_table("settlement_proposal_versions")
    op.drop_constraint(
        "ck_settlement_negotiation_attempt_proposal_version",
        "settlement_negotiation_attempts",
        type_="check",
    )
    op.drop_column("settlement_negotiation_attempts", "proposal_draft_unlocked")
    op.drop_column("settlement_negotiation_attempts", "proposal_version_ordinal")
    op.drop_constraint("ck_users_document_credit_balance", "users", type_="check")
    op.drop_column("users", "document_credit_balance")
