"""Retire case delegation and professional accounts.

Restores every delegated case to its owner and converts professional accounts
to general accounts. Legacy delegation tables and columns are left in place.
"""

from alembic import op
import sqlalchemy as sa

revision = "0027_single_general_account"
down_revision = "0026_owner_beta_fixture_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Order matters: revoke delegates before un-suspending owners so the
    # single-operator unique index is never violated.
    op.execute(
        sa.text(
            "UPDATE case_delegation_invitations "
            "SET status = 'revoked', revoked_at = CURRENT_TIMESTAMP "
            "WHERE status IN ('pending', 'accepted')"
        )
    )
    op.execute(
        sa.text(
            "UPDATE case_memberships SET revoked_at = CURRENT_TIMESTAMP "
            "WHERE role = 'delegate' AND revoked_at IS NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE case_memberships SET suspended_at = NULL WHERE suspended_at IS NOT NULL"
        )
    )
    op.execute(
        sa.text("UPDATE users SET account_type = 'party' WHERE account_type = 'professional'")
    )


def downgrade() -> None:
    # Delegations and professional account types are not restored.
    pass
