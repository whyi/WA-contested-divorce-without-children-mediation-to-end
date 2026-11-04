"""Add server-managed attempt limits and immutable proposal issuance."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0014_negotiation_attempt_limits"
down_revision = "0013_modified_offer_sources"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "settlement_attempt_limit",
            sa.Integer(),
            server_default="1",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_users_settlement_attempt_limit",
        "users",
        "settlement_attempt_limit IN (1, 3, 5, 10)",
    )
    op.add_column(
        "settlement_negotiation_attempts",
        sa.Column("proposal_issued_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "settlement_negotiation_attempts",
        sa.Column("proposal_terms_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "settlement_negotiation_attempts",
        sa.Column(
            "proposal_scenario_result_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("settlement_negotiation_attempts", "proposal_scenario_result_json")
    op.drop_column("settlement_negotiation_attempts", "proposal_terms_json")
    op.drop_column("settlement_negotiation_attempts", "proposal_issued_at")
    op.drop_constraint(
        "ck_users_settlement_attempt_limit",
        "users",
        type_="check",
    )
    op.drop_column("users", "settlement_attempt_limit")
