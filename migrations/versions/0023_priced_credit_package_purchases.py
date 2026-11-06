"""Track configured package purchases, usage, and refunds."""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "0023_priced_credit_package_purchases"
down_revision = "0022_deletion_tombstones"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "attempt_credit_package_purchases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("package_size", sa.Integer(), nullable=False),
        sa.Column("price_amount", sa.Integer(), nullable=True),
        sa.Column("amount_paid", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("stripe_price_id", sa.String(length=255), nullable=False),
        sa.Column("stripe_checkout_session_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_payment_intent_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_refund_id", sa.String(length=255), nullable=True),
        sa.Column("credits_used", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "price_amount IS NULL OR "
            "(package_size = 5 AND price_amount = 500) OR "
            "(package_size = 10 AND price_amount = 800)",
            name="ck_attempt_credit_package_catalog",
        ),
        sa.CheckConstraint(
            "credits_used >= 0 AND credits_used <= package_size",
            name="ck_attempt_credit_package_used",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'paid', 'legacy', 'payment_failed', 'expired', 'refund_pending', 'refunded')",
            name="ck_attempt_credit_package_status",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_checkout_session_id", name="uq_attempt_credit_checkout_session"),
        sa.UniqueConstraint("stripe_payment_intent_id", name="uq_attempt_credit_payment_intent"),
        sa.UniqueConstraint("stripe_refund_id", name="uq_attempt_credit_refund"),
    )
    op.create_index(
        "ix_attempt_credit_purchase_case_status",
        "attempt_credit_package_purchases",
        ["case_id", "status"],
    )
    connection = op.get_bind()
    legacy_purchases = connection.execute(
        sa.text(
            """
            SELECT id, user_id, case_id, delta, created_at
            FROM document_credit_ledger_entries
            WHERE source_type = 'package_purchase'
              AND delta IN (5, 10)
              AND case_id IS NOT NULL
            """
        )
    ).mappings()
    for ledger in legacy_purchases:
        purchase_id = uuid4()
        connection.execute(
            sa.text(
                """
                INSERT INTO attempt_credit_package_purchases
                    (id, user_id, case_id, package_size, price_amount, amount_paid,
                     currency, stripe_price_id, credits_used, status, created_at, paid_at)
                VALUES
                    (:id, :user_id, :case_id, :package_size, NULL, NULL,
                     'usd', 'legacy-unverified', :credits_used, 'legacy', :created_at, :paid_at)
                """
            ),
            {
                "id": purchase_id,
                "user_id": ledger["user_id"],
                "case_id": ledger["case_id"],
                "package_size": ledger["delta"],
                "credits_used": ledger["delta"],
                "created_at": ledger["created_at"],
                "paid_at": ledger["created_at"],
            },
        )
        connection.execute(
            sa.text(
                "UPDATE document_credit_ledger_entries SET package_purchase_id = :purchase_id WHERE id = :ledger_id"
            ),
            {"purchase_id": purchase_id, "ledger_id": ledger["id"]},
        )
    op.add_column(
        "document_credit_ledger_entries",
        sa.Column("package_purchase_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_document_credit_ledger_package_purchase",
        "document_credit_ledger_entries",
        "attempt_credit_package_purchases",
        ["package_purchase_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_document_credit_ledger_package_purchase_id",
        "document_credit_ledger_entries",
        ["package_purchase_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_credit_ledger_package_purchase_id",
        table_name="document_credit_ledger_entries",
    )
    op.drop_constraint(
        "fk_document_credit_ledger_package_purchase",
        "document_credit_ledger_entries",
        type_="foreignkey",
    )
    op.drop_column("document_credit_ledger_entries", "package_purchase_id")
    op.drop_index(
        "ix_attempt_credit_purchase_case_status",
        table_name="attempt_credit_package_purchases",
    )
    op.drop_table("attempt_credit_package_purchases")
