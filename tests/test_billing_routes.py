import asyncio
import importlib.util
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call, patch
from uuid import uuid4

from fastapi import HTTPException
from starlette.requests import Request

from app import billing_routes
from app.models import AttemptCreditPackagePurchase, DocumentCreditLedgerEntry


class BillingRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = SimpleNamespace(
            demo_mode_enabled=False,
            stripe_secret_key="sk_test_example",
            stripe_webhook_secret="whsec_example",
            stripe_price_id_attempt_credits_5="price_five",
            stripe_price_id_attempt_credits_10="price_ten",
            auth_public_base_url="https://example.test",
        )

    @staticmethod
    def webhook_request(body: bytes, signature: str = "t=1,v1=signature") -> Request:
        async def receive() -> dict[str, object]:
            return {"type": "http.request", "body": body, "more_body": False}

        return Request(
            {
                "type": "http",
                "method": "POST",
                "headers": [(b"stripe-signature", signature.encode())],
                "path": "/api/billing/webhook",
            },
            receive,
        )

    def test_one_time_price_formatter_rejects_recurring_or_inactive_prices(self) -> None:
        one_time = {
            "unit_amount": 500,
            "currency": "usd",
            "active": True,
            "recurring": None,
            "tax_behavior": "exclusive",
        }
        recurring = {**one_time, "recurring": {"interval": "month"}}
        inactive = {**one_time, "active": False}

        self.assertEqual(billing_routes._format_one_time_price(one_time), "$5.00")
        self.assertIsNone(billing_routes._format_one_time_price(recurring))
        self.assertIsNone(billing_routes._format_one_time_price(inactive))
        self.assertTrue(billing_routes._catalog_price_is_valid(one_time, 5))
        self.assertFalse(
            billing_routes._catalog_price_is_valid({**one_time, "unit_amount": 600}, 5)
        )
        self.assertFalse(
            billing_routes._catalog_price_is_valid({**one_time, "tax_behavior": None}, 5)
        )
        self.assertFalse(billing_routes._catalog_price_is_valid(one_time, 10))

    def test_packages_hide_unconfigured_or_invalid_price(self) -> None:
        with (
            patch.object(billing_routes, "get_settings", return_value=self.settings),
            patch.object(billing_routes, "_stripe_settings_ready", return_value=True),
            patch.object(
                billing_routes.stripe.Price,
                "retrieve",
                return_value={
                    "unit_amount": 500,
                    "currency": "usd",
                    "active": True,
                    "recurring": {"interval": "month"},
                    "tax_behavior": "exclusive",
                },
            ),
        ):
            result = billing_routes.list_attempt_credit_packages()

        self.assertEqual([item.credits for item in result.packages], [5, 10])
        self.assertTrue(all(not item.available and item.price is None for item in result.packages))

    def test_package_catalog_displays_exact_server_prices(self) -> None:
        with (
            patch.object(billing_routes, "get_settings", return_value=self.settings),
            patch.object(billing_routes, "_stripe_settings_ready", return_value=True),
            patch.object(
                billing_routes.stripe.Price,
                "retrieve",
                side_effect=[
                    {
                        "unit_amount": 500,
                        "currency": "usd",
                        "active": True,
                        "recurring": None,
                        "tax_behavior": "exclusive",
                    },
                    {
                        "unit_amount": 800,
                        "currency": "usd",
                        "active": True,
                        "recurring": None,
                        "tax_behavior": "exclusive",
                    },
                ],
            ),
        ):
            result = billing_routes.list_attempt_credit_packages()
        self.assertEqual(
            [(item.credits, item.price, item.available) for item in result.packages],
            [
                (5, "USD $5.00 before applicable tax", True),
                (10, "USD $8.00 before applicable tax", True),
            ],
        )

    def test_paid_package_requires_tax_enabled_session_and_single_quantity(self) -> None:
        session = {"id": "cs_paid", "metadata": {"package_size": "5"}}
        with (
            patch.object(
                billing_routes.stripe.checkout.Session,
                "list_line_items",
                return_value={"data": [{"quantity": 1, "price": {"id": "price_five"}}]},
            ),
            patch.object(
                billing_routes.stripe.Price,
                "retrieve",
                return_value={
                    "unit_amount": 500,
                    "currency": "usd",
                    "active": True,
                    "recurring": None,
                    "tax_behavior": "exclusive",
                },
            ),
        ):
            self.assertIsNone(billing_routes._paid_package_size(session, self.settings))
            self.assertEqual(
                billing_routes._paid_package_size(
                    {**session, "automatic_tax": {"enabled": True}}, self.settings
                ),
                5,
            )
        with patch.object(
            billing_routes.stripe.checkout.Session,
            "list_line_items",
            return_value={"data": [{"quantity": 2, "price": {"id": "price_five"}}]},
        ):
            self.assertIsNone(
                billing_routes._paid_package_size(
                    {**session, "automatic_tax": {"enabled": True}}, self.settings
                )
            )

    def test_purchase_migration_preserves_legacy_history_without_inventing_price(self) -> None:
        migration_path = (
            Path(__file__).parents[1]
            / "migrations"
            / "versions"
            / "0023_priced_credit_package_purchases.py"
        )
        spec = importlib.util.spec_from_file_location("migration_0023", migration_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        ledger_id, user_id, case_id = uuid4(), uuid4(), uuid4()
        connection = Mock()
        connection.execute.return_value.mappings.return_value = [
            {
                "id": ledger_id,
                "user_id": user_id,
                "case_id": case_id,
                "delta": 5,
                "created_at": datetime.now(UTC),
            }
        ]
        with patch.object(module, "op") as operations:
            operations.get_bind.return_value = connection
            module.upgrade()

        inserts = [
            call
            for call in connection.execute.call_args_list
            if "INSERT INTO attempt_credit_package_purchases" in str(call.args[0])
        ]
        self.assertEqual(len(inserts), 1)
        self.assertIsNone(inserts[0].args[1].get("price_amount"))
        self.assertEqual(inserts[0].args[1]["credits_used"], 5)
        self.assertIn("'legacy'", str(inserts[0].args[0]))
        self.assertIn("UPDATE document_credit_ledger_entries", str(connection.execute.call_args_list[-1].args[0]))

    def test_checkout_is_one_time_and_does_not_grant_from_redirect(self) -> None:
        actor = SimpleNamespace(id=uuid4(), email="buyer@example.test", stripe_customer_id="cus_1")
        case = SimpleNamespace(id=uuid4(), attempt_credit_balance=0, closed_at=None)
        db = Mock()
        db.scalar.side_effect = [case, None]
        with (
            patch.object(billing_routes, "get_settings", return_value=self.settings),
            patch.object(billing_routes, "_stripe_settings_ready", return_value=True),
            patch.object(billing_routes, "_authorized_case", return_value=case),
            patch.object(
                billing_routes.stripe.Price,
                "retrieve",
                return_value={
                    "unit_amount": 500,
                    "currency": "usd",
                    "active": True,
                    "recurring": None,
                    "tax_behavior": "exclusive",
                },
            ),
            patch.object(
                billing_routes.stripe.checkout.Session,
                "create",
                return_value={"id": "cs_pending", "url": "https://checkout.stripe.com/session"},
            ) as checkout,
        ):
            response = billing_routes.create_checkout_session(
                case.id, billing_routes.CheckoutCreate(package_size=5), actor, db
            )

        self.assertEqual(response["payment_status"], "pending_webhook_confirmation")
        self.assertNotIn("credits", response)
        self.assertEqual(case.attempt_credit_balance, 0)
        self.assertIsInstance(db.add.call_args.args[0], AttemptCreditPackagePurchase)
        self.assertEqual(db.add.call_args.args[0].status, "pending")
        self.assertEqual(checkout.call_args.kwargs["mode"], "payment")
        self.assertEqual(checkout.call_args.kwargs["line_items"], [{"price": "price_five", "quantity": 1}])
        self.assertEqual(checkout.call_args.kwargs["metadata"]["case_id"], str(case.id))
        self.assertEqual(checkout.call_args.kwargs["automatic_tax"], {"enabled": True})
        self.assertEqual(checkout.call_args.kwargs["payment_intent_data"]["receipt_email"], actor.email)
        self.assertEqual(checkout.call_args.kwargs["billing_address_collection"], "required")
        self.assertIn("within 30 days", checkout.call_args.kwargs["custom_text"]["submit"]["message"])

    def test_checkout_is_blocked_until_case_balance_is_zero(self) -> None:
        case = SimpleNamespace(id=uuid4(), attempt_credit_balance=1)
        db = Mock()
        db.scalar.return_value = case
        with (
            patch.object(billing_routes, "_authorized_case", return_value=case),
            patch.object(billing_routes.stripe.checkout.Session, "create") as checkout,
        ):
            with self.assertRaises(HTTPException) as raised:
                billing_routes.create_checkout_session(
                    case.id,
                    billing_routes.CheckoutCreate(package_size=10),
                    SimpleNamespace(id=uuid4()),
                    db,
                )
        self.assertEqual(raised.exception.status_code, 409)
        checkout.assert_not_called()
        db.add.assert_not_called()

    def test_pending_checkout_also_blocks_a_second_package(self) -> None:
        case = SimpleNamespace(id=uuid4(), attempt_credit_balance=0)
        db = Mock()
        db.scalar.side_effect = [case, uuid4()]
        with patch.object(billing_routes, "_authorized_case", return_value=case):
            with self.assertRaises(HTTPException) as raised:
                billing_routes.create_checkout_session(
                    case.id,
                    billing_routes.CheckoutCreate(package_size=5),
                    SimpleNamespace(id=uuid4()),
                    db,
                )
        self.assertEqual(raised.exception.status_code, 409)
        db.add.assert_not_called()

    def test_unconfigured_price_does_not_start_checkout(self) -> None:
        settings = SimpleNamespace(**self.settings.__dict__)
        settings.stripe_price_id_attempt_credits_5 = None
        with (
            patch.object(billing_routes, "get_settings", return_value=settings),
            patch.object(billing_routes, "_stripe_settings_ready", return_value=True),
            patch.object(
                billing_routes,
                "_authorized_case",
                return_value=SimpleNamespace(id=uuid4(), attempt_credit_balance=0),
            ),
            patch.object(billing_routes.stripe.checkout.Session, "create") as checkout,
        ):
            db = Mock()
            db.scalar.side_effect = [SimpleNamespace(id=uuid4(), attempt_credit_balance=0), None]
            with self.assertRaises(HTTPException) as raised:
                billing_routes.create_checkout_session(
                    uuid4(),
                    billing_routes.CheckoutCreate(package_size=5),
                    SimpleNamespace(id=uuid4(), stripe_customer_id="cus_1"),
                    db,
                )

        self.assertEqual(raised.exception.status_code, 503)
        checkout.assert_not_called()

    def test_only_paid_allow_listed_checkout_session_grants_case_credits(self) -> None:
        case_id, user_id = uuid4(), uuid4()
        user = SimpleNamespace(id=user_id, stripe_customer_id="cus_1")
        case = SimpleNamespace(id=case_id, attempt_credit_balance=2)
        purchase_id = uuid4()
        purchase = AttemptCreditPackagePurchase(
            id=purchase_id,
            user_id=user_id,
            case_id=case_id,
            package_size=5,
            price_amount=500,
            currency="usd",
            stripe_price_id="price_five",
            stripe_checkout_session_id="cs_paid",
            status="pending",
        )
        db = Mock()
        db.scalar.side_effect = [user, case, purchase, None]
        session = {
            "id": "cs_paid",
            "mode": "payment",
            "status": "complete",
            "payment_status": "paid",
            "customer": "cus_1",
            "payment_intent": "pi_paid",
            "currency": "usd",
            "amount_subtotal": 500,
            "amount_total": 540,
            "automatic_tax": {"enabled": True},
            "client_reference_id": str(user_id),
            "metadata": {
                "user_id": str(user_id),
                "case_id": str(case_id),
                "package_size": "5",
                "purchase_id": str(purchase_id),
            },
        }
        with (
            patch.object(billing_routes, "get_settings", return_value=self.settings),
            patch.object(
                billing_routes.stripe.checkout.Session,
                "list_line_items",
                return_value={"data": [{"quantity": 1, "price": {"id": "price_five"}}]},
            ),
            patch.object(
                billing_routes.stripe.Price,
                "retrieve",
                return_value={
                    "unit_amount": 500,
                    "currency": "usd",
                    "active": True,
                    "recurring": None,
                    "tax_behavior": "exclusive",
                },
            ),
        ):
            self.assertTrue(billing_routes._apply_checkout_completed(db, session))

        self.assertEqual(case.attempt_credit_balance, 7)
        entry = db.add.call_args.args[0]
        self.assertIsInstance(entry, DocumentCreditLedgerEntry)
        self.assertEqual(entry.delta, 5)
        self.assertEqual(entry.source_type, "package_purchase")
        self.assertEqual(entry.idempotency_key, "stripe-checkout:cs_paid")
        self.assertEqual(entry.package_purchase_id, purchase_id)
        self.assertEqual(purchase.status, "paid")
        self.assertEqual(purchase.stripe_payment_intent_id, "pi_paid")

    def test_browser_or_unpaid_session_never_grants_credits(self) -> None:
        db = Mock()
        for update in (
            {"payment_status": "unpaid"},
            {"mode": "subscription", "payment_status": "paid"},
        ):
            with patch.object(billing_routes, "get_settings", return_value=self.settings):
                result = billing_routes._apply_checkout_completed(
                    db,
                    {
                        "mode": "payment",
                        "status": "complete",
                        "payment_status": "paid",
                        **update,
                    },
                )
            self.assertTrue(result)
        db.scalar.assert_not_called()
        db.add.assert_not_called()

    def test_unknown_price_or_mismatched_metadata_grants_nothing(self) -> None:
        case_id, user_id = uuid4(), uuid4()
        for price_id, metadata_size in (("price_unknown", "5"), ("price_five", "10")):
            db = Mock()
            purchase_id = uuid4()
            purchase = AttemptCreditPackagePurchase(
                id=purchase_id,
                user_id=user_id,
                case_id=case_id,
                package_size=5,
                price_amount=500,
                currency="usd",
                stripe_price_id="price_five",
                stripe_checkout_session_id=f"cs_{metadata_size}",
                status="pending",
            )
            db.scalar.side_effect = [
                SimpleNamespace(id=user_id, stripe_customer_id="cus_1"),
                SimpleNamespace(id=case_id, attempt_credit_balance=0),
                purchase,
            ]
            session = {
                "id": f"cs_{metadata_size}",
                "mode": "payment",
                "status": "complete",
                "payment_status": "paid",
                "customer": "cus_1",
                "payment_intent": "pi_paid",
                "currency": "usd",
                "amount_subtotal": 500,
                "amount_total": 500,
                "automatic_tax": {"enabled": True},
                "client_reference_id": str(user_id),
                "metadata": {
                    "user_id": str(user_id),
                    "case_id": str(case_id),
                    "package_size": metadata_size,
                    "purchase_id": str(purchase_id),
                },
            }
            with (
                patch.object(billing_routes, "get_settings", return_value=self.settings),
                patch.object(
                    billing_routes.stripe.checkout.Session,
                    "list_line_items",
                    return_value={"data": [{"quantity": 1, "price": {"id": price_id}}]},
                ),
                patch.object(
                    billing_routes.stripe.Price,
                    "retrieve",
                    return_value={
                        "unit_amount": 500,
                        "currency": "usd",
                        "active": True,
                        "recurring": None,
                        "tax_behavior": "exclusive",
                    },
                ),
            ):
                self.assertFalse(billing_routes._apply_checkout_completed(db, session))
            db.add.assert_not_called()

    def test_duplicate_paid_session_is_idempotent(self) -> None:
        case_id, user_id, purchase_id = uuid4(), uuid4(), uuid4()
        case = SimpleNamespace(id=case_id, attempt_credit_balance=5)
        purchase = AttemptCreditPackagePurchase(
            id=purchase_id,
            user_id=user_id,
            case_id=case_id,
            package_size=5,
            price_amount=500,
            currency="usd",
            stripe_price_id="price_five",
            stripe_checkout_session_id="cs_paid",
            status="paid",
        )
        session = {
            "id": "cs_paid",
            "mode": "payment",
            "status": "complete",
            "payment_status": "paid",
            "customer": "cus_1",
            "payment_intent": "pi_paid",
            "currency": "usd",
            "amount_subtotal": 500,
            "amount_total": 500,
            "automatic_tax": {"enabled": True},
            "client_reference_id": str(user_id),
            "metadata": {
                "user_id": str(user_id),
                "case_id": str(case_id),
                "package_size": "5",
                "purchase_id": str(purchase_id),
            },
        }
        db = Mock()
        db.scalar.side_effect = [
            SimpleNamespace(id=user_id, stripe_customer_id="cus_1"),
            case,
            purchase,
        ]
        with (
            patch.object(billing_routes, "get_settings", return_value=self.settings),
            patch.object(
                billing_routes.stripe.checkout.Session,
                "list_line_items",
                return_value={"data": [{"quantity": 1, "price": {"id": "price_five"}}]},
            ),
            patch.object(
                billing_routes.stripe.Price,
                "retrieve",
                return_value={
                    "unit_amount": 500,
                    "currency": "usd",
                    "active": True,
                    "recurring": None,
                    "tax_behavior": "exclusive",
                },
            ),
        ):
            self.assertTrue(billing_routes._apply_checkout_completed(db, session))
        self.assertEqual(case.attempt_credit_balance, 5)
        db.add.assert_not_called()

    def test_delayed_payment_only_grants_after_async_success(self) -> None:
        purchase = AttemptCreditPackagePurchase(
            id=uuid4(),
            user_id=uuid4(),
            case_id=uuid4(),
            package_size=5,
            price_amount=500,
            currency="usd",
            stripe_price_id="price_five",
            stripe_checkout_session_id="cs_delayed",
            status="pending",
        )
        db = Mock()
        db.scalar.return_value = purchase
        pending = {
            "id": "cs_delayed",
            "mode": "payment",
            "status": "complete",
            "payment_status": "unpaid",
        }
        self.assertTrue(billing_routes._apply_checkout_completed(db, pending))
        db.scalar.assert_not_called()
        db.add.assert_not_called()

        self.assertEqual(
            billing_routes._process_event(
                db,
                {
                    "type": "checkout.session.async_payment_failed",
                    "data": {"object": {"id": "cs_delayed"}},
                },
            ),
            "processed",
        )
        self.assertEqual(purchase.status, "payment_failed")
        self.assertEqual(
            billing_routes._process_event(
                db,
                {
                    "type": "checkout.session.expired",
                    "data": {"object": {"id": "cs_delayed"}},
                },
            ),
            "processed",
        )
        self.assertEqual(purchase.status, "payment_failed")

    def test_delayed_payment_success_grants_once_after_unpaid_completion(self) -> None:
        user_id, case_id, purchase_id = uuid4(), uuid4(), uuid4()
        case = SimpleNamespace(id=case_id, attempt_credit_balance=0)
        purchase = AttemptCreditPackagePurchase(
            id=purchase_id,
            user_id=user_id,
            case_id=case_id,
            package_size=5,
            price_amount=500,
            currency="usd",
            stripe_price_id="price_five",
            stripe_checkout_session_id="cs_delayed",
            status="pending",
        )
        paid_session = {
            "id": "cs_delayed",
            "mode": "payment",
            "status": "complete",
            "payment_status": "paid",
            "customer": "cus_1",
            "payment_intent": "pi_delayed",
            "currency": "usd",
            "amount_subtotal": 500,
            "amount_total": 500,
            "automatic_tax": {"enabled": True},
            "client_reference_id": str(user_id),
            "metadata": {
                "user_id": str(user_id),
                "case_id": str(case_id),
                "package_size": "5",
                "purchase_id": str(purchase_id),
            },
        }
        db = Mock()
        db.scalar.side_effect = [
            SimpleNamespace(id=user_id, stripe_customer_id="cus_1"),
            case,
            purchase,
            None,
        ]
        with (
            patch.object(billing_routes, "get_settings", return_value=self.settings),
            patch.object(
                billing_routes.stripe.checkout.Session,
                "list_line_items",
                return_value={"data": [{"quantity": 1, "price": {"id": "price_five"}}]},
            ),
            patch.object(
                billing_routes.stripe.Price,
                "retrieve",
                return_value={
                    "unit_amount": 500,
                    "currency": "usd",
                    "active": True,
                    "recurring": None,
                    "tax_behavior": "exclusive",
                },
            ),
        ):
            self.assertEqual(
                billing_routes._process_event(
                    db,
                    {
                        "type": "checkout.session.completed",
                        "data": {
                            "object": {
                                "id": "cs_delayed",
                                "mode": "payment",
                                "status": "complete",
                                "payment_status": "unpaid",
                            }
                        },
                    },
                ),
                "processed",
            )
            self.assertEqual(
                billing_routes._process_event(
                    db,
                    {"type": "checkout.session.async_payment_succeeded", "data": {"object": paid_session}},
                ),
                "processed",
            )
        self.assertEqual(case.attempt_credit_balance, 5)
        self.assertEqual(purchase.status, "paid")

    def test_unused_package_refund_within_30_days_is_full_and_ledgered(self) -> None:
        now = datetime.now(UTC)
        user_id, case_id, purchase_id = uuid4(), uuid4(), uuid4()
        case = SimpleNamespace(id=case_id, attempt_credit_balance=5)
        purchase = AttemptCreditPackagePurchase(
            id=purchase_id,
            user_id=user_id,
            case_id=case_id,
            package_size=5,
            price_amount=500,
            currency="usd",
            stripe_price_id="price_five",
            stripe_payment_intent_id="pi_paid",
            amount_paid=500,
            credits_used=0,
            status="paid",
            paid_at=now - timedelta(days=4),
        )
        db = Mock()
        db.scalar.side_effect = [case, purchase]
        actor = SimpleNamespace(id=user_id)
        with (
            patch.object(billing_routes, "get_settings", return_value=self.settings),
            patch.object(billing_routes, "_stripe_settings_ready", return_value=True),
            patch.object(billing_routes, "_authorized_case", return_value=case),
            patch.object(
                billing_routes.stripe.Refund,
                "create",
                return_value={"id": "re_full", "status": "succeeded", "amount": 500},
            ) as refund_call,
        ):
            result = billing_routes.refund_package_purchase(case_id, purchase_id, actor, db)

        self.assertEqual(result, {"status": "refunded"})
        self.assertEqual(case.attempt_credit_balance, 0)
        self.assertEqual(purchase.status, "refunded")
        self.assertNotIn("amount", refund_call.call_args.kwargs)
        ledger = db.add.call_args.args[0]
        self.assertEqual(ledger.source_type, "package_refund")
        self.assertEqual(ledger.package_purchase_id, purchase_id)
        self.assertEqual(ledger.delta, -5)

    def test_delayed_full_refund_webhook_writes_immutable_ledger_entry(self) -> None:
        user_id, case_id, purchase_id = uuid4(), uuid4(), uuid4()
        case = SimpleNamespace(id=case_id, attempt_credit_balance=5)
        purchase = AttemptCreditPackagePurchase(
            id=purchase_id,
            user_id=user_id,
            case_id=case_id,
            package_size=5,
            price_amount=500,
            amount_paid=540,
            currency="usd",
            stripe_price_id="price_five",
            stripe_payment_intent_id="pi_paid",
            credits_used=0,
            status="refund_pending",
        )
        db = Mock()
        db.scalar.side_effect = [purchase, case]
        processed = billing_routes._apply_refund_event(
            db,
            {
                "id": "re_1",
                "status": "succeeded",
                "amount": 540,
                "payment_intent": "pi_paid",
                "metadata": {"purchase_id": str(purchase_id)},
            },
        )
        self.assertTrue(processed)
        self.assertEqual(purchase.status, "refunded")
        self.assertEqual(case.attempt_credit_balance, 0)
        self.assertEqual(db.add.call_args.args[0].delta, -5)

    def test_spent_partial_and_expired_package_refunds_are_denied(self) -> None:
        case_id, user_id = uuid4(), uuid4()
        for used, balance, purchased_at in (
            (1, 4, datetime.now(UTC)),
            (0, 4, datetime.now(UTC)),
            (0, 5, datetime.now(UTC) - timedelta(days=31)),
        ):
            with self.subTest(used=used, balance=balance, purchased_at=purchased_at):
                case = SimpleNamespace(id=case_id, attempt_credit_balance=balance)
                purchase = AttemptCreditPackagePurchase(
                    id=uuid4(),
                    user_id=user_id,
                    case_id=case_id,
                    package_size=5,
                    price_amount=500,
                    currency="usd",
                    stripe_price_id="price_five",
                    stripe_payment_intent_id="pi_paid",
                    credits_used=used,
                    status="paid",
                    paid_at=purchased_at,
                )
                db = Mock()
                db.scalar.side_effect = [case, purchase]
                with (
                    patch.object(billing_routes, "get_settings", return_value=self.settings),
                    patch.object(billing_routes, "_authorized_case", return_value=case),
                    patch.object(billing_routes.stripe.Refund, "create") as refund_call,
                ):
                    with self.assertRaises(HTTPException) as raised:
                        billing_routes.refund_package_purchase(
                            case_id, purchase.id, SimpleNamespace(id=user_id), db
                        )
                self.assertEqual(raised.exception.status_code, 409)
                refund_call.assert_not_called()

    def test_webhook_rejects_invalid_signatures(self) -> None:
        request = self.webhook_request(b'{"id":"evt_example"}')
        with (
            patch.object(billing_routes, "get_settings", return_value=self.settings),
            patch.object(billing_routes.stripe.Webhook, "construct_event", side_effect=ValueError),
        ):
            with self.assertRaises(HTTPException) as raised:
                asyncio.run(billing_routes.receive_stripe_webhook(request, Mock()))
        self.assertEqual(raised.exception.status_code, 400)

    def test_duplicate_verified_webhook_event_is_not_processed_twice(self) -> None:
        request = self.webhook_request(b'{"id":"evt_example","type":"unknown"}')
        event = {"id": "evt_example", "type": "unknown", "data": {"object": {}}}
        db = Mock()
        db.scalar.return_value = None
        with (
            patch.object(billing_routes, "get_settings", return_value=self.settings),
            patch.object(billing_routes.stripe.Webhook, "construct_event", return_value=event),
            patch.object(billing_routes, "_process_event") as process_event,
        ):
            result = asyncio.run(billing_routes.receive_stripe_webhook(request, db))

        self.assertEqual(result, {"received": True})
        process_event.assert_not_called()
        db.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
