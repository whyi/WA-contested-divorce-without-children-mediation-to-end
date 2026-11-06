"""Add account types, suspended memberships and case delegation invitations."""

from alembic import op
import sqlalchemy as sa

revision = "0018_case_delegation"
down_revision = "0017_case_closure_and_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("account_type", sa.String(length=20), server_default="party", nullable=False),
    )
    op.create_check_constraint(
        "ck_users_account_type", "users", "account_type IN ('party', 'professional')"
    )
    op.add_column(
        "case_memberships",
        sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.drop_constraint("ck_case_memberships_role", "case_memberships", type_="check")
    op.create_check_constraint(
        "ck_case_memberships_role",
        "case_memberships",
        "role IN ('owner', 'editor', 'viewer', 'delegate')",
    )
    op.create_index(
        "uq_case_membership_single_operator",
        "case_memberships",
        ["case_id"],
        unique=True,
        postgresql_where=sa.text("revoked_at IS NULL AND suspended_at IS NULL AND role IN ('owner', 'delegate')"),
    )
    op.create_table(
        "case_delegation_invitations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("invitee_email", sa.String(length=320), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("delegate_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'accepted', 'revoked', 'expired')",
            name="ck_case_delegation_invitations_status",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["delegate_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        "ix_case_delegation_invitations_case_id", "case_delegation_invitations", ["case_id"]
    )
    op.create_index(
        "uq_case_delegation_open_invitation",
        "case_delegation_invitations",
        ["case_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('pending', 'accepted')"),
    )


def downgrade() -> None:
    op.drop_table("case_delegation_invitations")
    op.drop_index("uq_case_membership_single_operator", table_name="case_memberships")
    op.execute("DELETE FROM case_memberships WHERE role = 'delegate'")
    op.drop_constraint("ck_case_memberships_role", "case_memberships", type_="check")
    op.create_check_constraint(
        "ck_case_memberships_role", "case_memberships", "role IN ('owner', 'editor', 'viewer')"
    )
    op.drop_column("case_memberships", "suspended_at")
    op.drop_constraint("ck_users_account_type", "users", type_="check")
    op.drop_column("users", "account_type")
