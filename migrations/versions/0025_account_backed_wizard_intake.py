"""Persist authenticated wizard intake drafts per case."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0025_account_backed_wizard_intake"
down_revision = "0024_live_proposal_drafts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cases",
        sa.Column(
            "wizard_intake_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "cases",
        sa.Column(
            "wizard_intake_revision",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("cases", "wizard_intake_revision")
    op.drop_column("cases", "wizard_intake_json")
