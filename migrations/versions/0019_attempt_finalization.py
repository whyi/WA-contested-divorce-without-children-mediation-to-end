"""Add attempt finalization state and snapshot columns."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0019_attempt_finalization"
down_revision = "0018_case_delegation"
branch_labels = None
depends_on = None

TABLE = "settlement_negotiation_attempts"


def upgrade() -> None:
    op.add_column(TABLE, sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        TABLE,
        sa.Column("finalized_snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(TABLE, sa.Column("finalized_version_ordinal", sa.Integer(), nullable=True))
    op.add_column(
        TABLE, sa.Column("finalized_by_user_id_snapshot", sa.Uuid(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column(TABLE, "finalized_by_user_id_snapshot")
    op.drop_column(TABLE, "finalized_version_ordinal")
    op.drop_column(TABLE, "finalized_snapshot_json")
    op.drop_column(TABLE, "finalized_at")
