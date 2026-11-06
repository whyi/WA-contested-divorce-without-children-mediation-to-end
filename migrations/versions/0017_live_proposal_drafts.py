"""Keep proposal draft documents synchronized until sent confirmation."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0017_live_proposal_drafts"
down_revision = "0016_subscription_memberships"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "settlement_proposal_versions",
        sa.Column(
            "downloaded_formats",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("settlement_proposal_versions", "updated_at")
    op.drop_column("settlement_proposal_versions", "downloaded_formats")
