import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import HTTPException

from app import attempt_credits, billing_routes
from app.models import Case, DocumentCreditLedgerEntry


class AttemptCreditPolicyTests(unittest.TestCase):
    def test_first_successful_case_finalization_is_free(self) -> None:
        case = SimpleNamespace(id=uuid4(), first_finalization_used=False, attempt_credit_balance=0)
        actor = SimpleNamespace(id=uuid4())
        attempt = SimpleNamespace(id=uuid4())
        db = Mock()

        charge = attempt_credits.consume_finalization_credit(db, case, actor, attempt)

        self.assertEqual(charge["policy"], "free_first_case_finalization")
        self.assertEqual(charge["credit_cost"], 0)
        self.assertTrue(case.first_finalization_used)
        self.assertEqual(case.attempt_credit_balance, 0)
        db.add.assert_not_called()

    def test_later_successful_finalization_debits_exactly_one_case_credit(self) -> None:
        case = SimpleNamespace(id=uuid4(), first_finalization_used=True, attempt_credit_balance=3)
        actor = SimpleNamespace(id=uuid4())
        attempt = SimpleNamespace(id=uuid4())
        db = Mock()

        charge = attempt_credits.consume_finalization_credit(db, case, actor, attempt)

        self.assertEqual(charge["policy"], "attempt_credit")
        self.assertEqual(charge["credit_cost"], 1)
        self.assertEqual(case.attempt_credit_balance, 2)
        entry = db.add.call_args.args[0]
        self.assertIsInstance(entry, DocumentCreditLedgerEntry)
        self.assertEqual(entry.case_id, case.id)
        self.assertEqual(entry.user_id, actor.id)
        self.assertEqual(entry.idempotency_key, f"finalization:{attempt.id}")
        self.assertEqual(entry.delta, -1)
        self.assertEqual(entry.balance_after, 2)

    def test_insufficient_credit_preserves_first_attempt_and_balance(self) -> None:
        case = SimpleNamespace(id=uuid4(), first_finalization_used=True, attempt_credit_balance=0)
        actor = SimpleNamespace(id=uuid4())
        attempt = SimpleNamespace(id=uuid4())
        db = Mock()

        with self.assertRaises(HTTPException) as raised:
            attempt_credits.consume_finalization_credit(db, case, actor, attempt)

        self.assertEqual(raised.exception.status_code, 402)
        self.assertEqual(case.attempt_credit_balance, 0)
        self.assertTrue(case.first_finalization_used)
        db.add.assert_not_called()

    def test_package_skus_are_allow_listed_and_prices_are_configuration_only(self) -> None:
        settings = SimpleNamespace(
            stripe_price_id_attempt_credits_5="price_five",
            stripe_price_id_attempt_credits_10="price_ten",
        )

        self.assertEqual(attempt_credits.package_size_for_price(settings, "price_five"), 5)
        self.assertEqual(attempt_credits.package_size_for_price(settings, "price_ten"), 10)
        self.assertIsNone(attempt_credits.package_size_for_price(settings, "price_unknown"))
        self.assertIsNone(
            attempt_credits.package_size_for_price(
                SimpleNamespace(
                    stripe_price_id_attempt_credits_5="same",
                    stripe_price_id_attempt_credits_10="same",
                ),
                "same",
            )
        )

    def test_verified_package_grant_is_case_scoped_and_checkout_idempotent(self) -> None:
        case = SimpleNamespace(id=uuid4(), attempt_credit_balance=1)
        actor = SimpleNamespace(id=uuid4())
        db = Mock()
        db.scalar.return_value = None

        attempt_credits.grant_package_credits(
            db, case, actor, package_size=5, checkout_session_id="cs_paid"
        )

        self.assertEqual(case.attempt_credit_balance, 6)
        entry = db.add.call_args.args[0]
        self.assertEqual(entry.case_id, case.id)
        self.assertEqual(entry.source_type, "package_purchase")
        self.assertEqual(entry.idempotency_key, "stripe-checkout:cs_paid")
        self.assertEqual(entry.delta, 5)

        existing = SimpleNamespace(idempotency_key="stripe-checkout:cs_paid")
        db.scalar.return_value = existing
        db.add.reset_mock()
        attempt_credits.grant_package_credits(
            db, case, actor, package_size=5, checkout_session_id="cs_paid"
        )
        self.assertEqual(case.attempt_credit_balance, 6)
        db.add.assert_not_called()

    def test_package_checkout_is_one_time_and_does_not_grant_in_browser(self) -> None:
        settings = SimpleNamespace(
            demo_mode_enabled=False,
            stripe_secret_key="sk_test_example",
            stripe_webhook_secret="whsec_example",
            stripe_price_id_attempt_credits_5="price_five",
            auth_public_base_url="https://example.test",
        )
        actor = SimpleNamespace(id=uuid4(), stripe_customer_id="cus_example")
        case = SimpleNamespace(id=uuid4(), closed_at=None)
        with (
            patch.object(billing_routes, "get_settings", return_value=settings),
            patch.object(billing_routes, "_stripe_settings_ready", return_value=True),
            patch.object(billing_routes, "_authorized_case", return_value=case),
            patch.object(
                billing_routes.stripe.Price,
                "retrieve",
                return_value={"unit_amount": 2000, "currency": "usd", "active": True},
            ),
            patch.object(
                billing_routes.stripe.checkout.Session,
                "create",
                return_value={"url": "https://checkout.stripe.com/session"},
            ) as checkout,
        ):
            result = billing_routes.create_checkout_session(
                case.id,
                billing_routes.CheckoutCreate(package_size=5),
                actor,
                Mock(),
            )

        self.assertEqual(result["payment_status"], "pending_webhook_confirmation")
        self.assertEqual(result["checkout_url"], "https://checkout.stripe.com/session")
        self.assertEqual(checkout.call_args.kwargs["mode"], "payment")
        self.assertEqual(checkout.call_args.kwargs["line_items"], [{"price": "price_five", "quantity": 1}])
        self.assertNotIn("credits", result)

    def test_legacy_price_entitlements_and_case_data_are_reset_additively(self) -> None:
        migration_path = (
            Path(__file__).parents[1]
            / "migrations"
            / "versions"
            / "0020_attempt_credit_packages.py"
        )
        spec = importlib.util.spec_from_file_location("migration_0020", migration_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.down_revision, "0019_attempt_finalization")

        with patch.object(module, "op") as op:
            module.upgrade()

        added_case_columns = [
            call.args[1] for call in op.add_column.call_args_list if call.args[0] == "cases"
        ]
        self.assertEqual(
            {column.name for column in added_case_columns},
            {"attempt_credit_balance", "first_finalization_used"},
        )
        sql = "\n".join(str(call.args[0]) for call in op.execute.call_args_list)
        self.assertIn("document_credit_balance = 0", sql)
        self.assertIn("finalized_at IS NOT NULL", sql)
        self.assertNotIn("DELETE FROM", sql.upper())
        self.assertFalse(hasattr(Case, "subscription_plan"))


if __name__ == "__main__":
    unittest.main()
