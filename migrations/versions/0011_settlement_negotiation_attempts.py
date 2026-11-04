"""Add immutable, versioned settlement negotiation attempts."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0011_settlement_attempts"
down_revision = "0010_settlement_offer_response"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=True)
    timestamp = sa.DateTime(timezone=True)
    op.create_table(
        "settlement_negotiation_attempts",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("case_id", uuid_type, nullable=False),
        sa.Column("selection_id", uuid_type, nullable=False),
        sa.Column("predecessor_id", uuid_type),
        sa.Column("attempt_ordinal", sa.Integer(), nullable=False),
        sa.Column("snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("frozen_snapshot_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column(
            "editable_state_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("revision", sa.Integer(), server_default="0", nullable=False),
        sa.Column("frozen_at", timestamp),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "attempt_ordinal >= 1",
            name="ck_settlement_negotiation_attempt_ordinal",
        ),
        sa.CheckConstraint(
            "revision >= 0",
            name="ck_settlement_negotiation_attempt_revision",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["selection_id"],
            ["settlement_scenario_selections.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["predecessor_id"],
            ["settlement_negotiation_attempts.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "selection_id",
            name="uq_settlement_negotiation_attempt_selection",
        ),
        sa.UniqueConstraint(
            "case_id",
            "attempt_ordinal",
            name="uq_settlement_negotiation_attempt_case_ordinal",
        ),
        sa.UniqueConstraint(
            "predecessor_id",
            name="uq_settlement_negotiation_attempt_predecessor",
        ),
    )
    op.create_index(
        "ix_settlement_negotiation_attempts_case_id",
        "settlement_negotiation_attempts",
        ["case_id"],
    )
    op.create_index(
        "ix_settlement_negotiation_attempts_predecessor_id",
        "settlement_negotiation_attempts",
        ["predecessor_id"],
    )
    op.create_index(
        "ix_settlement_negotiation_attempts_selection_id",
        "settlement_negotiation_attempts",
        ["selection_id"],
    )


def downgrade() -> None:
    op.drop_table("settlement_negotiation_attempts")
