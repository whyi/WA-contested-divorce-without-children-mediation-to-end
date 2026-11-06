"""Add reversible case closure and lifecycle events."""

from alembic import op
import sqlalchemy as sa

revision = "0017_case_closure_and_events"
down_revision = "0016_subscription_memberships"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cases", sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("cases", sa.Column("closed_reason", sa.String(length=20), nullable=True))
    op.add_column("cases", sa.Column("status_before_close", sa.String(length=20), nullable=True))
    op.create_check_constraint(
        "ck_cases_closed_reason",
        "cases",
        "closed_reason IS NULL OR closed_reason IN ('accepted', 'stopped', 'closed')",
    )
    op.execute(
        "UPDATE cases SET closed_at = updated_at, closed_reason = 'accepted', "
        "status_before_close = 'settlement' WHERE status = 'finalized'"
    )
    op.create_table(
        "case_lifecycle_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("user_id_snapshot", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.String(length=20), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "event_type IN ('closed', 'reopened')", name="ck_case_lifecycle_events_type"
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_case_lifecycle_events_case_id", "case_lifecycle_events", ["case_id"])


def downgrade() -> None:
    op.drop_index("ix_case_lifecycle_events_case_id", table_name="case_lifecycle_events")
    op.drop_table("case_lifecycle_events")
    op.drop_constraint("ck_cases_closed_reason", "cases", type_="check")
    op.drop_column("cases", "status_before_close")
    op.drop_column("cases", "closed_reason")
    op.drop_column("cases", "closed_at")
