import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import HTTPException
from starlette.requests import Request

from app import billing_routes
from app.models import DocumentCreditLedgerEntry


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
        one_time = {"unit_amount": 2000, "currency": "usd", "active": True, "recurring": None}
        recurring = {**one_time, "recurring": {"interval": "month"}}
        inactive = {**one_time, "active": False}

        self.assertEqual(billing_routes._format_one_time_price(one_time), "$20.00")
        self.assertIsNone(billing_routes._format_one_time_price(recurring))
        self.assertIsNone(billing_routes._format_one_time_price(inactive))

    def test_packages_hide_unconfigured_or_invalid_price(self) -> None:
        with (
            patch.object(billing_routes, "get_settings", return_value=self.settings),
            patch.object(billing_routes, "_stripe_settings_ready", return_value=True),
            patch.object(
                billing_routes.stripe.Price,
                "retrieve",
                return_value={
                    "unit_amount": 2000,
                    "currency": "usd",
                    "active": True,
                    "recurring": {"interval": "month"},
                },
            ),
        ):
            result = billing_routes.list_attempt_credit_packages()

        self.assertEqual([item.credits for item in result.packages], [5, 10])
        self.assertTrue(all(not item.available and item.price is None for item in result.packages))

    def test_checkout_is_one_time_and_does_not_grant_from_redirect(self) -> None:
        actor = SimpleNamespace(id=uuid4(), email="buyer@example.test", stripe_customer_id="cus_1")
        case = SimpleNamespace(id=uuid4(), attempt_credit_balance=0, closed_at=None)
        db = Mock()
        with (
            patch.object(billing_routes, "get_settings", return_value=self.settings),
            patch.object(billing_routes, "_stripe_settings_ready", return_value=True),
            patch.object(billing_routes, "_authorized_case", return_value=case),
            patch.object(
                billing_routes.stripe.Price,
                "retrieve",
                return_value={
                    "unit_amount": 2000,
                    "currency": "usd",
                    "active": True,
                    "recurring": None,
                },
            ),
            patch.object(
                billing_routes.stripe.checkout.Session,
                "create",
                return_value={"url": "https://checkout.stripe.com/session"},
            ) as checkout,
        ):
            response = billing_routes.create_checkout_session(
                case.id, billing_routes.CheckoutCreate(package_size=5), actor, db
            )

        self.assertEqual(response["payment_status"], "pending_webhook_confirmation")
        self.assertNotIn("credits", response)
        self.assertEqual(case.attempt_credit_balance, 0)
        db.add.assert_not_called()
        self.assertEqual(checkout.call_args.kwargs["mode"], "payment")
        self.assertEqual(checkout.call_args.kwargs["line_items"], [{"price": "price_five", "quantity": 1}])
        self.assertEqual(checkout.call_args.kwargs["metadata"]["case_id"], str(case.id))

    def test_unconfigured_price_does_not_start_checkout(self) -> None:
        settings = SimpleNamespace(**self.settings.__dict__)
        settings.stripe_price_id_attempt_credits_5 = None
        with (
            patch.object(billing_routes, "get_settings", return_value=settings),
            patch.object(billing_routes, "_stripe_settings_ready", return_value=True),
            patch.object(billing_routes, "_authorized_case", return_value=SimpleNamespace(id=uuid4())),
            patch.object(billing_routes.stripe.checkout.Session, "create") as checkout,
        ):
            with self.assertRaises(HTTPException) as raised:
                billing_routes.create_checkout_session(
                    uuid4(),
                    billing_routes.CheckoutCreate(package_size=5),
                    SimpleNamespace(id=uuid4(), stripe_customer_id="cus_1"),
                    Mock(),
                )

        self.assertEqual(raised.exception.status_code, 503)
        checkout.assert_not_called()

    def test_only_paid_allow_listed_checkout_session_grants_case_credits(self) -> None:
        case_id, user_id = uuid4(), uuid4()
        user = SimpleNamespace(id=user_id, stripe_customer_id="cus_1")
        case = SimpleNamespace(id=case_id, attempt_credit_balance=2)
        db = Mock()
        db.scalar.side_effect = [user, case, uuid4(), None]
        session = {
            "id": "cs_paid",
            "mode": "payment",
            "status": "complete",
            "payment_status": "paid",
            "customer": "cus_1",
            "client_reference_id": str(user_id),
            "metadata": {
                "user_id": str(user_id),
                "case_id": str(case_id),
                "package_size": "5",
            },
        }
        with (
            patch.object(billing_routes, "get_settings", return_value=self.settings),
            patch.object(
                billing_routes.stripe.checkout.Session,
                "list_line_items",
                return_value={"data": [{"quantity": 1, "price": {"id": "price_five"}}]},
            ),
        ):
            self.assertTrue(billing_routes._apply_checkout_completed(db, session))

        self.assertEqual(case.attempt_credit_balance, 7)
        entry = db.add.call_args.args[0]
        self.assertIsInstance(entry, DocumentCreditLedgerEntry)
        self.assertEqual(entry.delta, 5)
        self.assertEqual(entry.source_type, "package_purchase")
        self.assertEqual(entry.idempotency_key, "stripe-checkout:cs_paid")

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
            db.scalar.side_effect = [
                SimpleNamespace(id=user_id, stripe_customer_id="cus_1"),
                SimpleNamespace(id=case_id, attempt_credit_balance=0),
                uuid4(),
            ]
            session = {
                "id": f"cs_{metadata_size}",
                "mode": "payment",
                "status": "complete",
                "payment_status": "paid",
                "customer": "cus_1",
                "client_reference_id": str(user_id),
                "metadata": {
                    "user_id": str(user_id),
                    "case_id": str(case_id),
                    "package_size": metadata_size,
                },
            }
            with (
                patch.object(billing_routes, "get_settings", return_value=self.settings),
                patch.object(
                    billing_routes.stripe.checkout.Session,
                    "list_line_items",
                    return_value={"data": [{"quantity": 1, "price": {"id": price_id}}]},
                ),
            ):
                self.assertTrue(billing_routes._apply_checkout_completed(db, session))
            db.add.assert_not_called()

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
