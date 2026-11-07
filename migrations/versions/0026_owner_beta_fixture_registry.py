"""Track the owner-beta account's synthetic UAT case for safe reset."""

from alembic import op
import sqlalchemy as sa

revision = "0026_owner_beta_fixture_registry"
down_revision = "0025_account_backed_wizard_intake"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "owner_beta_fixture_registry",
        sa.Column(
            "owner_user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "case_id",
            sa.Uuid(),
            sa.ForeignKey("cases.id", ondelete="SET NULL"),
            nullable=True,
            unique=True,
        ),
        sa.Column("fixture_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("owner_beta_fixture_registry")
