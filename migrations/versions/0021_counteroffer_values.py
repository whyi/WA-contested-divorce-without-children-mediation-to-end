"""Add user-recorded counteroffer values to offer responses."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0021_counteroffer_values"
down_revision = "0020_attempt_credit_packages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "settlement_offer_responses",
        sa.Column("counteroffer_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("settlement_offer_responses", "counteroffer_json")
