"""Persist signup names and versioned consent without changing existing accounts."""

from alembic import op
import sqlalchemy as sa

revision = "0029_signup_consent"
down_revision = "0028_original_upload_filenames"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("first_name", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("terms_version", sa.String(40), nullable=True))


def downgrade() -> None:
    for column in ("terms_version", "terms_accepted_at", "last_name", "first_name"):
        op.drop_column("users", column)
