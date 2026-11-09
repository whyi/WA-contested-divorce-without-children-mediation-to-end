"""Keep attempts read-only after an accepted case is reopened."""

from alembic import op
import sqlalchemy as sa

revision = "0030_accepted_case_attempt_lock"
down_revision = "0029_signup_consent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cases",
        sa.Column("attempts_locked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE cases SET attempts_locked_at = COALESCE(closed_at, updated_at, CURRENT_TIMESTAMP) "
            "WHERE closed_reason = 'accepted'"
        )
    )


def downgrade() -> None:
    op.drop_column("cases", "attempts_locked_at")
