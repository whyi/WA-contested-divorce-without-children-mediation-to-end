"""Persist per-user material-import batches and idempotent file items."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_material_imports"
down_revision = "0002_authentication"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=True)
    timestamp = sa.DateTime(timezone=True)

    op.create_table(
        "material_import_batches",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("user_id", uuid_type, nullable=False),
        sa.Column("case_id", uuid_type, nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_material_import_batches_user_id", "material_import_batches", ["user_id"]
    )
    op.create_index(
        "ix_material_import_batches_case_id", "material_import_batches", ["case_id"]
    )
    op.create_table(
        "material_import_items",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("batch_id", uuid_type, nullable=False),
        sa.Column("item_id", uuid_type, nullable=False),
        sa.Column("document_id", uuid_type, nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["material_import_batches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("batch_id", "item_id", name="uq_material_import_item_batch_item"),
        sa.UniqueConstraint("document_id", name="uq_material_import_item_document"),
    )
    op.create_index("ix_material_import_items_batch_id", "material_import_items", ["batch_id"])


def downgrade() -> None:
    op.drop_index("ix_material_import_items_batch_id", table_name="material_import_items")
    op.drop_table("material_import_items")
    op.drop_index("ix_material_import_batches_case_id", table_name="material_import_batches")
    op.drop_index("ix_material_import_batches_user_id", table_name="material_import_batches")
    op.drop_table("material_import_batches")
