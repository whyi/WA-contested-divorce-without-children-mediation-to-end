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

    def test_monthly_price_formatter_rejects_non_monthly_or_inactive_prices(self) -> None:
        monthly = {
            "unit_amount": 1900,
            "currency": "usd",
            "recurring": {"interval": "month"},
            "active": True,
        }
        annual = {**monthly, "recurring": {"interval": "year"}}
        inactive = {**monthly, "active": False}
        zero_decimal = {**monthly, "unit_amount": 1900, "currency": "jpy"}
        three_decimal = {**monthly, "unit_amount": 1900, "currency": "kwd"}
        scaled_zero_decimal = {**monthly, "unit_amount": 1900, "currency": "isk"}

        self.assertEqual(billing_routes._format_monthly_price(monthly), "$19.00/month")
        self.assertIsNone(billing_routes._format_monthly_price(annual))
        self.assertIsNone(billing_routes._format_monthly_price(inactive))
        self.assertEqual(billing_routes._format_monthly_price(zero_decimal), "JPY 1,900/month")
        self.assertEqual(billing_routes._format_monthly_price(three_decimal), "KWD 1.900/month")
        self.assertEqual(billing_routes._format_monthly_price(scaled_zero_decimal), "ISK 19/month")

    def test_invoice_plan_rejects_unknown_and_mixed_prices(self) -> None:
        lines = lambda *prices: {
            "lines": {
                "data": [
                    {"pricing": {"price_details": {"price": price}}}
                    for price in prices
                ]
            }
        }
        with patch.object(
            billing_routes,
            "_stripe_price_plan",
            side_effect=lambda price: {"price_essential": "essential"}.get(price),
        ):
            self.assertEqual(
                billing_routes._invoice_plan_code(lines("price_essential")),
                "essential",
            )
            self.assertIsNone(billing_routes._invoice_plan_code(lines("price_unknown")))
            self.assertIsNone(
                billing_routes._invoice_plan_code(lines("price_essential", "price_unknown"))
            )

    def test_demo_mode_disables_stripe_billing(self) -> None:
        settings = SimpleNamespace(
            demo_mode_enabled=True,
            stripe_secret_key="sk_test_example",
            stripe_webhook_secret="whsec_example",
        )
        with patch.object(billing_routes, "get_settings", return_value=settings):
            self.assertFalse(billing_routes._stripe_settings_ready())

    def test_checkout_rejects_non_monthly_prices(self) -> None:
        settings = SimpleNamespace(
            stripe_secret_key="sk_test_example",
            stripe_webhook_secret="whsec_example",
            stripe_price_id_essential="price_essential",
            auth_public_base_url="https://example.test",
        )
        user = SimpleNamespace(
            subscription_status="free",
            stripe_subscription_id=None,
            stripe_customer_id="cus_example",
        )
        annual_price = {
            "unit_amount": 1900,
            "currency": "usd",
            "recurring": {"interval": "year"},
            "active": True,
        }
        with (
            patch.object(billing_routes, "get_settings", return_value=settings),
            patch.object(billing_routes, "_stripe_settings_ready", return_value=True),
            patch.object(billing_routes, "_stripe_price_plan", return_value="essential"),
            patch.object(billing_routes.stripe.Price, "retrieve", return_value=annual_price),
        ):
            with self.assertRaises(HTTPException) as raised:
                billing_routes.create_checkout_session(
                    billing_routes.CheckoutCreate(plan_code="essential"),
                    user,
                    Mock(),
                )

        self.assertEqual(raised.exception.status_code, 503)

    def test_paid_invoice_grants_only_up_to_credit_rollover_cap(self) -> None:
        user = SimpleNamespace(
            id=uuid4(),
            stripe_customer_id="cus_example",
            stripe_subscription_id="sub_example",
            subscription_status="active",
            document_credit_balance=1,
        )
        db = Mock()
        invoice = {
            "id": "in_example",
            "billing_reason": "subscription_cycle",
            "subscription": "sub_example",
            "amount_paid": 1900,
        }
        with (
            patch.object(billing_routes, "_customer_for_event", return_value=user),
            patch.object(billing_routes, "_invoice_plan_code", return_value="essential"),
        ):
            self.assertTrue(billing_routes._apply_invoice_paid(db, invoice))

        self.assertEqual(user.subscription_plan, "essential")
        self.assertEqual(user.subscription_status, "active")
        self.assertEqual(user.settlement_attempt_limit, 3)
        self.assertEqual(user.document_credit_balance, 3)
        entry = db.add.call_args.args[0]
        self.assertIsInstance(entry, DocumentCreditLedgerEntry)
        self.assertEqual(entry.idempotency_key, "stripe-invoice:in_example")
        self.assertEqual(entry.delta, 2)
        self.assertEqual(entry.balance_after, 3)

    def test_unpaid_trial_invoice_does_not_grant_monthly_credits(self) -> None:
        db = Mock()
        with patch.object(billing_routes, "_customer_for_event") as find_customer:
            self.assertTrue(
                billing_routes._apply_invoice_paid(
                    db,
                    {
                        "billing_reason": "subscription_create",
                        "amount_paid": 0,
                    },
                )
            )

        find_customer.assert_not_called()
        db.add.assert_not_called()

    def test_paid_invoice_for_superseded_subscription_is_ignored(self) -> None:
        user = SimpleNamespace(
            stripe_customer_id="cus_example",
            stripe_subscription_id="sub_current",
            subscription_status="active",
            document_credit_balance=0,
        )
        db = Mock()
        invoice = {
            "id": "in_old",
            "billing_reason": "subscription_cycle",
            "subscription": "sub_old",
            "amount_paid": 3900,
        }
        with patch.object(billing_routes, "_customer_for_event", return_value=user):
            self.assertTrue(billing_routes._apply_invoice_paid(db, invoice))

        self.assertEqual(user.document_credit_balance, 0)
        db.add.assert_not_called()

    def test_webhook_is_disabled_in_demo_mode(self) -> None:
        request = Request(
            {"type": "http", "method": "POST", "headers": [], "path": "/api/billing/webhook"},
            lambda: None,
        )
        settings = SimpleNamespace(demo_mode_enabled=True, stripe_webhook_secret="whsec_example")
        with patch.object(billing_routes, "get_settings", return_value=settings):
            with self.assertRaises(HTTPException) as raised:
                asyncio.run(billing_routes.receive_stripe_webhook(request, Mock()))

        self.assertEqual(raised.exception.status_code, 503)

    def test_webhook_rejects_invalid_signatures(self) -> None:
        request = self.webhook_request(b'{"id":"evt_example"}')
        settings = SimpleNamespace(demo_mode_enabled=False, stripe_webhook_secret="whsec_example")
        with (
            patch.object(billing_routes, "get_settings", return_value=settings),
            patch.object(billing_routes.stripe.Webhook, "construct_event", side_effect=ValueError),
        ):
            with self.assertRaises(HTTPException) as raised:
                asyncio.run(billing_routes.receive_stripe_webhook(request, Mock()))

        self.assertEqual(raised.exception.status_code, 400)

    def test_webhook_body_size_is_bounded_before_signature_parsing(self) -> None:
        request = self.webhook_request(b"too large")
        settings = SimpleNamespace(demo_mode_enabled=False, stripe_webhook_secret="whsec_example")
        with (
            patch.object(billing_routes, "get_settings", return_value=settings),
            patch.object(billing_routes, "MAX_WEBHOOK_BYTES", 1),
            patch.object(billing_routes.stripe.Webhook, "construct_event") as construct_event,
        ):
            with self.assertRaises(HTTPException) as raised:
                asyncio.run(billing_routes.receive_stripe_webhook(request, Mock()))

        self.assertEqual(raised.exception.status_code, 413)
        construct_event.assert_not_called()

    def test_webhook_duplicate_event_is_not_processed_twice(self) -> None:
        request = self.webhook_request(b'{"id":"evt_example","type":"unhandled"}')
        settings = SimpleNamespace(demo_mode_enabled=False, stripe_webhook_secret="whsec_example")
        event = {"id": "evt_example", "type": "unhandled", "data": {"object": {}}}
        db = Mock()
        db.scalar.return_value = None
        with (
            patch.object(billing_routes, "get_settings", return_value=settings),
            patch.object(billing_routes.stripe.Webhook, "construct_event", return_value=event),
            patch.object(billing_routes, "_process_event") as process_event,
        ):
            result = asyncio.run(billing_routes.receive_stripe_webhook(request, db))

        self.assertEqual(result, {"received": True})
        process_event.assert_not_called()
        db.rollback.assert_called_once()

    def test_webhook_commits_entitlements_with_the_event_receipt(self) -> None:
        request = self.webhook_request(b'{"id":"evt_example","type":"unhandled"}')
        settings = SimpleNamespace(demo_mode_enabled=False, stripe_webhook_secret="whsec_example")
        event = {"id": "evt_example", "type": "unhandled", "data": {"object": {}}}
        record = SimpleNamespace(status="processing", processed_at=None)
        db = Mock()
        db.scalar.return_value = "evt_example"
        db.get.return_value = record
        with (
            patch.object(billing_routes, "get_settings", return_value=settings),
            patch.object(billing_routes.stripe.Webhook, "construct_event", return_value=event),
            patch.object(billing_routes, "_process_event", return_value="processed"),
        ):
            result = asyncio.run(billing_routes.receive_stripe_webhook(request, db))

        self.assertEqual(result, {"received": True})
        self.assertEqual(record.status, "processed")
        self.assertIsNotNone(record.processed_at)
        db.commit.assert_called_once()

    def test_subscription_updates_apply_tier_and_ignore_older_events(self) -> None:
        now = 1_800_000_000
        user = SimpleNamespace(
            stripe_customer_id="cus_example",
            stripe_subscription_id=None,
            subscription_plan="free",
            subscription_status="free",
            settlement_attempt_limit=1,
            subscription_period_end=None,
            subscription_cancel_at_period_end=False,
            billing_state_event_created_at=None,
        )
        db = Mock()
        db.scalar.return_value = user
        event = {
            "id": "evt_new",
            "type": "customer.subscription.updated",
            "created": now,
            "data": {
                "object": {
                    "id": "sub_example",
                    "customer": "cus_example",
                    "status": "active",
                    "current_period_end": now + 30 * 24 * 60 * 60,
                    "cancel_at_period_end": True,
                    "items": {"data": [{"price": {"id": "price_plus"}}]},
                }
            },
        }
        with patch.object(
            billing_routes,
            "_stripe_price_plan",
            side_effect=lambda price: {"price_plus": "plus"}.get(price),
        ):
            self.assertTrue(
                billing_routes._apply_subscription_event(
                    db,
                    event,
                    billing_routes._period_end(now),
                )
            )
            stale = {
                **event,
                "data": {
                    "object": {
                        **event["data"]["object"],
                        "status": "past_due",
                    }
                },
            }
            self.assertTrue(
                billing_routes._apply_subscription_event(
                    db,
                    stale,
                    billing_routes._period_end(now - 1),
                )
            )

        self.assertEqual(user.subscription_plan, "plus")
        self.assertEqual(user.subscription_status, "active")
        self.assertEqual(user.settlement_attempt_limit, 5)
        self.assertTrue(user.subscription_cancel_at_period_end)


if __name__ == "__main__":
    unittest.main()
