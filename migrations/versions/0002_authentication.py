"""Authentication, identity, credential, and case-membership records."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_authentication"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=True)
    json_type = postgresql.JSONB(astext_type=sa.Text())
    timestamp = sa.DateTime(timezone=True)

    op.create_table(
        "users",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(512)),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("email_verified_at", timestamp),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now()),
        sa.Column("updated_at", timestamp, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('pending_verification', 'active', 'locked', 'disabled')",
            name="ck_users_status",
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "external_identities",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("provider_subject", sa.String(255), nullable=False),
        sa.Column("provider_email", sa.String(320)),
        sa.Column("email_verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now()),
        sa.CheckConstraint("provider IN ('google')", name="ck_external_identities_provider"),
        sa.UniqueConstraint(
            "provider", "provider_subject", name="uq_external_identity_provider_subject"
        ),
    )
    op.create_index("ix_external_identities_user_id", "external_identities", ["user_id"])

    op.create_table(
        "auth_sessions",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("family_id", uuid_type, nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now()),
        sa.Column("last_used_at", timestamp, server_default=sa.func.now()),
        sa.Column("idle_expires_at", timestamp, nullable=False),
        sa.Column("absolute_expires_at", timestamp, nullable=False),
        sa.Column("revoked_at", timestamp),
        sa.Column("revoke_reason", sa.String(80)),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_index("ix_auth_sessions_family_id", "auth_sessions", ["family_id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column(
            "session_id",
            uuid_type,
            sa.ForeignKey("auth_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("jti_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", timestamp, nullable=False),
        sa.Column("used_at", timestamp),
        sa.Column("revoked_at", timestamp),
    )
    op.create_index("ix_refresh_tokens_session_id", "refresh_tokens", ["session_id"])

    op.create_table(
        "auth_tokens",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purpose", sa.String(30), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("created_at", timestamp, server_default=sa.func.now()),
        sa.Column("expires_at", timestamp, nullable=False),
        sa.Column("used_at", timestamp),
        sa.Column("revoked_at", timestamp),
        sa.CheckConstraint(
            "purpose IN ('email_verification', 'password_reset')",
            name="ck_auth_tokens_purpose",
        ),
    )
    op.create_index("ix_auth_tokens_user_id", "auth_tokens", ["user_id"])

    op.create_table(
        "totp_credentials",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column(
            "user_id",
            uuid_type,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("encrypted_secret", sa.LargeBinary(), nullable=False),
        sa.Column("pending", sa.Boolean(), nullable=False),
        sa.Column("last_used_step", sa.Integer()),
        sa.Column("created_at", timestamp, server_default=sa.func.now()),
        sa.Column("confirmed_at", timestamp),
        sa.Column("revoked_at", timestamp),
    )
    op.create_table(
        "passkey_credentials",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("credential_id", sa.String(1024), nullable=False, unique=True),
        sa.Column("public_key", sa.LargeBinary(), nullable=False),
        sa.Column("sign_count", sa.Integer(), nullable=False),
        sa.Column("transports", json_type, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now()),
        sa.Column("last_used_at", timestamp),
        sa.Column("revoked_at", timestamp),
    )
    op.create_index("ix_passkey_credentials_user_id", "passkey_credentials", ["user_id"])

    op.create_table(
        "auth_challenges",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("purpose", sa.String(40), nullable=False),
        sa.Column("challenge", sa.Text(), nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now()),
        sa.Column("expires_at", timestamp, nullable=False),
        sa.Column("consumed_at", timestamp),
        sa.Column("context", json_type, nullable=False),
    )
    op.create_index("ix_auth_challenges_user_id", "auth_challenges", ["user_id"])

    op.create_table(
        "recovery_codes",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now()),
        sa.Column("used_at", timestamp),
    )
    op.create_index("ix_recovery_codes_user_id", "recovery_codes", ["user_id"])

    op.create_table(
        "auth_rate_limits",
        sa.Column("key_hash", sa.String(64), primary_key=True),
        sa.Column("window_started_at", timestamp, nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
    )

    op.create_table(
        "auth_audit_events",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("outcome", sa.String(30), nullable=False),
        sa.Column("context", json_type, nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now()),
    )
    op.create_index("ix_auth_audit_events_user_id", "auth_audit_events", ["user_id"])

    op.create_table(
        "case_memberships",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("case_id", uuid_type, sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("granted_at", timestamp, server_default=sa.func.now()),
        sa.Column("revoked_at", timestamp),
        sa.CheckConstraint("role IN ('owner', 'editor', 'viewer')", name="ck_case_memberships_role"),
        sa.UniqueConstraint("case_id", "user_id", name="uq_case_membership_user_case"),
    )
    op.create_index("ix_case_memberships_case_id", "case_memberships", ["case_id"])
    op.create_index("ix_case_memberships_user_id", "case_memberships", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_case_memberships_user_id", table_name="case_memberships")
    op.drop_index("ix_case_memberships_case_id", table_name="case_memberships")
    op.drop_table("case_memberships")
    op.drop_index("ix_auth_audit_events_user_id", table_name="auth_audit_events")
    op.drop_table("auth_audit_events")
    op.drop_table("auth_rate_limits")
    op.drop_index("ix_recovery_codes_user_id", table_name="recovery_codes")
    op.drop_table("recovery_codes")
    op.drop_index("ix_auth_challenges_user_id", table_name="auth_challenges")
    op.drop_table("auth_challenges")
    op.drop_index("ix_passkey_credentials_user_id", table_name="passkey_credentials")
    op.drop_table("passkey_credentials")
    op.drop_table("totp_credentials")
    op.drop_index("ix_auth_tokens_user_id", table_name="auth_tokens")
    op.drop_table("auth_tokens")
    op.drop_index("ix_refresh_tokens_session_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index("ix_auth_sessions_family_id", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_user_id", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_index("ix_external_identities_user_id", table_name="external_identities")
    op.drop_table("external_identities")
    op.drop_table("users")
