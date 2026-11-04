"""Add Stripe-backed subscription membership and webhook idempotency."""

from alembic import op
import sqlalchemy as sa

revision = "0016_subscription_memberships"
down_revision = "0015_document_credit_versions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("subscription_plan", sa.String(length=20), server_default="free", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("subscription_status", sa.String(length=30), server_default="free", nullable=False),
    )
    op.add_column("users", sa.Column("stripe_customer_id", sa.String(length=255), nullable=True))
    op.add_column(
        "users",
        sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True),
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
    op.execute(
        """
        UPDATE users
        SET subscription_plan = CASE settlement_attempt_limit
            WHEN 3 THEN 'essential'
            WHEN 5 THEN 'plus'
            WHEN 10 THEN 'pro'
            ELSE 'free'
        END,
        subscription_status = CASE
            WHEN settlement_attempt_limit IN (3, 5, 10) THEN 'legacy'
            ELSE 'free'
        END
        """
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
    op.create_unique_constraint(
        "uq_users_stripe_customer_id",
        "users",
        ["stripe_customer_id"],
    )
    op.create_unique_constraint(
        "uq_users_stripe_subscription_id",
        "users",
        ["stripe_subscription_id"],
    )
    op.alter_column(
        "document_credit_ledger_entries",
        "proposal_version_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )
    op.add_column(
        "document_credit_ledger_entries",
        sa.Column(
            "source_type",
            sa.String(length=30),
            server_default="proposal_export",
            nullable=False,
        ),
    )
    op.add_column(
        "document_credit_ledger_entries",
        sa.Column("source_reference", sa.String(length=255), nullable=True),
    )
    op.create_table(
        "billing_webhook_events",
        sa.Column("event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('processing', 'processed', 'ignored')",
            name="ck_billing_webhook_events_status",
        ),
        sa.PrimaryKeyConstraint("event_id"),
    )


def downgrade() -> None:
    op.drop_table("billing_webhook_events")
    op.drop_column("document_credit_ledger_entries", "source_reference")
    op.drop_column("document_credit_ledger_entries", "source_type")
    op.alter_column(
        "document_credit_ledger_entries",
        "proposal_version_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )
    op.drop_constraint("uq_users_stripe_subscription_id", "users", type_="unique")
    op.drop_constraint("uq_users_stripe_customer_id", "users", type_="unique")
    op.drop_constraint("ck_users_subscription_status", "users", type_="check")
    op.drop_constraint("ck_users_subscription_plan", "users", type_="check")
    op.drop_column("users", "subscription_cancel_at_period_end")
    op.drop_column("users", "billing_state_event_created_at")
    op.drop_column("users", "subscription_period_end")
    op.drop_column("users", "stripe_subscription_id")
    op.drop_column("users", "stripe_customer_id")
    op.drop_column("users", "subscription_status")
    op.drop_column("users", "subscription_plan")
