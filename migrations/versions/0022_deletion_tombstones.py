"""Persist tombstones for permanent account, case, and material deletion."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0022_deletion_tombstones"
down_revision = "0021_counteroffer_values"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deletion_tombstones",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scope_type", sa.String(length=20), nullable=False),
        sa.Column("scope_id", sa.Uuid(), nullable=False),
        sa.Column("initiated_by", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "object_keys",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "scope_type IN ('account', 'case', 'document', 'import_item')",
            name="ck_deletion_tombstones_scope_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'completed')",
            name="ck_deletion_tombstones_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scope_type", "scope_id", name="uq_deletion_tombstone_scope"),
    )


def downgrade() -> None:
    op.drop_table("deletion_tombstones")
