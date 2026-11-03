"""Persist settlement-planning consent, ledger events, scenario runs, and selections."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0008_settlement_planning"
down_revision = "0007_property_tracing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=True)
    timestamp = sa.DateTime(timezone=True)
    json_type = postgresql.JSONB(astext_type=sa.Text())

    op.add_column(
        "cases",
        sa.Column("settlement_revision", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_table(
        "settlement_planning_consent_events",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("case_id", uuid_type, nullable=False),
        sa.Column("user_id", uuid_type),
        sa.Column("user_id_snapshot", uuid_type, nullable=False),
        sa.Column("notice_version", sa.String(length=100), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_settlement_planning_consent_events_case_id",
        "settlement_planning_consent_events",
        ["case_id"],
    )
    op.add_column(
        "settlement_planning_consent_events",
        sa.Column("provider", sa.String(length=100)),
    )
    op.add_column(
        "settlement_planning_consent_events",
        sa.Column("model_id", sa.String(length=255)),
    )
    op.add_column(
        "settlement_planning_consent_events",
        sa.Column("region", sa.String(length=100)),
    )
    op.add_column(
        "settlement_planning_consent_events",
        sa.Column("purpose", sa.Text()),
    )
    op.add_column(
        "settlement_planning_consent_events",
        sa.Column("data_sent", sa.Text()),
    )
    op.add_column(
        "settlement_planning_consent_events",
        sa.Column("data_handling_notice", sa.Text()),
    )
    op.create_table(
        "settlement_ledger_events",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("case_id", uuid_type, nullable=False),
        sa.Column("asset_id", uuid_type, nullable=False),
        sa.Column("asset_name", sa.String(length=200), nullable=False),
        sa.Column("asset_kind", sa.String(length=8), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("event_json", json_type, nullable=False),
        sa.Column("user_id", uuid_type),
        sa.Column("user_id_snapshot", uuid_type, nullable=False),
        sa.Column("idempotency_key", uuid_type, nullable=False),
        sa.Column("request_sha256", sa.String(length=64), nullable=False),
        sa.Column("profile_revision", sa.Integer(), nullable=False),
        sa.Column("settlement_revision", sa.Integer(), nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("sequence_number >= 0", name="ck_settlement_ledger_sequence"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "case_id",
            "asset_id",
            "effective_date",
            "sequence_number",
            name="uq_settlement_ledger_asset_event_order",
        ),
        sa.UniqueConstraint(
            "case_id",
            "user_id_snapshot",
            "idempotency_key",
            name="uq_settlement_ledger_event_idempotency",
        ),
    )
    op.create_index("ix_settlement_ledger_events_case_id", "settlement_ledger_events", ["case_id"])
    op.create_table(
        "settlement_scenario_runs",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("case_id", uuid_type, nullable=False),
        sa.Column("user_id", uuid_type),
        sa.Column("user_id_snapshot", uuid_type, nullable=False),
        sa.Column("profile_revision", sa.Integer(), nullable=False),
        sa.Column("settlement_revision", sa.Integer(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("axes_json", json_type, nullable=False),
        sa.Column("scenario_results_json", json_type, nullable=False),
        sa.Column("ranking_json", json_type),
        sa.Column("ranking_error", sa.Text()),
        sa.Column("input_fact_ids", json_type, nullable=False),
        sa.Column("provider", sa.String(length=100)),
        sa.Column("model_id", sa.String(length=255)),
        sa.Column("region", sa.String(length=100)),
        sa.Column("notice_version", sa.String(length=100)),
        sa.Column("data_handling_notice", sa.Text()),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_settlement_scenario_runs_case_id", "settlement_scenario_runs", ["case_id"])
    op.create_table(
        "settlement_scenario_selections",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("case_id", uuid_type, nullable=False),
        sa.Column("user_id", uuid_type),
        sa.Column("user_id_snapshot", uuid_type, nullable=False),
        sa.Column("idempotency_key", uuid_type, nullable=False),
        sa.Column("request_sha256", sa.String(length=64), nullable=False),
        sa.Column("run_id", uuid_type, nullable=False),
        sa.Column("scenario_id", sa.String(length=80), nullable=False),
        sa.Column("scenario_result_json", json_type, nullable=False),
        sa.Column("profile_revision", sa.Integer(), nullable=False),
        sa.Column("settlement_revision", sa.Integer(), nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["settlement_scenario_runs.id"],
            name="fk_settlement_scenario_selections_run_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "case_id",
            "user_id_snapshot",
            "idempotency_key",
            name="uq_settlement_scenario_selection_idempotency",
        ),
    )
    op.create_index(
        "ix_settlement_scenario_selections_case_id",
        "settlement_scenario_selections",
        ["case_id"],
    )
    op.create_index(
        "ix_settlement_scenario_selections_run_id",
        "settlement_scenario_selections",
        ["run_id"],
    )


def downgrade() -> None:
    op.drop_table("settlement_scenario_selections")
    op.drop_table("settlement_scenario_runs")
    op.drop_table("settlement_ledger_events")
    op.drop_table("settlement_planning_consent_events")
    op.drop_column("cases", "settlement_revision")
