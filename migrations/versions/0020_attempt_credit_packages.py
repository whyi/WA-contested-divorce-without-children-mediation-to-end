"""Replace recurring tiers and document credits with case attempt credits."""

from alembic import op
import sqlalchemy as sa

revision = "0020_attempt_credit_packages"
down_revision = "0019_attempt_finalization"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cases",
        sa.Column("attempt_credit_balance", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "cases",
        sa.Column("first_finalization_used", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_check_constraint(
        "ck_cases_attempt_credit_balance", "cases", "attempt_credit_balance >= 0"
    )
    op.execute(
        """
        UPDATE cases
        SET first_finalization_used = TRUE
        WHERE EXISTS (
            SELECT 1
            FROM settlement_negotiation_attempts AS attempts
            WHERE attempts.case_id = cases.id
              AND attempts.finalized_at IS NOT NULL
              AND attempts.finalized_snapshot_json IS NOT NULL
        )
        """
    )
    op.execute("UPDATE users SET document_credit_balance = 0")
    op.execute(
        """
        UPDATE document_credit_ledger_entries
        SET source_type = 'legacy_document_credit'
        """
    )
    op.add_column(
        "document_credit_ledger_entries",
        sa.Column("case_id", sa.Uuid(), nullable=True),
    )
    op.execute(
        """
        UPDATE document_credit_ledger_entries AS entries
        SET case_id = versions.case_id
        FROM settlement_proposal_versions AS versions
        WHERE entries.proposal_version_id = versions.id
        """
    )
    op.create_foreign_key(
        "fk_document_credit_ledger_entries_case_id_cases",
        "document_credit_ledger_entries",
        "cases",
        ["case_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_document_credit_ledger_entries_case_id",
        "document_credit_ledger_entries",
        ["case_id"],
    )
    op.create_unique_constraint(
        "uq_document_credit_ledger_case_idempotency",
        "document_credit_ledger_entries",
        ["case_id", "idempotency_key"],
    )

    op.drop_constraint(
        "ck_users_document_credit_balance", "users", type_="check"
    )
    op.drop_column("users", "document_credit_balance")
    op.drop_constraint(
        "ck_users_settlement_attempt_limit", "users", type_="check"
    )
    op.drop_column("users", "settlement_attempt_limit")
    op.drop_constraint("ck_users_subscription_status", "users", type_="check")
    op.drop_constraint("ck_users_subscription_plan", "users", type_="check")
    op.drop_constraint("uq_users_stripe_subscription_id", "users", type_="unique")
    op.drop_column("users", "subscription_cancel_at_period_end")
    op.drop_column("users", "billing_state_event_created_at")
    op.drop_column("users", "subscription_period_end")
    op.drop_column("users", "stripe_subscription_id")
    op.drop_column("users", "subscription_status")
    op.drop_column("users", "subscription_plan")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("subscription_plan", sa.String(length=20), server_default="free", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("subscription_status", sa.String(length=30), server_default="free", nullable=False),
    )
    op.add_column("users", sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True))
    op.create_unique_constraint(
        "uq_users_stripe_subscription_id", "users", ["stripe_subscription_id"]
    )
    op.add_column(
        "users",
        sa.Column("subscription_period_end", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("billing_state_event_created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "subscription_cancel_at_period_end",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_users_subscription_plan",
        "users",
        "subscription_plan IN ('free', 'essential', 'plus', 'pro')",
    )
    op.create_check_constraint(
        "ck_users_subscription_status",
        "users",
        "subscription_status IN ('free', 'legacy', 'incomplete', 'active', 'trialing', "
        "'past_due', 'unpaid', 'canceled', 'incomplete_expired')",
    )
    op.add_column(
        "users",
        sa.Column("settlement_attempt_limit", sa.Integer(), server_default="1", nullable=False),
    )
    op.create_check_constraint(
        "ck_users_settlement_attempt_limit",
        "users",
        "settlement_attempt_limit IN (1, 3, 5, 10)",
    )
    op.add_column(
        "users",
        sa.Column("document_credit_balance", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_check_constraint(
        "ck_users_document_credit_balance", "users", "document_credit_balance >= 0"
    )

    op.drop_constraint(
        "uq_document_credit_ledger_case_idempotency",
        "document_credit_ledger_entries",
        type_="unique",
    )
    op.drop_index(
        "ix_document_credit_ledger_entries_case_id",
        table_name="document_credit_ledger_entries",
    )
    op.drop_constraint(
        "fk_document_credit_ledger_entries_case_id_cases",
        "document_credit_ledger_entries",
        type_="foreignkey",
    )
    op.drop_column("document_credit_ledger_entries", "case_id")
    op.drop_constraint("ck_cases_attempt_credit_balance", "cases", type_="check")
    op.drop_column("cases", "first_finalization_used")
    op.drop_column("cases", "attempt_credit_balance")
