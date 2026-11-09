"""Preserve original upload filenames and retry unfinished confirmed overwrites."""

from alembic import op
import sqlalchemy as sa

revision = "0028_original_upload_filenames"
down_revision = "0027_single_general_account"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("original_filename", sa.String(1024), nullable=True))
    op.add_column("documents", sa.Column("overwrite_document_id", sa.Uuid(), nullable=True))
    op.create_index("ix_documents_case_filename", "documents", ["case_id", "original_filename"])


def downgrade() -> None:
    op.drop_index("ix_documents_case_filename", table_name="documents")
    op.drop_column("documents", "overwrite_document_id")
    op.drop_column("documents", "original_filename")
