"""Freeze settlement attempts only after explicit sent confirmation."""

from alembic import op
import sqlalchemy as sa

revision = "0012_sent_confirmation_freeze"
down_revision = "0011_settlement_attempts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "settlement_negotiation_attempts",
        sa.Column("sent_confirmed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE settlement_negotiation_attempts "
            "SET sent_confirmed_at = frozen_at "
            "WHERE frozen_at IS NOT NULL"
        )
    )


def downgrade() -> None:
    op.drop_column("settlement_negotiation_attempts", "sent_confirmed_at")
