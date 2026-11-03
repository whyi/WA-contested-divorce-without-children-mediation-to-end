"""Support encrypted export-provider connections and minimal delivery audits."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0009_cr2a_property_exports"
down_revision = "0008_settlement_planning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=True)
    timestamp = sa.DateTime(timezone=True)

    op.create_table(
        "export_provider_connections",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("user_id", uuid_type, nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("provider_subject", sa.String(length=255), nullable=False),
        sa.Column("account_label", sa.String(length=320), nullable=False),
        sa.Column("encrypted_access_token", sa.LargeBinary(), nullable=False),
        sa.Column("encrypted_refresh_token", sa.LargeBinary()),
        sa.Column("token_expires_at", timestamp),
        sa.Column(
            "scopes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "provider IN ('google_drive', 'dropbox')",
            name="ck_export_provider_connections_provider",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "user_id",
            "provider",
            name="uq_export_provider_connection_user_provider",
        ),
    )
    op.create_index(
        "ix_export_provider_connections_user_id",
        "export_provider_connections",
        ["user_id"],
    )
    op.create_table(
        "export_delivery_events",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("case_id", uuid_type, nullable=False),
        sa.Column("selection_id", uuid_type, nullable=False),
        sa.Column("user_id", uuid_type),
        sa.Column("user_id_snapshot", uuid_type, nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("destination_digest", sa.String(length=64), nullable=False),
        sa.Column("request_sha256", sa.String(length=64), nullable=False),
        sa.Column("outcome", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("file_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("idempotency_key", uuid_type, nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "channel IN ('google_drive', 'dropbox', 'email')",
            name="ck_export_delivery_events_channel",
        ),
        sa.CheckConstraint(
            "outcome IN ('pending', 'success', 'partial', 'failed')",
            name="ck_export_delivery_events_outcome",
        ),
        sa.CheckConstraint("file_count BETWEEN 0 AND 2", name="ck_export_delivery_events_file_count"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["selection_id"],
            ["settlement_scenario_selections.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "user_id_snapshot",
            "idempotency_key",
            name="uq_export_delivery_event_idempotency",
        ),
    )
    op.create_index(
        "ix_export_delivery_events_case_id",
        "export_delivery_events",
        ["case_id"],
    )
    op.create_index(
        "ix_export_delivery_events_selection_id",
        "export_delivery_events",
        ["selection_id"],
    )


def downgrade() -> None:
    op.drop_table("export_delivery_events")
    op.drop_table("export_provider_connections")
